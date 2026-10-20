"""Opt-in DeepSeek evidence decisions over frozen HTTP pages; no live-web claim."""

import asyncio
import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from support.research_discovery_samples import discovery_scope, planning_batch
from test_research_agent_integration import proposal, response_message, turn_context
from test_research_data_integration import record_call
from test_research_evidence_integration import evidence_graph
from test_research_planning_live import EvaluationLimits

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.environ.get("DEER_FLOW_RUN_LIVE_TESTS") != "1", reason="Explicit real DeepSeek opt-in required")]


class EvidenceEvaluationLimits(EvaluationLimits):
    def admit(self, kind):
        # Round one hit ten model calls while reading three captures and correcting
        # invalid units. Retain the 180-second deadline; allow this longer workflow.
        if time.monotonic() - self.started > 180:
            raise RuntimeError("Evaluation wall-clock limit reached")
        field, cap = ("model_calls", 20) if kind == "model" else ("tool_calls", 24)
        setattr(self, field, getattr(self, field) + 1)
        if getattr(self, field) > cap:
            raise RuntimeError("Evaluation call limit reached")


def frozen_catalog(case):
    if case == "laptop-mismatch":
        return {
            "specs": ("official", "行远 L1 16GB/512GB，全新笔记本，重量1.35kg，Linux驱动可用。"),
            "sale": ("retailer", "合成商城，合成自营，中国大陆，CNY。行远 L1 8GB/256GB，全新，公开售价3999元。页面没有16GB/512GB报价。"),
            "review": ("review", "独立评测：行远 L1 32GB/1TB，在指定Docker容器负载下编译耗时85秒。这个结论不适用于16GB/512GB版本。"),
        }
    if case == "conditional-unavailable":
        return {
            "specs": ("official", "极光 A1 8GB/256GB，全新，支持光学防抖，电池5000mAh。"),
            "sale": ("retailer", "合成商城，中国大陆，CNY，合成自营。极光 A1 8GB/256GB，全新，会员价2999元，需要会员并领取指定地区补贴，资格和叠加规则未说明。未展示普通公开报价。"),
            "jd": ("retailer", None),
        }
    return {
        "launch": ("official", "2023年发布稿：极光 A1 8GB/256GB 首发价3999 CNY。此历史文章不提供当前销售报价。支持光学防抖，电池5000mAh。"),
        "sale": ("retailer", "合成商城，合成自营，中国大陆，CNY。极光 A1 8GB/256GB，全新，公开售价3299元，无会员、补贴、优惠券要求。本合成页面显示此次有效公开报价；库存与结算另核对。"),
        "review": ("review", "独立评测：极光 A1 8GB/256GB，在日间测试中防抖表现稳定。这是单次样本观点，不是总体用户满意度。"),
    }


def assert_frozen_evidence_quality(artifact):
    """Check numbers in conditions/gaps as well as structured claims."""
    pattern = re.compile(r"\d+(?:\.\d+)?\s*(?:GB|TB|mAh|kg|CNY|元|秒)", re.IGNORECASE)

    def tokens(text):
        return {re.sub(r"\s+", "", item).casefold() for item in pattern.findall(text)}

    truth = json.dumps(artifact["scope"], ensure_ascii=False) + " ".join(text or "" for _, text in frozen_catalog(artifact["case"]).values())
    allowed = tokens(truth)
    for claim in artifact["result"]["claims"]:
        text = str(claim["value"]) + " " + (claim.get("conditions") or "")
        if claim.get("price"):
            text += " " + claim["price"]["conditions"]
        assert tokens(text) <= allowed, f"Unsupported numeric detail in claim {claim['id']}: {tokens(text) - allowed}"
    for gap in artifact["result"]["gaps"]:
        assert tokens(gap["description"]) <= allowed, f"Unsupported numeric detail in gap {gap['id']}: {tokens(gap['description']) - allowed}"


