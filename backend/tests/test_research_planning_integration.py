"""Reproduce the missing count guard through the existing research graph."""

import asyncio
import json

import pytest
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from support.research_discovery_samples import controlled_web_tools, discovery_scope, planning_batch
from test_research_agent_integration import call, invoke_turn, proposal, response_message, turn_context
from test_research_data_integration import DataModel, data_graph, record_call, tool_payloads
from test_research_data_integration import research_home as research_home
from test_research_gateway_http import gateway as gateway

controlled_search, controlled_fetch = controlled_web_tools()


def planning_graph(replies, saver=None, mode="full", category="phone", calls=None, external_tools=None):
    from deerflow.agents.research.middleware import ResearchScopeMiddleware
    from deerflow.agents.research.tools import RESEARCH_TOOLS
    from deerflow.agents.thread_state import get_thread_state_schema

    return create_agent(
        model=DataModel(replies=replies),
        tools=[*RESEARCH_TOOLS, *(controlled_web_tools(category, calls) if external_tools is None else external_tools)],
        middleware=[ResearchScopeMiddleware(enabled=True, agent_name="researcher")],
        state_schema=get_thread_state_schema(mode),
        checkpointer=saver,
    )


def plan_steps(category="phone"):
    return [
        call("web_search", {"query": "便携开发笔记本" if category == "laptop" else "摄影续航手机"}, "search"),
        call("web_fetch", {"url": "https://example.com/research-fixtures/portable" if category == "laptop" else "https://example.com/research-fixtures/aurora"}, "fetch"),
        record_call(planning_batch(category)),
        call("read_research_data", {"section": "products"}, "read-products"),
        call("read_research_data", {"section": "dimensions"}, "read-dimensions"),
        call("read_research_data", {"section": "gaps"}, "read-gaps"),
        AIMessage(content="已保存未核实的候选规划及缺口"),
    ]


def test_confirmed_candidate_count_is_enforced_before_snapshot_write(research_home):
    batch = {"products": [{"id": letter, "name": letter, "reason": "待核实"} for letter in ("A", "B", "C")]}
    agent = data_graph([proposal(), record_call(batch), AIMessage(content="结束受控实验")], InMemorySaver())
    pending = invoke_turn(agent, [HumanMessage(content="准备研究")], "prepare")
    result = invoke_turn(agent, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])], "confirm")
    payload = tool_payloads(result, "record_research_data")[-1]
    assert payload.get("error", {}).get("code") == "candidate_limit_exceeded", payload
    assert result["research"]["result"] is None
    assert not list(research_home.rglob("*.json"))


def test_discovery_instructions_reach_only_the_research_model(research_home, monkeypatch):
    from langchain_core.messages import SystemMessage
    from test_research_agent_integration import ScriptedResearchModel, graph

    seen = []
    generate = ScriptedResearchModel._generate

    def capture(self, messages, *args, **kwargs):
        seen.append(messages)
        return generate(self, messages, *args, **kwargs)

    monkeypatch.setattr(ScriptedResearchModel, "_generate", capture)
    study = data_graph([proposal(topic="untrusted-topic-do-not-promote"), AIMessage(content="范围已整理")], InMemorySaver())
    invoke_turn(study, [HumanMessage(content="准备研究")], "prepare")
    invoke_turn(study, [HumanMessage(content="补充条件")], "new-text")
    authority = "\n".join(str(message.content) for message in seen[-1] if isinstance(message, SystemMessage))
    assert "discovery_source_ids" in authority
    assert "untrusted-topic-do-not-promote" not in authority
    ordinary = graph([AIMessage(content="普通回答")], [], enabled=False)
    invoke_turn(ordinary, [HumanMessage(content="普通问题")], "ordinary")
    assert not any("discovery_source_ids" in str(message.content) for message in seen[-1] if isinstance(message, SystemMessage))


