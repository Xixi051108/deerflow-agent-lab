"""Opt-in synthetic site for the real Browser panel; never mount in Gateway."""

import argparse
import os
import tempfile
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import Request

from app.gateway.auth.models import User
from app.gateway.routers import browser
from deerflow.community.browser_automation import session as sessions
from deerflow.community.browser_automation import tools as browser_tools
from deerflow.runtime.user_context import reset_current_user, set_current_user

SITE = "https://example.com/phase5/"
THREADS = {f"00000000-0000-0000-0000-{index:012d}" for index in (1, 2)}
USER = User(id=UUID("00000000-0000-0000-0000-0000000000ab"), email="synthetic@example.com", password_hash="unused", system_role="user")
LOGIN = """<!doctype html><title>Synthetic login</title>
<style>body{font:20px sans-serif}input,button{display:block;margin:20px;width:260px;height:32px}</style>
<h1>Synthetic login</h1><form><input aria-label="Name"><input type="password" aria-label="Password">
<button>Sign in (synthetic)</button></form><script>
document.querySelector('form').onsubmit = async event => {
  event.preventDefault();
  document.cookie = 'phase5=synthetic-session; path=/; secure; SameSite=Lax';
  localStorage.setItem('phase5', 'synthetic-local');
  await new Promise(resolve => {
    const request = indexedDB.open('phase5', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('auth');
    request.onsuccess = () => {
      const transaction = request.result.transaction('auth', 'readwrite');
      transaction.objectStore('auth').put('synthetic-indexed', 'session');
      transaction.oncomplete = () => { request.result.close(); resolve(); };
    };
  });
  location.href = '/phase5/shop?product_id=synthetic';
};</script>"""
SHOP = """<!doctype html><title>Synthetic shop</title><h1>Signed in synthetic shop</h1>
<p>极光 A1 12GB+256GB 商品标价3299元，登录优惠资格仍须单独核对。</p>
<div id="state"></div><script>
const request = indexedDB.open('phase5', 1);
request.onsuccess = () => {
  const read = request.result.transaction('auth').objectStore('auth').get('session');
  read.onsuccess = () => {
    document.querySelector('#state').textContent =
      document.cookie.includes('phase5=synthetic-session') &&
      localStorage.getItem('phase5') === 'synthetic-local' && read.result === 'synthetic-indexed'
      ? 'Cookie + localStorage + IndexedDB restored' : 'State missing';
    request.result.close();
  };
};</script>"""


def make_app():
    # Same auth shape as router tests; this process has no real user database.
    from _router_auth_helpers import make_authed_test_app

    manager = sessions.BrowserSessionManager()
    tool = SimpleNamespace(name="browser_navigate", model_extra={})
    config = SimpleNamespace(tools=[tool], get_tool_config=lambda name: tool if name == "browser_navigate" else None)
    install_guard = sessions.BrowserSession._install_request_guard

    async def install_site(session):
        await install_guard(session)

        async def respond(route):
            if browser_tools.validate_browser_url(route.request.url) is not None:
                await route.abort()
                return
            signed_in = "phase5=synthetic-session" in (route.request.headers.get("cookie") or "")
            await route.fulfill(content_type="text/html; charset=utf-8", body=SHOP if signed_in else LOGIN)

        await session._context.route(SITE + "**", respond)

    @asynccontextmanager
    async def lifespan(app):
        with (
            patch("deerflow.config.get_app_config", return_value=config),
            patch.object(browser_tools, "get_app_config", return_value=config),
            patch.object(browser, "_authenticate_ws", AsyncMock(return_value=USER)),
            patch.object(sessions, "_manager", manager),
            patch.object(sessions.BrowserSession, "_install_request_guard", install_site),
        ):
            try:
                yield
            finally:
                await manager.close_all_sessions()

    app = make_authed_test_app(user_factory=lambda: USER)
    app.router.lifespan_context = lifespan
    app.include_router(browser.router)

    async def get_thread(thread_id, **kwargs):
        return {"thread_id": thread_id, "user_id": str(USER.id)} if thread_id in THREADS else None

    app.state.thread_store.get = get_thread

    @app.middleware("http")
    async def user_context(request: Request, call_next):
        token = set_current_user(USER)
        try:
            return await call_next(request)
        finally:
            reset_current_user(token)

    @app.get("/health")
    async def health():
        return {"synthetic": True}

    @app.get("/api/phase5-test/page/{thread_id}")
    async def page_state(thread_id: str):
        session = manager.existing_session(thread_id)
        return {"text": await session.get_text() if session else "closed"}

    if directory := os.environ.get("BROWSER_LOGIN_PANEL_DIST"):
        from pathlib import Path

        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        @app.get("/workspace/chats/{thread_id}")
        async def panel(thread_id: str):
            return FileResponse(Path(directory) / "index.html")

        app.mount("/static", StaticFiles(directory=Path(directory) / "static"))

    return app


if __name__ == "__main__":
    import sys
    from pathlib import Path

    import uvicorn

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8105)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="phase5-browser-") as home:
        os.environ["DEER_FLOW_HOME"] = home
        uvicorn.run(make_app(), host="127.0.0.1", port=args.port, log_level="info")
