"""Discovery plans use the original asynchronous file-I/O boundary."""

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from support.research_discovery_samples import discovery_scope
from test_research_agent_integration import proposal, response_message, turn_context
from test_research_data_integration import research_home as research_home
from test_research_data_integration import tool_payloads
from test_research_planning_integration import plan_steps, planning_graph


@pytest.fixture(params=["full", "delta"])
def plan_graph(research_home, request):
    return planning_graph([proposal(**discovery_scope().model_dump(mode="json")), *plan_steps()], InMemorySaver(), request.param)


@pytest.mark.asyncio
async def test_plan_record_and_read_do_not_block_the_event_loop(plan_graph):
    config = {"configurable": {"thread_id": "research-thread"}}
    messages = [HumanMessage(content="准备候选规划")]
    pending = await plan_graph.ainvoke({"messages": messages}, config, context=turn_context("prepare", messages))
    messages = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
    result = await plan_graph.ainvoke({"messages": messages}, config, context=turn_context("confirm", messages))
    assert result["research"]["result"]["revision"] == 1
    assert tool_payloads(result, "read_research_data")[-3]["records"][0]["discovery_source_ids"] == ["s1"]
