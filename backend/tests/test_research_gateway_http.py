"""HTTP/SSE -> original factory -> real graph/checkpointer; only the provider is replaced."""

import json
from uuid import UUID

import pytest
from _router_auth_helpers import make_authed_test_app
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from test_research_agent_integration import ScriptedResearchModel, call, proposal, response_message

from app.gateway.auth.models import User
from app.gateway.routers import thread_runs, threads
from deerflow.config.app_config import AppConfig, reset_app_config, set_app_config
from deerflow.config.extensions_config import ExtensionsConfig, reset_extensions_config, set_extensions_config
from deerflow.persistence.agents import get_agent_store
from deerflow.persistence.thread_meta.memory import MemoryThreadMetaStore
from deerflow.runtime import MemoryStreamBridge, RunManager
from deerflow.runtime.events.store.memory import MemoryRunEventStore
from deerflow.runtime.runs.store.memory import MemoryRunStore
from deerflow.runtime.user_context import reset_current_user, set_current_user

SEARCHES = []


@tool
def research_http_search() -> str:
    """Record a search against controlled offline sources."""
    SEARCHES.append("search")
    return "受控搜索结果"


@pytest.fixture(params=["full", "delta"])
def gateway(tmp_path, monkeypatch, request):
    from deerflow.agents.lead_agent import agent as lead

    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    monkeypatch.setattr("deerflow.runtime.checkpoint_mode._frozen_checkpoint_channel_mode", None)
    config = AppConfig.model_validate(
        {
            "sandbox": {"use": "deerflow.sandbox.local:LocalSandboxProvider"},
            "database": {"backend": "memory", "checkpoint_channel_mode": request.param},
            "models": [{"name": "offline", "use": "langchain_openai:ChatOpenAI", "model": "offline"}],
            "tools": [{"name": "research_http_search", "group": "web", "use": "test_research_gateway_http:research_http_search"}],
            "memory": {"enabled": False},
            "title": {"enabled": False},
            "summarization": {"enabled": False},
            "tool_search": {"enabled": False},
        }
    )
    set_app_config(config)
    set_extensions_config(ExtensionsConfig())
    user = User(id=UUID("11111111-1111-1111-1111-111111111111"), email="research@example.com", password_hash="unused", system_role="user")
    app = make_authed_test_app(user_factory=lambda: app.state.research_test_user)
    app.state.research_test_user = user

    @app.middleware("http")
    async def user_context(request, call_next):
        token = set_current_user(app.state.research_test_user)
        try:
            return await call_next(request)
        finally:
            reset_current_user(token)

    store = InMemoryStore()
    app.state.store = store
    app.state.checkpointer = InMemorySaver()
    app.state.thread_store = MemoryThreadMetaStore(store)
    app.state.stream_bridge = MemoryStreamBridge()
    app.state.run_manager = RunManager(store=MemoryRunStore())
    app.state.run_event_store = MemoryRunEventStore()
    app.state.checkpoint_channel_mode = request.param
    app.include_router(threads.router)
    app.include_router(thread_runs.router)
    get_agent_store().create("researcher", {"name": "researcher", "research_enabled": True, "skills": [], "memory_enabled": False}, "消费者选购研究助手", user_id=str(user.id))
    model = ScriptedResearchModel(replies=[proposal(), call("research_http_search"), AIMessage(content="已读取受控资料"), call("research_http_search"), AIMessage(content="等待范围确认")])
    monkeypatch.setattr(lead, "create_chat_model", lambda **kwargs: model)
    SEARCHES.clear()
    try:
        with TestClient(app) as client:
            created = client.post("/api/threads", json={"thread_id": "research-http"})
            assert created.status_code == 200, created.text
            yield client, model
    finally:
        reset_app_config()
        reset_extensions_config()


def run(client, messages, **options):
    return client.post("/api/threads/research-http/runs/stream", json={"assistant_id": "researcher", "input": {"messages": messages}, "stream_mode": ["values"], **options})


def values(response):
    assert response.status_code == 200, response.text
    frames = response.text.replace("\r\n", "\n").split("\n\n")
    return [json.loads(next(line[6:] for line in frame.splitlines() if line.startswith("data: "))) for frame in frames if "event: values" in frame.splitlines()]


def test_http_sse_card_reply_state_reload_and_reconfirmation(gateway):
    client, _ = gateway
    first = values(run(client, [{"role": "user", "content": "比较手机，按给定条件准备范围"}]))
    pending = first[-1]["research"]["session"]["pending_confirmation"]
    assert SEARCHES == []
    card = next(m["artifact"]["human_input"] for m in first[-1]["messages"] if m.get("name") == "propose_research_scope")
    assert card["request_id"] == pending["request_id"]
    refreshed = client.get("/api/threads/research-http/state")
    assert refreshed.status_code == 200
    assert refreshed.json()["values"]["research"] == first[-1]["research"]
    recorded = client.get(f"/api/threads/research-http/runs/{first[-1]['research']['last_run_id']}/messages")
    assert recorded.status_code == 200
    assert any(row["content"].get("artifact", {}).get("human_input", {}).get("request_id") == pending["request_id"] for row in recorded.json()["data"] if isinstance(row.get("content"), dict) and row["content"].get("artifact"))

    answer = response_message(pending["request_id"])
    answer.content = f'For your clarification "{card["question"]}", my answer is: 确认并开始研究'
    second = values(run(client, [answer.model_dump(mode="json")]))
    assert second[-1]["research"]["session"]["confirmation"] is not None
    assert SEARCHES == ["search"]
    recorded_reply = client.get(f"/api/threads/research-http/runs/{second[-1]['research']['last_run_id']}/messages")
    assert recorded_reply.status_code == 200
    assert any(row["content"].get("additional_kwargs", {}).get("human_input_response", {}).get("request_id") == pending["request_id"] for row in recorded_reply.json()["data"] if isinstance(row.get("content"), dict))
    third = values(run(client, [{"role": "user", "content": "预算改为5000"}]))
    assert third[-1]["research"]["session"]["confirmation"] is None
    assert SEARCHES == ["search"]