@pytest.mark.parametrize("category", ["phone", "laptop"])
@pytest.mark.parametrize("mode", ["full", "delta"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_confirm_search_fetch_record_and_read_a_plan(research_home, category, mode, asynchronous):
    calls = []
    agent = planning_graph([proposal(**discovery_scope(category).model_dump(mode="json")), *plan_steps(category)], InMemorySaver(), mode, category, calls)

    def run(messages, run_id):
        config = {"configurable": {"thread_id": "research-thread"}, "recursion_limit": 64}
        if asynchronous:
            return asyncio.run(agent.ainvoke({"messages": messages}, config, context=turn_context(run_id, messages)))
        return agent.invoke({"messages": messages}, config, context=turn_context(run_id, messages))

    pending = run([HumanMessage(content="准备研究")], "prepare")
    assert calls == []
    result = run([response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])], "confirm")
    assert [name for name, _ in calls] == ["web_search", "web_fetch"]
    assert result["research"]["result"]["revision"] == 1
    assert tool_payloads(result, "read_research_data")[-3]["records"][0]["discovery_source_ids"] == ["s1"]
    assert tool_payloads(result, "read_research_data")[-2]["records"][0]["name"] == ("便携重量" if category == "laptop" else "影像能力")
    assert any(row["product_id"] is None for row in tool_payloads(result, "read_research_data")[-1]["records"])


@pytest.mark.parametrize("mode", ["full", "delta"])
@pytest.mark.parametrize("failure", ["count", "source", "named"])
def test_invalid_later_batch_keeps_the_previous_selected_snapshot(research_home, mode, failure):
    first = planning_batch()
    scope = discovery_scope().model_dump(mode="json")
    if failure == "count":
        scope["target_candidate_count"] = 1
        second = {"products": [{"id": "p2", "name": "第二款", "reason": "不能绕过累计数量"}]}
        code = "candidate_limit_exceeded"
    elif failure == "source":
        second = {"sources": [{**first["sources"][0], "status": "failed", "failure_reason": "固定读取失败"}]}
        code = "invalid_discovery_source"
    else:
        scope.update(allow_discovery=False, named_candidates=["极光 A1"], target_candidate_count=1)
        second = {"products": [{"id": "p1", "name": "名单外替换", "reason": "不能借用旧ID换对象"}]}
        code = "candidate_outside_scope"
    agent = planning_graph([proposal(**scope), record_call(first), record_call(second, revision=1), call("read_research_data", {"section": "products"}, "after-error"), AIMessage(content="保留原结果")], InMemorySaver(), mode)
    pending = invoke_turn(agent, [HumanMessage(content="准备研究")], "prepare")
    result = invoke_turn(agent, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])], "confirm")
    assert tool_payloads(result, "record_research_data")[-1]["error"]["code"] == code
    assert result["research"]["result"]["revision"] == 1
    assert tool_payloads(result, "read_research_data")[-1]["records"][0]["name"] == "极光 A1"
    assert len(list(research_home.rglob("*.json"))) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["full", "delta"])
async def test_plan_fields_survive_real_sqlite_close_and_reopen(research_home, mode):
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    path = str(research_home / "planning.sqlite")
    config = {"configurable": {"thread_id": "research-thread"}}
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        agent = planning_graph([proposal(**discovery_scope().model_dump(mode="json"))], saver, mode)
        messages = [HumanMessage(content="准备研究")]
        pending = await agent.ainvoke({"messages": messages}, config, context=turn_context("prepare", messages))
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        agent = planning_graph(plan_steps(), saver, mode)
        messages = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
        saved = await agent.ainvoke({"messages": messages}, config, context=turn_context("confirm", messages))
    async with AsyncSqliteSaver.from_conn_string(path) as saver:
        agent = planning_graph([proposal(**discovery_scope().model_dump(mode="json")), call("read_research_data", {"section": "products"}, "read-restored"), AIMessage(content="已恢复")], saver, mode)
        assert (await agent.aget_state(config)).values["research"]["result"] == saved["research"]["result"]
        messages = [HumanMessage(content="继续")]
        pending = await agent.ainvoke({"messages": messages}, config, context=turn_context("reopen", messages))
        messages = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
        restored = await agent.ainvoke({"messages": messages}, config, context=turn_context("reconfirm", messages))
        assert tool_payloads(restored, "read_research_data")[-1]["records"][0]["discovery_source_ids"] == ["s1"]


