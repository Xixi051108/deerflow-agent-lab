"""Public-tool and DeerFlow assembly contracts for the synthetic diagnosis tools."""

import pytest
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_failed_task_returns_synthetic_evidence():
    from deerflow.community.task_diagnosis.tools import query_task_status_tool

    result = await query_task_status_tool.ainvoke({"task_id": "T1001"})

    assert result == {
        "data_source": "synthetic",
        "found": True,
        "task_id": "T1001",
        "status": "failed",
        "error_code": "E_TIMEOUT",
    }


@pytest.mark.asyncio
async def test_error_lookup_returns_explanation_and_a_suggestion_not_a_repair():
    from deerflow.community.task_diagnosis.tools import lookup_error_code_tool

    result = await lookup_error_code_tool.ainvoke({"error_code": "E_TIMEOUT"})

    assert result == {
        "data_source": "synthetic",
        "found": True,
        "error_code": "E_TIMEOUT",
        "cause": "上游请求超时",
        "suggested_action": "检查上游可用性与超时配置",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("task_id", "status", "error_code"),
    [("T1002", "failed", "E_PERMISSION"), ("T1003", "succeeded", None), ("T1004", "running", None), ("T1005", "failed", "E_UNKNOWN"), ("T1006", "failed", None)],
)
async def test_task_states_are_reported_without_inventing_error_codes(task_id, status, error_code):
    from deerflow.community.task_diagnosis.tools import query_task_status_tool

    result = await query_task_status_tool.ainvoke({"task_id": task_id})
    assert result["status"] == status
    assert result["error_code"] == error_code


@pytest.mark.asyncio
@pytest.mark.parametrize(("tool_name", "arguments", "expected"), [("query_task_status_tool", {"task_id": "T9999"}, {"task_id": "T9999"}), ("lookup_error_code_tool", {"error_code": "E_UNKNOWN"}, {"error_code": "E_UNKNOWN"})])
async def test_missing_evidence_is_explicit(tool_name, arguments, expected):
    from deerflow.community.task_diagnosis import tools

    result = await getattr(tools, tool_name).ainvoke(arguments)
    assert result == {"data_source": "synthetic", "found": False, **expected}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [("query_task_status_tool", {"task_id": "../.env"}), ("query_task_status_tool", {"task_id": "T1001", "path": "/secret"}), ("lookup_error_code_tool", {"error_code": "invalid"}), ("query_task_status_tool", {"task_id": 1001})],
)
async def test_tool_schema_rejects_invalid_or_unexpected_arguments(tool_name, arguments):
    from deerflow.community.task_diagnosis import tools

    with pytest.raises(ValidationError):
        await getattr(tools, tool_name).ainvoke(arguments)


def diagnosis_config():
    from deerflow.config.app_config import AppConfig
    from deerflow.config.sandbox_config import SandboxConfig
    from deerflow.config.tool_config import ToolConfig, ToolGroupConfig

    return AppConfig(
        models=[],
        sandbox=SandboxConfig(use="deerflow.sandbox.local:LocalSandboxProvider"),
        tool_groups=[ToolGroupConfig(name="task-diagnosis")],
        tools=[ToolConfig(name=name, group="task-diagnosis", use=f"deerflow.community.task_diagnosis.tools:{name}_tool") for name in ("query_task_status", "lookup_error_code")],
    )


def test_deerflow_loads_and_invokes_tools_from_configuration():
    from deerflow.tools import get_available_tools

    loaded = get_available_tools(app_config=diagnosis_config(), groups=["task-diagnosis"], include_mcp=False, include_upload_tool=False)
    tools = {item.name: item for item in loaded}

    assert {"query_task_status", "lookup_error_code"} <= tools.keys()
    assert tools["query_task_status"].invoke({"task_id": "T1001"})["error_code"] == "E_TIMEOUT"
    assert tools["lookup_error_code"].invoke({"error_code": "E_PERMISSION"})["cause"] == "访问权限不足"


def test_deerflow_group_filter_withholds_diagnosis_tools():
    from deerflow.tools import get_available_tools

    loaded = get_available_tools(app_config=diagnosis_config(), groups=[], include_mcp=False, include_upload_tool=False)

    assert not {"query_task_status", "lookup_error_code"} & {item.name for item in loaded}


@pytest.mark.asyncio
async def test_real_lead_agent_executes_both_tools_with_only_the_model_replaced(monkeypatch, tmp_path):
    import asyncio
    import json

    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    from deerflow.agents.lead_agent import agent as lead_module
    from deerflow.config import paths as paths_module
    from deerflow.config.app_config import AppConfig, pop_current_app_config, push_current_app_config
    from deerflow.config.memory_config import MemoryConfig
    from deerflow.config.model_config import ModelConfig
    from deerflow.config.summarization_config import SummarizationConfig

    class ToolCallingModel(FakeMessagesListChatModel):
        call_count: int = 0

        def bind_tools(self, tools, **kwargs):
            assert {"query_task_status", "lookup_error_code"} <= {item.name for item in tools}
            return self

        def _generate(self, *args, **kwargs):
            self.call_count += 1
            assert self.call_count <= 3, "the scripted tool exchange must finish after three model decisions"
            return super()._generate(*args, **kwargs)

    base = diagnosis_config()
    config = AppConfig(
        models=[ModelConfig(name="offline", use="langchain_deepseek:ChatDeepSeek", model="offline")],
        sandbox=base.sandbox,
        tools=base.tools,
        tool_groups=base.tool_groups,
        memory=MemoryConfig(enabled=False),
        summarization=SummarizationConfig(enabled=False),
    )
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr(paths_module, "_paths", paths_module.Paths(base_dir=tmp_path))
    model = ToolCallingModel(
        responses=[
            AIMessage(content="", tool_calls=[{"name": "query_task_status", "args": {"task_id": "T1001"}, "id": "query-1"}]),
            AIMessage(content="", tool_calls=[{"name": "lookup_error_code", "args": {"error_code": "E_TIMEOUT"}, "id": "lookup-1"}]),
            AIMessage(content="合成任务 T1001 失败，错误码 E_TIMEOUT，原因为上游请求超时。建议检查配置；未执行修复。"),
        ]
    )
    monkeypatch.setattr(lead_module, "create_chat_model", lambda **kwargs: model)
    push_current_app_config(config)
    try:
        assembly = await asyncio.to_thread(lead_module.assemble_lead_agent, {"configurable": {"thread_id": "diagnosis-test"}}, app_config=config)
        result = await assembly.graph.ainvoke({"messages": [HumanMessage(content="请使用两个业务查询工具诊断 T1001。")]}, {"configurable": {"thread_id": "diagnosis-test"}, "recursion_limit": config.recursion_limit})
    finally:
        pop_current_app_config()

    messages = [item for item in result["messages"] if isinstance(item, ToolMessage)]
    assert [item.name for item in messages] == ["query_task_status", "lookup_error_code"]
    assert json.loads(messages[0].content)["error_code"] == "E_TIMEOUT"
    assert json.loads(messages[1].content)["cause"] == "上游请求超时"
