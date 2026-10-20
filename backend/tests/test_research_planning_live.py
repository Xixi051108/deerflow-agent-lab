"""Opt-in real DeepSeek behavior over frozen search pages, not live web quality."""

import asyncio
import json
import os
import re
import time
from pathlib import Path

import pytest
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from support.research_discovery_samples import CATALOG, controlled_web_tools, discovery_scope
from test_research_agent_integration import response_message, turn_context

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.environ.get("DEER_FLOW_RUN_LIVE_TESTS") != "1", reason="Explicit live opt-in required; real DeepSeek calls incur usage")]


class EvaluationLimits(AgentMiddleware):
    """Test protection only; does not implement the product's future budget."""

    def __init__(self):
        self.model_calls = 0
        self.tool_calls = 0
        self.started = time.monotonic()

    def admit(self, kind):
        if time.monotonic() - self.started > 180:
            raise RuntimeError("Evaluation wall-clock limit reached")
        field, cap = ("model_calls", 10) if kind == "model" else ("tool_calls", 12)
        setattr(self, field, getattr(self, field) + 1)
        if getattr(self, field) > cap:
            raise RuntimeError("Evaluation call limit reached")

    async def awrap_model_call(self, request, handler):
        self.admit("model")
        return await handler(request)

    async def awrap_tool_call(self, request, handler):
        self.admit("tool")
        return await handler(request)


def assert_controlled_plan_quality(artifact):
    """Sample-specific factual checks supplement, rather than replace, manual review."""
    result = artifact["result"]
    specifications = re.compile(r"\d+(?:\.\d+)?\s*(?:mAh|kg|GB)", re.IGNORECASE)

    def normalize(value):
        return re.sub(r"\s+", "", value).casefold()

    scope_text = json.dumps(artifact["scope"], ensure_ascii=False)
    for product in result["products"]:
        evidence = scope_text + " ".join(source["text"] or "" for source in result["sources"] if source["product_id"] == product["id"])
        supported = {normalize(value) for value in specifications.findall(evidence)}
        assert {normalize(value) for value in specifications.findall(product["reason"] or "")} <= supported, "Selection reason contains an unsupported numeric specification"
    if artifact["case"] == "laptop-shortage":
        assert "32GB" not in scope_text
        assert not any(re.search(r"(?:用户|原始|需求|意图|要求).{0,30}32\s*GB", gap["description"], re.IGNORECASE) for gap in result["gaps"]), "Gap invents a user requirement for 32GB"


@pytest.mark.asyncio
@pytest.mark.parametrize("case,category,mode,named_only", [("phone", "phone", "full", False), ("laptop-shortage", "laptop", "full", False), ("named-only", "phone", "delta", True)])
async def test_real_deepseek_discovers_and_plans(tmp_path, monkeypatch, case, category, mode, named_only):
    from deerflow.agents.research.middleware import ResearchScopeMiddleware
    from deerflow.agents.research.storage import load_result
    from deerflow.agents.research.tools import RESEARCH_TOOLS
    from deerflow.agents.thread_state import get_thread_state_schema
    from deerflow.config import get_app_config
    from deerflow.models import create_chat_model

    config = get_app_config()
    selected = next((item for item in config.models if "deepseek" in item.use.lower()), None)
    assert selected is not None, "Existing DeepSeek configuration required"
    model = create_chat_model(selected.name, thinking_enabled=False, app_config=config, attach_tracing=False, model_overrides={"max_tokens": 3000, "timeout": 45, "max_retries": 0, "streaming": False})
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    limits, calls = EvaluationLimits(), []
    scope = discovery_scope(category, named_only=named_only)
    agent = create_agent(
        model=model,
        tools=[*RESEARCH_TOOLS, *controlled_web_tools(category, calls)],
        middleware=[ResearchScopeMiddleware(enabled=True, agent_name="researcher"), limits],
        state_schema=get_thread_state_schema(mode),
        checkpointer=InMemorySaver(),
        system_prompt="你是消费者选购研究助手。本次只完成候选发现和比较维度规划，使用工具保存结构化结果并简短说明。资料为合成测试样本，不提供真实购买建议，不生成报告文件。",
    )
    graph_config = {"configurable": {"thread_id": "research-thread"}, "recursion_limit": 64}
    initial = [HumanMessage(content="请按以下完整范围提议原确认卡；不要擅自修改字段。确认后执行候选发现与维度规划，记录排除理由和资料缺口。\n" + scope.model_dump_json())]
    final = None
    try:
        pending = await asyncio.wait_for(agent.ainvoke({"messages": initial}, graph_config, context=turn_context("prepare", initial)), 180)
        request_id = pending["research"]["session"]["pending_confirmation"]["request_id"]
        confirmed = [response_message(request_id)]
        final = await asyncio.wait_for(agent.ainvoke({"messages": confirmed}, graph_config, context=turn_context("confirm", confirmed)), max(1, 180 - (time.monotonic() - limits.started)))
    finally:
        state = (await agent.aget_state(graph_config)).values
        messages = [message.model_dump(mode="json") for message in state.get("messages", [])]
        directory = Path(os.environ.get("DEER_FLOW_RESEARCH_EVAL_OUTPUT", str(tmp_path)))
        directory.mkdir(parents=True, exist_ok=True)
        artifact = {
            "case": case,
            "model": selected.model,
            "scope": scope.model_dump(mode="json"),
            "model_attempts": limits.model_calls,
            "tool_attempts": limits.tool_calls,
            "seconds": round(time.monotonic() - limits.started, 2),
            "controlled_web_calls": calls,
            "messages": messages,
            "research": state.get("research"),
        }
        if state.get("research", {}).get("result"):
            result = await asyncio.to_thread(load_result, state["research"]["result"], user_id="default", thread_id="research-thread", agent_name="researcher")
            artifact["result"] = result.model_dump(mode="json")
        (directory / f"{case}.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    assert final is not None and final["research"]["result"] is not None
    result = artifact["result"]
    assert artifact["scope"] == artifact["research"]["session"]["scope"], "Model changed the fully supplied scope"
    assert_controlled_plan_quality(artifact)
    candidates = {row["name"] for row in result["products"] if row["disposition"] == "candidate"}
    expected = {"行远 L1"} if category == "laptop" else {"极光 A1"} if named_only else {"极光 A1", "长航 B2"}
    assert candidates == expected
    assert all(row["reason"] and row["reason"].strip() for row in result["products"])
    assert all(row["description"] and row["basis"].strip() for row in result["dimensions"])
    assert result["gaps"], "Unprovided current prices and any shortage must remain explicit"
    if len(candidates) < scope.target_candidate_count:
        assert any(row["product_id"] is None and row["dimension_id"] is None for row in result["gaps"]), "Candidate shortage needs a study-level gap"
    assert any(name == "web_search" for name, _ in calls)
    urls = {f"https://example.com/research-fixtures/{slug}" for slug, _, _ in CATALOG[category]}
    assert all(row["url"] in urls for row in result["sources"])
    if not named_only:
        assert all(row["discovery_source_ids"] for row in result["products"] if row["disposition"] == "candidate")
    words = " ".join(row["name"] + row["description"] + row["basis"] for row in result["dimensions"])
    assert any(word in words for word in (["内存", "开发", "兼容"] if category == "laptop" else ["影像", "拍照", "摄影"]))
    assert any(word in words for word in (["重量", "便携", "携带"] if category == "laptop" else ["续航", "电池"]))
