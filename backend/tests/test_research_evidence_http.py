"""Evidence capture through the original authenticated HTTP worker and client."""

import json

from langchain_core.messages import AIMessage
from support.research_discovery_samples import discovery_scope, planning_batch
from test_research_agent_integration import call, proposal, response_message
from test_research_data_integration import record_call
from test_research_evidence_integration import URL, EvidenceModel, collect_call, offer_batch
from test_research_evidence_integration import frozen_reader as frozen_reader
from test_research_gateway_http import gateway as gateway
from test_research_gateway_http import run, values


def test_capture_and_price_survive_http_sse_state_reload(gateway, frozen_reader, monkeypatch):
    client, _ = gateway
    model = EvidenceModel(
        replies=[
            proposal(**discovery_scope().model_dump(mode="json")),
            record_call(planning_batch()),
            collect_call(),
            record_call(offer_batch(), revision=2),
            call("read_research_data", {"section": "claims"}),
            AIMessage(content="已保存，仍需语义审核"),
        ]
    )
    monkeypatch.setattr("deerflow.agents.lead_agent.agent.create_chat_model", lambda **kwargs: model)
    pending = values(run(client, [{"role": "user", "content": URL, "id": "research-user"}]))[-1]
    confirmed = values(run(client, [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"]).model_dump(mode="json")]))[-1]
    assert confirmed["research"]["result"]["revision"] == 3
    refreshed = client.get("/api/threads/research-http/state").json()["values"]
    assert refreshed["research"] == confirmed["research"]
    page = json.loads(next(m["content"] for m in reversed(refreshed["messages"]) if m.get("name") == "read_research_data"))
    assert page["records"][0]["evidence_assessment"]["status"] == "captured_offer_observation"
    events = client.get(f"/api/threads/research-http/runs/{confirmed['research']['last_run_id']}/messages").json()["data"]
    assert any(row["content"].get("name") == "collect_research_source" for row in events if isinstance(row.get("content"), dict))
    assert len(frozen_reader) == 1


def test_embedded_client_registers_capture_and_preserves_confirmation_gate(gateway, frozen_reader, monkeypatch):
    from langgraph.checkpoint.memory import InMemorySaver

    from deerflow.client import DeerFlowClient
    from deerflow.persistence.agents import get_agent_store
    from deerflow.runtime.user_context import get_effective_user_id

    get_agent_store().create("evidence-embedded", {"name": "evidence-embedded", "research_enabled": True, "skills": [], "memory_enabled": False}, "合成研究助手", user_id=get_effective_user_id())
    model = EvidenceModel(replies=[collect_call(), AIMessage(content="请先确认")])
    monkeypatch.setattr("deerflow.client.create_chat_model", lambda **kwargs: model)
    client = DeerFlowClient(agent_name="evidence-embedded", available_skills=set(), checkpointer=InMemorySaver())
    events = list(client.stream(URL, thread_id="evidence-embedded"))
    results = [event.data for event in events if event.type == "messages-tuple" and event.data.get("name") == "collect_research_source"]
    assert results and json.loads(results[-1]["content"])["error"]["code"] == "scope_incomplete"
    assert frozen_reader == []
