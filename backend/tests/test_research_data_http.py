"""New research tools through original factory, worker, authenticated HTTP and SSE."""

import json

from langchain_core.messages import AIMessage
from test_research_agent_integration import call, proposal, response_message
from test_research_data_integration import DataModel, record_call
from test_research_gateway_http import gateway as gateway
from test_research_gateway_http import run, values


def record_over_http(gateway, monkeypatch):
    client, _ = gateway
    model = DataModel(replies=[proposal(), record_call(), call("read_research_data", {"section": "claims"}, "read"), AIMessage(content="受控数据已记录")])
    monkeypatch.setattr("deerflow.agents.lead_agent.agent.create_chat_model", lambda **kwargs: model)
    pending = values(run(client, [{"role": "user", "content": "准备研究", "id": "research-user"}]))[-1]
    confirmed = values(run(client, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"]).model_dump(mode="json")]))[-1]
    return client, model, confirmed


def test_http_sse_state_and_event_history_contain_validated_projection(gateway, monkeypatch):
    client, _, confirmed = record_over_http(gateway, monkeypatch)
    assert confirmed["research"]["result"]["counts"]["claims"] == 2
    refreshed = client.get("/api/threads/research-http/state").json()["values"]
    assert refreshed["research"] == confirmed["research"]
    read = next(m for m in reversed(refreshed["messages"]) if m.get("name") == "read_research_data")
    assert json.loads(read["content"])["records"][0]["value"] == "190"
    events = client.get(f"/api/threads/research-http/runs/{confirmed['research']['last_run_id']}/messages").json()["data"]
    assert any(row["content"].get("name") == "record_research_data" for row in events if isinstance(row.get("content"), dict))
    assert client.post("/api/threads/research-http/state", json={"values": {"research": refreshed["research"]}}).status_code == 422
    assert run(client, [], input={"research": refreshed["research"]}).status_code == 422
    from uuid import UUID

    user = client.app.state.research_test_user
    client.app.state.research_test_user = user.model_copy(update={"id": UUID("22222222-2222-2222-2222-222222222222")})
    assert client.get("/api/threads/research-http/state").status_code == 404
    assert run(client, [{"role": "user", "content": "读取研究数据"}]).status_code == 404


def test_http_branch_and_historical_resume_clear_result_selection(gateway, monkeypatch):
    client, model, confirmed = record_over_http(gateway, monkeypatch)
    assert confirmed["research"]["result"] is not None
    checkpoint = client.get("/api/threads/research-http/state").json()["checkpoint_id"]
    assistant = next(m for m in reversed(confirmed["messages"]) if m["type"] == "ai")
    response = client.post("/api/threads/research-http/branches", json={"message_id": assistant["id"]})
    assert response.status_code == 200, response.text
    branch = client.get(f"/api/threads/{response.json()['thread_id']}/state").json()["values"]["research"]
    assert branch["result"] is None
    assert branch["session"]["research_id"] != confirmed["research"]["session"]["research_id"]
    changed = client.post("/api/threads/research-http/state", json={"checkpoint_id": checkpoint, "values": {"title": "历史草案"}})
    assert changed.status_code == 200, changed.text
    assert changed.json()["values"]["research"]["result"] is None
    model.replies, model.position = [call("read_research_data", {"section": "claims"}), AIMessage(content="先重新确认")], 0
    resumed = values(run(client, [{"role": "user", "content": "回看历史"}], checkpoint_id=checkpoint))[-1]
    assert resumed["research"]["result"] is None
    assert resumed["research"]["session"]["confirmation"] is None


def test_embedded_client_registers_both_data_tools_with_the_same_gate(gateway, monkeypatch):
    from langgraph.checkpoint.memory import InMemorySaver

    from deerflow.client import DeerFlowClient
    from deerflow.persistence.agents import get_agent_store
    from deerflow.runtime.user_context import get_effective_user_id

    get_agent_store().create("data-embedded", {"name": "data-embedded", "research_enabled": True, "skills": [], "memory_enabled": False}, "合成研究助手", user_id=get_effective_user_id())
    model = DataModel(replies=[record_call(), call("read_research_data", {"section": "products"}), AIMessage(content="请先确认范围")])
    monkeypatch.setattr("deerflow.client.create_chat_model", lambda **kwargs: model)
    client = DeerFlowClient(agent_name="data-embedded", available_skills=set(), checkpointer=InMemorySaver())
    events = list(client.stream("直接写入数据", thread_id="data-embedded"))
    for name in ("record_research_data", "read_research_data"):
        results = [event.data for event in events if event.type == "messages-tuple" and event.data.get("name") == name]
        assert results, name
        assert json.loads(results[-1]["content"])["error"]["code"] == "scope_incomplete"