def test_original_factory_worker_http_and_sse_save_discovery_fields(gateway, monkeypatch):
    from test_research_gateway_http import run, values

    from deerflow.config.app_config import AppConfig, get_app_config, set_app_config

    client, _ = gateway
    settings = get_app_config().model_dump()
    settings["tools"] = [
        {"name": "web_search", "group": "web", "use": "test_research_planning_integration:controlled_search"},
        {"name": "web_fetch", "group": "web", "use": "test_research_planning_integration:controlled_fetch"},
    ]
    set_app_config(AppConfig.model_validate(settings))
    model = DataModel(replies=[proposal(**discovery_scope().model_dump(mode="json")), *plan_steps()])
    monkeypatch.setattr("deerflow.agents.lead_agent.agent.create_chat_model", lambda **kwargs: model)
    pending = values(run(client, [{"role": "user", "content": "准备受控候选规划"}]))[-1]
    final = values(run(client, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"]).model_dump(mode="json")]))[-1]
    refreshed = client.get("/api/threads/research-http/state").json()["values"]
    assert final["research"]["result"]["counts"]["products"] == 1
    assert refreshed["research"] == final["research"]
    records = next(json.loads(message["content"])["records"] for message in refreshed["messages"] if message.get("name") == "read_research_data" and json.loads(message["content"])["section"] == "products")
    assert records[0]["discovery_source_ids"] == ["s1"]
    history = client.get(f"/api/threads/research-http/runs/{final['research']['last_run_id']}/messages").json()["data"]
    assert any(row["content"].get("name") == "record_research_data" for row in history if isinstance(row.get("content"), dict))


def test_embedded_factory_receives_the_same_discovery_contract(gateway, monkeypatch):
    from langchain_core.messages import SystemMessage

    from deerflow.client import DeerFlowClient
    from deerflow.persistence.agents import get_agent_store
    from deerflow.runtime.user_context import get_effective_user_id

    get_agent_store().create("planning-embedded", {"name": "planning-embedded", "research_enabled": True, "skills": [], "memory_enabled": False, "allowed_subagents": []}, "受控研究助手", user_id=get_effective_user_id())
    seen = []
    generate = DataModel._generate

    def capture(self, messages, *args, **kwargs):
        seen.extend(messages)
        return generate(self, messages, *args, **kwargs)

    monkeypatch.setattr(DataModel, "_generate", capture)
    monkeypatch.setattr("deerflow.client.create_chat_model", lambda **kwargs: DataModel(replies=[AIMessage(content="请确认范围")]))
    client = DeerFlowClient(agent_name="planning-embedded", available_skills=set(), checkpointer=InMemorySaver())
    events = list(client.stream("准备候选发现", thread_id="planning-embedded"))
    assert any("discovery_source_ids" in str(message.content) for message in seen if isinstance(message, SystemMessage))
    assert any(event.type == "values" and event.data.get("research") for event in events)


@pytest.mark.parametrize("failure", ["empty", "error", "unavailable"])
def test_retrieval_gaps_can_be_saved_without_inventing_products(research_home, failure):
    from langchain_core.tools import tool

    @tool("web_search")
    def failed_search(query: str) -> str:
        """Return a controlled empty result or retrieval error."""
        return json.dumps({"results": []} if failure == "empty" else {"error": "controlled retrieval failure"})

    gap = {"gaps": [{"id": "retrieval-gap", "reason": "retrieval_unavailable", "description": "本次检索未获得可用资料，不能断言市场不存在产品"}]}
    replies = [proposal()]
    if failure != "unavailable":
        replies.append(call("web_search", {"query": "手机"}, "failed-search"))
    replies.extend([record_call(gap), call("read_research_data", {"section": "gaps"}, "read-gap"), AIMessage(content="已保留检索缺口")])
    agent = planning_graph(replies, InMemorySaver(), external_tools=[] if failure == "unavailable" else [failed_search])
    pending = invoke_turn(agent, [HumanMessage(content="准备研究")], "prepare")
    result = invoke_turn(agent, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])], "confirm")
    assert result["research"]["result"]["counts"]["products"] == 0
    assert result["research"]["result"]["counts"]["sources"] == 0
    assert tool_payloads(result, "read_research_data")[-1]["records"][0]["reason"] == "retrieval_unavailable"