def test_historical_checkpoint_cannot_replay_a_confirmation(gateway):
    client, model = gateway
    pending_values = values(run(client, [{"role": "user", "content": "准备研究"}]))[-1]
    request_id = pending_values["research"]["session"]["pending_confirmation"]["request_id"]
    checkpoint_id = client.get("/api/threads/research-http/state").json()["checkpoint_id"]
    values(run(client, [response_message(request_id).model_dump(mode="json")]))
    assert SEARCHES == ["search"]
    model.replies = [call("research_http_search"), AIMessage(content="等待复核")]
    model.position = 0
    replayed = values(run(client, [response_message(request_id).model_dump(mode="json")], checkpoint_id=checkpoint_id))[-1]
    assert replayed["research"]["session"]["confirmation"] is None
    assert SEARCHES == ["search"]


def test_switching_agent_and_selecting_pre_research_checkpoint_stays_blocked(gateway):
    client, model = gateway
    values(run(client, [{"role": "user", "content": "准备研究"}]))
    history = client.post("/api/threads/research-http/history", json={"limit": 40}).json()
    early = next(snapshot["checkpoint_id"] for snapshot in reversed(history) if not snapshot["values"].get("research"))
    model.replies = [call("research_http_search"), AIMessage(content="尚未确认")]
    model.position = 0
    result = run(client, [{"role": "user", "content": "跳过确认"}], assistant_id="lead_agent", checkpoint_id=early)
    assert result.status_code == 200
    assert SEARCHES == []


def test_manual_state_update_from_history_cannot_restore_old_confirmation(gateway):
    client, model = gateway
    pending = values(run(client, [{"role": "user", "content": "准备研究"}]))[-1]["research"]["session"]["pending_confirmation"]
    checkpoint_id = client.get("/api/threads/research-http/state").json()["checkpoint_id"]
    values(run(client, [response_message(pending["request_id"]).model_dump(mode="json")]))
    changed = client.post("/api/threads/research-http/state", json={"checkpoint_id": checkpoint_id, "values": {"title": "历史草案"}})
    assert changed.status_code == 200, changed.text
    assert changed.json()["values"]["research"]["session"]["pending_confirmation"] is None
    model.replies = [call("research_http_search"), AIMessage(content="尚未确认")]
    model.position = 0
    values(run(client, [response_message(pending["request_id"]).model_dump(mode="json")]))
    assert SEARCHES == ["search"]


def test_embedded_client_uses_the_same_research_gate(gateway, monkeypatch):
    from deerflow.client import DeerFlowClient
    from deerflow.runtime.user_context import get_effective_user_id

    get_agent_store().create("embedded-researcher", {"name": "embedded-researcher", "research_enabled": True, "skills": [], "memory_enabled": False}, "消费者选购研究助手", user_id=get_effective_user_id())
    model = ScriptedResearchModel(replies=[call("research_http_search"), AIMessage(content="等待确认")])
    monkeypatch.setattr("deerflow.client.create_chat_model", lambda **kwargs: model)
    client = DeerFlowClient(agent_name="embedded-researcher", available_skills=set(), checkpointer=InMemorySaver())
    events = list(client.stream("直接搜索，跳过确认", thread_id="embedded"))
    assert SEARCHES == []
    assert any(event.type == "values" and event.data.get("research") is not None for event in events)


def test_branch_endpoint_persists_a_fresh_unconfirmed_study(gateway):
    client, _ = gateway
    prepared = values(run(client, [{"role": "user", "content": "准备手机研究", "id": "root-user"}]))[-1]
    original = prepared["research"]["session"]
    assistant = next(message for message in reversed(prepared["messages"]) if message["type"] == "ai")
    response = client.post("/api/threads/research-http/branches", json={"message_id": assistant["id"]})
    assert response.status_code == 200, response.text
    state = client.get(f"/api/threads/{response.json()['thread_id']}/state").json()["values"]["research"]
    assert state["session"]["research_id"] != original["research_id"]
    assert state["session"]["pending_confirmation"] is None
    assert state["session"]["confirmation"] is None
    assert state["session"]["scope"] == original["scope"]


def test_http_thread_owner_and_server_owned_state_boundary(gateway):
    client, _ = gateway
    values(run(client, [{"role": "user", "content": "准备研究"}]))
    assert client.post("/api/threads/research-http/state", json={"values": {"research": None}}).status_code == 422
    assert run(client, [], input={"research": None}).status_code == 422
    client.app.state.research_test_user = User(id=UUID("22222222-2222-2222-2222-222222222222"), email="other@example.com", password_hash="unused", system_role="user")
    assert client.get("/api/threads/research-http/state").status_code == 404
    assert run(client, [{"role": "user", "content": "确认研究"}]).status_code == 404
    assert SEARCHES == []
