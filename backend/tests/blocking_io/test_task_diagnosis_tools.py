"""The real async tools must keep their bundled JSON reads off the event loop."""

import pytest

from deerflow.community.task_diagnosis.tools import lookup_error_code_tool, query_task_status_tool


@pytest.mark.asyncio
async def test_diagnosis_file_reads_do_not_block_the_event_loop():
    task = await query_task_status_tool.ainvoke({"task_id": "T1001"})
    error = await lookup_error_code_tool.ainvoke({"error_code": task["error_code"]})

    assert error["cause"] == "上游请求超时"
