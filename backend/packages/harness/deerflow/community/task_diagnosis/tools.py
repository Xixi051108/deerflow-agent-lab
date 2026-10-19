"""Read-only learning tools; all task records are synthetic, never Gateway runs."""

import json
from pathlib import Path

from langchain.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from deerflow.utils.file_io import run_file_io


class TaskStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str = Field(strict=True, pattern=r"^T[0-9]{4}$", description="Synthetic business task ID, for example T1001")


class ErrorCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error_code: str = Field(strict=True, pattern=r"^E_[A-Z_]{1,40}$", description="Error code returned by query_task_status")


@tool("query_task_status", args_schema=TaskStatusInput)
async def query_task_status_tool(task_id: str) -> dict:
    """Query a synthetic business task's status and error code (not a DeerFlow run).

    All records are demo data. For failed tasks with an error code, call
    lookup_error_code next. Missing tasks or error codes provide insufficient
    evidence for a diagnosis. This read-only tool never repairs or restarts tasks.
    """
    text = await run_file_io((Path(__file__).parent / "tasks.json").read_text, encoding="utf-8")
    record = json.loads(text).get(task_id)
    result = {"data_source": "synthetic", "found": record is not None, "task_id": task_id}
    if record is not None:
        result.update(record)
    return result


@tool("lookup_error_code", args_schema=ErrorCodeInput)
async def lookup_error_code_tool(error_code: str) -> dict:
    """Look up a synthetic task error's meaning and suggested investigation.

    Use an error code returned by query_task_status. A missing record means
    insufficient evidence; never invent a cause. Suggestions are not actions
    already performed: this read-only tool cannot fix, restart, or modify tasks.
    """
    text = await run_file_io((Path(__file__).parent / "errors.json").read_text, encoding="utf-8")
    record = json.loads(text).get(error_code)
    result = {"data_source": "synthetic", "found": record is not None, "error_code": error_code}
    if record is not None:
        result.update(record)
    return result
