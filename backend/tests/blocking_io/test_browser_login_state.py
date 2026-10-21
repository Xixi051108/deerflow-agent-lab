"""Login persistence must stay off the Gateway/private event loops."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_browser_login_state import _InlineLoop

from deerflow.community.browser_automation.login_state import load_login_state
from deerflow.community.browser_automation.session import BrowserSessionManager
from deerflow.runtime.user_context import get_effective_user_id
from deerflow.utils.file_io import run_file_io


@pytest.mark.asyncio
async def test_remember_and_forget_offload_private_state_io(tmp_path, monkeypatch):
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    manager = BrowserSessionManager()
    monkeypatch.setattr(manager, "_ensure_loop", lambda: _InlineLoop())
    session = manager.get_session("synthetic-thread")
    session._context = SimpleNamespace(storage_state=AsyncMock(return_value={"cookies": [], "origins": []}), close=AsyncMock())
    await session.remember_login()
    assert (await run_file_io(load_login_state, get_effective_user_id()))[1] == {"cookies": [], "origins": []}
    await manager.forget_logins(get_effective_user_id())
    assert (await run_file_io(load_login_state, get_effective_user_id()))[1] is None
    assert session.is_closed
