"""Research graph transitions must not add blocking I/O to the agent loop."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from test_research_agent_integration import call, graph, proposal, response_message, turn_context


@pytest.fixture
def research_graph():
    invocations = []
    return graph([proposal(), call("web_search"), AIMessage(content="已读取受控资料")], invocations, InMemorySaver()), invocations


@pytest.mark.asyncio
async def test_research_cards_confirmation_and_guard_do_not_block(research_graph):
    agent, invocations = research_graph
    config = {"configurable": {"thread_id": "research-thread"}, "recursion_limit": 30}
    messages = [HumanMessage(content="准备手机范围")]
    pending = await agent.ainvoke({"messages": messages}, config, context=turn_context("prepare", messages))
    request_id = pending["research"]["session"]["pending_confirmation"]["request_id"]
    messages = [response_message(request_id)]
    confirmed = await agent.ainvoke({"messages": messages}, config, context=turn_context("confirm", messages))
    assert confirmed["research"]["session"]["confirmation"] is not None
    assert invocations == ["手机"]
