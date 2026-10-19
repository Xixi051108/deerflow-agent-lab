"""Research snapshot tools must offload disk work from the real async graph."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from test_research_agent_integration import call, proposal, response_message, turn_context
from test_research_data_integration import data_graph, record_call, tool_payloads
from test_research_data_integration import research_home as research_home


@pytest.fixture
def snapshot_graph(research_home):
    return data_graph([proposal(), record_call(), call("read_research_data", {"section": "sources"}, "read"), AIMessage(content="已记录")], InMemorySaver())


@pytest.mark.asyncio
async def test_record_and_read_snapshot_do_not_block(snapshot_graph):
    config = {"configurable": {"thread_id": "research-thread"}}
    messages = [HumanMessage(content="准备研究")]
    pending = await snapshot_graph.ainvoke({"messages": messages}, config, context=turn_context("prepare", messages))
    messages = [response_message(pending["research"]["session"]["pending_confirmation"]["request_id"])]
    result = await snapshot_graph.ainvoke({"messages": messages}, config, context=turn_context("confirm", messages))
    assert result["research"]["result"]["counts"]["sources"] == 1
    assert tool_payloads(result, "read_research_data")[-1]["records"][0]["title"] == "合成受控来源"