@pytest.mark.asyncio
@pytest.mark.parametrize("case,mode", [("launch-current", "full"), ("conditional-unavailable", "full"), ("laptop-mismatch", "delta")])
async def test_deepseek_collects_and_checks_evidence(tmp_path, monkeypatch, case, mode):
    from deerflow.agents.research.middleware import ResearchScopeMiddleware
    from deerflow.agents.research.storage import load_result
    from deerflow.agents.research.tools import RESEARCH_TOOLS
    from deerflow.agents.thread_state import get_thread_state_schema
    from deerflow.config import get_app_config
    from deerflow.models import create_chat_model
    from deerflow.utils.file_io import run_file_io

    config = get_app_config()
    selected = next(item for item in config.models if "deepseek" in item.use.lower())
    model = create_chat_model(selected.name, thinking_enabled=False, app_config=config, attach_tracing=False, model_overrides={"max_tokens": 3000, "timeout": 45, "max_retries": 0, "streaming": False})
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    category = "laptop" if case == "laptop-mismatch" else "phone"
    scope_data = discovery_scope(category).model_dump(mode="json")
    scope_data.update(target_candidate_count=1, allow_discovery=False, named_candidates=["行远 L1" if category == "laptop" else "极光 A1"], as_of_date=datetime.now(UTC).date().isoformat())
    catalog = frozen_catalog(case)
    root = "https://example.com/evidence-fixtures/"
    calls = []

    @tool("web_search")
    def search(query: str, max_results: int = 5) -> str:
        """Search synthetic public-page leads; use actual capture before relying on facts."""
        calls.append({"tool": "web_search", "query": query})
        # Discovery exposes an old release first; sales queries expose the other leads.
        keys = ["launch"] if "launch" in catalog and not any(word in query.lower() for word in ["价格", "售价", "京东", "商城", "当前", "price", "销售", "购买", "sale"]) else list(catalog)
        return json.dumps({"results": [{"url": root + key, "title": key, "kind": catalog[key][0], "snippet": (catalog[key][1] or "该公开渠道读取失败")[:95]} for key in keys[:max_results]]}, ensure_ascii=False)

    send = httpx.AsyncClient.send

    async def controlled_send(client, request, **kwargs):
        if request.url.host != "r.jina.ai":
            return await send(client, request, **kwargs)
        url = json.loads(request.content)["url"]
        calls.append({"tool": "capture_http", "url": url})
        page = catalog.get(url.removeprefix(root)) if url.startswith(root) else None
        if page is None or page[1] is None:
            return httpx.Response(429, text="synthetic unavailable", request=request)
        return httpx.Response(200, text=f"<html><head><title>{url.rsplit('/', 1)[-1]}</title></head><body><article><p>{page[1]}</p></article></body></html>", request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", controlled_send)
    saver = InMemorySaver()
    graph_config = {"configurable": {"thread_id": "research-thread"}, "recursion_limit": 80}
    # Stage-four behavior is separately evaluated. Seed only the confirmed plan via
    # the real tool chain; all stage-five decisions and extraction use DeepSeek.
    plan = planning_batch(category)
    plan["gaps"] = [gap for gap in plan["gaps"] if gap["id"] != "candidate-gap"]
    seed = evidence_graph([proposal(**scope_data), record_call(plan), AIMessage(content="候选和维度已保存，继续核对证据。")], saver, mode)
    initial = [HumanMessage(content="请研究指定产品配置的证据与当前价格，保留历史、条件、不匹配和未知。资料是合成样本，无需最终推荐或报告。先从 " + root + ("specs" if "specs" in catalog else "launch") + " 了解，核对公开销售渠道。")]
    pending = await seed.ainvoke({"messages": initial}, graph_config, context=turn_context("prepare", initial))
    confirmed = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
    seeded = await seed.ainvoke({"messages": confirmed}, graph_config, context=turn_context("confirm", confirmed))
    assert seeded["research"]["result"]["revision"] == 1
    limits = EvidenceEvaluationLimits()
    agent = create_agent(
        model=model,
        tools=[*RESEARCH_TOOLS, search],
        middleware=[ResearchScopeMiddleware(enabled=True, agent_name="researcher"), limits],
        state_schema=get_thread_state_schema(mode),
        checkpointer=saver,
        system_prompt="继续同一次已确认研究的证据采集工作，使用原工具保存事实、精确引用、价格观察与缺口，再回读。先前已保存候选和维度。本轮仅研究一个指定配置，不要求最终推荐。所有网页为合成资料。",
    )
    try:
        await asyncio.wait_for(agent.ainvoke({"messages": []}, graph_config, context=turn_context("confirm", confirmed)), 180)
    finally:
        state = (await agent.aget_state(graph_config)).values
        result = await run_file_io(load_result, state["research"]["result"], user_id="default", thread_id="research-thread", agent_name="researcher")
        artifact = {
            "case": case,
            "model": selected.model,
            "scope": scope_data,
            "model_attempts": limits.model_calls,
            "tool_attempts": limits.tool_calls,
            "seconds": round(time.monotonic() - limits.started, 2),
            "web_calls": calls,
            "messages": [message.model_dump(mode="json") for message in state["messages"]],
            "result": result.model_dump(mode="json"),
        }
        directory = Path(os.environ.get("DEER_FLOW_RESEARCH_EVAL_OUTPUT", str(tmp_path)))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{case}.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    captures = [source for source in result.sources if source.capture is not None]
    assert_frozen_evidence_quality(artifact)
    assert any(call["tool"] == "web_search" for call in calls), "No active sales-channel search"
    assert any(source.kind == "retailer" for source in captures), "No actual public sales-page attempt"
    assert result.claims and result.citations
    known = [claim for claim in result.claims if claim.price is not None]
    if case == "launch-current":
        assert any(claim.price.amount == 3299 and claim.price.basis == "public_offer" for claim in known)
        assert not any(claim.price.amount == 3999 and claim.price.basis == "public_offer" for claim in known)
    elif case == "conditional-unavailable":
        assert not any(claim.price.basis == "public_offer" for claim in known)
        assert result.gaps
        assert all(claim.price.basis in {"member", "subsidized", "promotion"} and claim.price.conditions for claim in known)
    else:
        assert not any(claim.configuration_id == "c1" and claim.price is not None and claim.price.amount == 3999 for claim in result.claims)
        assert not any(claim.configuration_id == "c1" and str(claim.value) == "85" for claim in result.claims)
        assert result.gaps
    assert all(
        source.capture is not None
        for claim in result.claims
        if claim.value is not None and claim.kind != "inference"
        for citation in result.citations
        if citation.claim_id == claim.id
        for source in result.sources
        if source.id == citation.source_id
    ), "Model used unbound text for a new observation"
