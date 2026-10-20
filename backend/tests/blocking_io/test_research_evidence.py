"""Real extraction, configuration and persistence stay off the async event loop."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from support.research_discovery_samples import discovery_scope, planning_batch
from test_research_agent_integration import call, proposal, response_message, turn_context
from test_research_data_integration import record_call, tool_payloads
from test_research_data_integration import research_home as research_home
from test_research_evidence_integration import URL, collect_call, evidence_graph, offer_batch
from test_research_evidence_integration import frozen_reader as frozen_reader


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["full", "delta"])
async def test_capture_and_price_do_not_block_event_loop(research_home, frozen_reader, mode):
    agent = evidence_graph(
        [proposal(**discovery_scope().model_dump(mode="json")), record_call(planning_batch()), collect_call(), record_call(offer_batch(), revision=2), call("read_research_data", {"section": "claims"}), AIMessage(content="已存")],
        InMemorySaver(),
        mode,
    )
    config = {"configurable": {"thread_id": "research-thread"}}
    messages = [HumanMessage(content=URL)]
    pending = await agent.ainvoke({"messages": messages}, config, context=turn_context("prepare", messages))
    messages = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
    result = await agent.ainvoke({"messages": messages}, config, context=turn_context("confirm", messages))
    assert result["research"]["result"]["revision"] == 3
    assert tool_payloads(result, "read_research_data")[-1]["records"][0]["evidence_assessment"]["status"] == "captured_offer_observation"
