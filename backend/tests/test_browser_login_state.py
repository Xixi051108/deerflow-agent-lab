"""User-owned browser state remains outside research and sandbox artifacts."""

import pytest


class _InlineLoop:
    async def run(self, coro):
        return await coro

    def submit(self, coro):
        import asyncio
        from concurrent.futures import Future

        result = Future()
        task = asyncio.create_task(coro)

        def done(future):
            try:
                result.set_result(future.result())
            except BaseException as exc:
                result.set_exception(exc)

        task.add_done_callback(done)
        return result


@pytest.mark.asyncio
@pytest.mark.parametrize("login_page", [False, True])
async def test_click_snapshots_the_new_active_popup_instead_of_old_page(login_home, login_page):
    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    destination = "https://example.com/login?code=synthetic-callback" if login_page else "https://example.com/buy"
    try:
        page = await session._ensure_page()

        async def respond(route):
            if route.request.url == "https://example.com/start":
                html = f'<title>Product overview</title><a target="_blank" href="{destination}">Buy</a>'
            else:
                html = "<title>Purchase options</title><button>12GB+512GB</button>"
                if login_page:
                    html = '<title>Private login</title><input type="password"><button>Private login action</button>'
            await route.fulfill(content_type="text/html; charset=utf-8", body=html)

        await page.route("https://example.com/**", respond)
        # A popup's initial request must be routed at context level.
        await session._context.route("https://example.com/**", respond)
        before = await session.navigate("https://example.com/start")
        clicked = await session.click(next(element.ref for element in before.elements if element.name == "Buy"))
        assert clicked.url == destination.split("?", 1)[0]
        if login_page:
            assert "Sign in using Browser Live" in clicked.title and not clicked.elements
            assert "synthetic-callback" not in str(clicked)
        else:
            assert clicked.title == "Purchase options"
            option = next(element for element in clicked.elements if element.name == "12GB+512GB")
            assert (await session.click(option.ref)).title == "Purchase options"
    finally:
        await session.close()


@pytest.fixture
def login_home(tmp_path, monkeypatch):
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    return tmp_path


@pytest.mark.asyncio
async def test_snapshot_waits_for_inflight_purchase_options_after_popup(login_home):
    import asyncio

    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session._ensure_page()

        async def respond(route):
            if route.request.url.endswith("/options"):
                await asyncio.sleep(0.4)
                await route.fulfill(content_type="application/json", body='["12GB+512GB"]')
            elif route.request.url.endswith("/start"):
                await route.fulfill(content_type="text/html", body='<a target="_blank" href="https://example.com/buy">Buy</a>')
            else:
                await route.fulfill(
                    content_type="text/html",
                    body="<title>Purchase</title><main>Loading</main><script>fetch('/options').then(r=>r.json()).then(options=>document.querySelector('main').innerHTML='<button>'+options[0]+'</button>')</script>",
                )

        await session._context.route("https://example.com/**", respond)
        before = await session.navigate("https://example.com/start")
        clicked = await session.click(next(element.ref for element in before.elements if element.name == "Buy"))
        assert any(element.name == "12GB+512GB" for element in clicked.elements)
    finally:
        await session.close()


def test_expired_state_is_removed_and_old_writers_are_fenced(login_home, monkeypatch):
    from deerflow.community.browser_automation import login_state

    monkeypatch.setattr(login_state.time, "time", lambda: 1000)
    state = {"cookies": [], "origins": [{"origin": "https://example.com", "localStorage": [{"name": "session", "value": "synthetic"}]}]}
    old = login_state.save_login_state("alice", state, expected_revision=None)
    monkeypatch.setattr(login_state.time, "time", lambda: 1000 + 31 * 24 * 3600)
    revision, value = login_state.load_login_state("alice")
    assert value is None and revision != old
    with pytest.raises(login_state.BrowserLoginConflict):
        login_state.save_login_state("alice", state, expected_revision=old)


def test_users_with_case_distinct_ids_do_not_share_state(login_home):
    from deerflow.community.browser_automation.login_state import load_login_state, save_login_state

    save_login_state("Alice", {"cookies": [], "origins": []}, expected_revision=None)
    assert load_login_state("alice") == (None, None)


@pytest.mark.asyncio
async def test_clear_closes_owned_sessions_and_prevents_retained_browser_reopening(login_home, monkeypatch):
    from deerflow.community.browser_automation.login_state import load_login_state
    from deerflow.community.browser_automation.session import BrowserSessionManager
    from deerflow.runtime.user_context import get_effective_user_id

    manager = BrowserSessionManager()
    monkeypatch.setattr(manager, "_ensure_loop", lambda: _InlineLoop())
    session = manager.get_session("old-thread")
    await session.navigate("about:blank")
    await session.remember_login()
    await manager.forget_logins(get_effective_user_id())
    assert load_login_state(get_effective_user_id())[1] is None
    with pytest.raises(RuntimeError, match="closed"):
        await session.navigate("about:blank")
    with pytest.raises(RuntimeError):
        await session.remember_login()
    assert manager.get_session("new-thread") is not session


def test_concurrent_saves_have_one_winner_and_clear_remains_final(login_home):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from deerflow.community.browser_automation.login_state import BrowserLoginConflict, clear_login_state, load_login_state, save_login_state

    barrier = Barrier(2)

    def save(value):
        barrier.wait(timeout=5)
        try:
            return save_login_state("alice", {"cookies": [], "origins": []}, expected_revision=None)
        except BrowserLoginConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, (1, 2)))
    assert sum(result is not None for result in results) == 1
    clear_login_state("alice")
    assert load_login_state("alice")[1] is None
    for revision in results:
        with pytest.raises(BrowserLoginConflict):
            save_login_state("alice", {"cookies": [], "origins": []}, expected_revision=revision)


@pytest.mark.asyncio
async def test_login_snapshot_does_not_expose_input_values_or_callback_credentials(login_home):
    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session.navigate("about:blank")
        await session._context.route("https://login.example/**", lambda route: route.fulfill(content_type="text/html", body="<input type='password' value='synthetic-password'><input value='synthetic-otp'>"))
        snapshot = await session.navigate("https://login.example/login?code=synthetic-callback#synthetic-token")
        assert not any(secret in snapshot.render() for secret in ("synthetic-password", "synthetic-otp", "synthetic-callback", "synthetic-token"))
        assert await session.login_status() == {"remembered": False, "notice": "login_required"}
        with pytest.raises(RuntimeError, match="login"):
            await session.capture_page()
    finally:
        await session._close()


@pytest.mark.asyncio
async def test_rebuilt_browser_context_keeps_request_guard(login_home):
    from deerflow.community.browser_automation.session import BrowserSession

    checked = []

    def guard(url):
        checked.append(url)
        return "blocked"

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=2000, viewport={"width": 800, "height": 600}, url_guard=guard)
    try:
        await session.navigate("about:blank")
        await session._page.close()
        await session.navigate("about:blank")
        with pytest.raises(Exception):
            await session.navigate("https://blocked.example/")
        assert checked == ["https://blocked.example/"]
    finally:
        await session._close()


@pytest.mark.asyncio
async def test_real_browser_refreshes_saved_login_and_restores_in_new_session(login_home):
    from deerflow.community.browser_automation.login_state import load_login_state
    from deerflow.community.browser_automation.session import BrowserSession

    pytest.importorskip("playwright.async_api")

    def create(user_id="alice"):
        return BrowserSession(_InlineLoop(), user_id=user_id, headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})

    first, second, other = create(), create(), create("bob")

    async def synthetic_page(session):
        await session.navigate("about:blank")
        await session._context.route("https://login.example/**", lambda route: route.fulfill(content_type="text/html", body="<h1>Synthetic shop</h1>"))
        await session.navigate("https://login.example/")

    try:
        await synthetic_page(first)
        await first._context.add_cookies([{"name": "session", "value": "synthetic-v1", "url": "https://login.example/"}])
        await first._page.evaluate("localStorage.setItem('session', 'synthetic-local')")
        await first._page.evaluate("""async () => {
            const db = await new Promise((resolve, reject) => {
                const request = indexedDB.open('synthetic-auth', 1);
                request.onupgradeneeded = () => request.result.createObjectStore('tokens');
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            await new Promise((resolve, reject) => {
                const transaction = db.transaction('tokens', 'readwrite');
                transaction.objectStore('tokens').put('synthetic-indexeddb', 'session');
                transaction.oncomplete = resolve; transaction.onerror = reject;
            });
            db.close();
        }""")
        await first.remember_login()
        await first._context.add_cookies([{"name": "session", "value": "synthetic-v2", "url": "https://login.example/"}])
        # A normal browser operation checkpoints refreshed state, without another Remember.
        await first.snapshot()
        assert load_login_state("alice")[1]["cookies"][0]["value"] == "synthetic-v2"
        await first._close()
        await synthetic_page(second)
        assert (await second._context.cookies())[0]["value"] == "synthetic-v2"
        assert await second._page.evaluate("localStorage.getItem('session')") == "synthetic-local"
        assert (
            await second._page.evaluate("""async () => {
            const db = await new Promise(resolve => {
                const request = indexedDB.open('synthetic-auth', 1);
                request.onsuccess = () => resolve(request.result);
            });
            return await new Promise(resolve => {
                const request = db.transaction('tokens').objectStore('tokens').get('session');
                request.onsuccess = () => { db.close(); resolve(request.result); };
            });
        }""")
            == "synthetic-indexeddb"
        )
        await synthetic_page(other)
        assert await other._context.cookies() == []
        assert await other._page.evaluate("localStorage.getItem('session')") is None
        assert load_login_state("bob") == (None, None)
    finally:
        await first._close()
        await second._close()
        await other._close()


@pytest.mark.asyncio
async def test_corrupt_storage_opens_clean_browser_and_can_be_cleared(login_home):
    from deerflow.community.browser_automation.login_state import clear_login_state, save_login_state
    from deerflow.community.browser_automation.session import BrowserSession

    save_login_state("alice", {"cookies": [], "origins": []}, expected_revision=None)
    next(login_home.rglob("state.json")).write_text("{invalid synthetic state", encoding="utf-8")
    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session.navigate("about:blank")
        assert await session._context.cookies() == []
        assert await session.login_status() == {"remembered": False, "notice": "storage_unavailable"}
        clear_login_state("alice")
    finally:
        await session._close()


def test_saved_login_survives_a_new_python_process(login_home):
    import os
    import subprocess
    import sys

    from deerflow.community.browser_automation.login_state import save_login_state

    state = {"cookies": [{"name": "session", "value": "synthetic-restart", "domain": "example.com", "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"}], "origins": []}
    save_login_state("alice", state, expected_revision=None)
    script = """
import asyncio
from deerflow.community.browser_automation.session import BrowserSession
class Loop:
    async def run(self, coro): return await coro
async def verify():
    session = BrowserSession(Loop(), user_id='alice', headless=True, timeout_ms=5000, viewport={'width': 800, 'height': 600})
    try:
        await session.navigate('about:blank')
        cookies = await session._context.cookies()
        assert cookies[0]['value'] == 'synthetic-restart'
    finally:
        await session._close()
asyncio.run(verify())
print('restored')
"""
    result = subprocess.run([sys.executable, "-B", "-c", script], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "restored"


@pytest.mark.asyncio
async def test_periodic_updates_and_close_save_refreshed_state(login_home, monkeypatch):
    import asyncio

    from deerflow.community.browser_automation import session as module
    from deerflow.community.browser_automation.login_state import load_login_state

    monkeypatch.setattr(module, "_LOGIN_SAVE_INTERVAL_S", 0.01)
    saved = asyncio.Event()
    loop = asyncio.get_running_loop()
    real_save = module.save_login_state

    def observe_save(user_id, state, **kwargs):
        revision = real_save(user_id, state, **kwargs)
        if state["cookies"] and state["cookies"][0]["value"] == "synthetic-refreshed":
            loop.call_soon_threadsafe(saved.set)
        return revision

    monkeypatch.setattr(module, "save_login_state", observe_save)
    session = module.BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session.navigate("about:blank")
        await session.remember_login()
        await session._context.add_cookies([{"name": "session", "value": "synthetic-refreshed", "url": "https://example.com/"}])
        await asyncio.wait_for(saved.wait(), 5)
        assert load_login_state("alice")[1]["cookies"][0]["value"] == "synthetic-refreshed"
        await session._context.add_cookies([{"name": "session", "value": "synthetic-at-close", "url": "https://example.com/"}])
    finally:
        await session._close()
    assert load_login_state("alice")[1]["cookies"][0]["value"] == "synthetic-at-close"


@pytest.mark.asyncio
async def test_cancelled_clear_drains_disk_and_blocks_new_sessions(login_home, monkeypatch):
    import asyncio
    import threading

    from deerflow.community.browser_automation import session as module
    from deerflow.community.browser_automation.login_state import load_login_state
    from deerflow.runtime.user_context import get_effective_user_id
    from deerflow.utils.file_io import run_file_io

    entered, release = threading.Event(), threading.Event()
    original = module.clear_login_state

    def delayed_clear(user_id):
        entered.set()
        assert release.wait(5)
        original(user_id)

    monkeypatch.setattr(module, "clear_login_state", delayed_clear)
    manager = module.BrowserSessionManager()
    monkeypatch.setattr(manager, "_ensure_loop", lambda: _InlineLoop())
    old = manager.get_session("old")
    task = asyncio.create_task(manager.forget_logins(get_effective_user_id()))
    try:
        assert await run_file_io(entered.wait, 5)
        with pytest.raises(RuntimeError, match="cleared"):
            manager.get_session("new")
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert old.is_closed
        assert load_login_state(get_effective_user_id())[1] is None
        assert manager.get_session("new") is not old
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


def test_expired_cookies_are_not_restored(login_home, monkeypatch):
    from deerflow.community.browser_automation import login_state

    monkeypatch.setattr(login_state.time, "time", lambda: 1000)
    state = {"cookies": [{"name": "session", "value": "synthetic-expiring", "domain": "example.com", "path": "/", "expires": 1010, "httpOnly": True, "secure": True, "sameSite": "Lax"}], "origins": []}
    revision = login_state.save_login_state("alice", state, expected_revision=None)
    monkeypatch.setattr(login_state.time, "time", lambda: 1011)
    assert login_state.load_login_state("alice")[1] is None
    with pytest.raises(login_state.BrowserLoginConflict):
        login_state.save_login_state("alice", state, expected_revision=revision)


def test_clear_waits_for_inflight_save_and_removes_its_credentials(login_home, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from deerflow.community.browser_automation import login_state

    entered, release, clear_started = threading.Event(), threading.Event(), threading.Event()
    write = login_state._write

    def delayed_write(user_id, state):
        if state is not None:
            entered.set()
            assert release.wait(5)
        return write(user_id, state)

    def clear():
        clear_started.set()
        login_state.clear_login_state("alice")

    monkeypatch.setattr(login_state, "_write", delayed_write)
    with ThreadPoolExecutor(max_workers=2) as pool:
        saving = pool.submit(login_state.save_login_state, "alice", {"cookies": [], "origins": []}, expected_revision=None)
        try:
            assert entered.wait(5)
            clearing = pool.submit(clear)
            assert clear_started.wait(5)
        finally:
            release.set()
        revision = saving.result(timeout=5)
        clearing.result(timeout=5)
    assert login_state.load_login_state("alice")[1] is None
    with pytest.raises(login_state.BrowserLoginConflict):
        login_state.save_login_state("alice", {"cookies": [], "origins": []}, expected_revision=revision)


@pytest.mark.asyncio
async def test_popup_close_returns_to_original_page_without_losing_storage(login_home):
    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session.navigate("about:blank")
        original_context, original_page = session._context, session._page
        popup = await original_context.new_page()
        await popup.close()
        assert await session.current_url() == "about:blank"
        assert session._context is original_context
        assert session._page is original_page
    finally:
        await session._close()


@pytest.mark.asyncio
async def test_closing_login_view_drains_scheduled_live_frames(login_home):
    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    try:
        await session.start_screencast(lambda data: None)
        pending = tuple(session._background_tasks)
        assert pending
        await session._close()
        assert all(task.done() for task in pending)
    finally:
        await session._close()


def test_oversized_save_preserves_previous_state(login_home):
    from deerflow.community.browser_automation.login_state import MAX_LOGIN_BYTES, load_login_state, save_login_state

    state = {"cookies": [], "origins": []}
    revision = save_login_state("alice", state, expected_revision=None)
    with pytest.raises(ValueError, match="size limit"):
        save_login_state("alice", {"cookies": [], "origins": [{"origin": "https://example.com", "localStorage": [{"name": "synthetic", "value": "x" * MAX_LOGIN_BYTES}]}]}, expected_revision=revision)
    assert load_login_state("alice") == (revision, state)


@pytest.mark.asyncio
async def test_background_browser_errors_do_not_log_credential_details(caplog):
    import logging
    from unittest.mock import AsyncMock

    from deerflow.community.browser_automation.session import BrowserSession

    session = BrowserSession(_InlineLoop(), user_id="alice", headless=True, timeout_ms=5000, viewport={"width": 800, "height": 600})
    session._rebind_screencast = AsyncMock(side_effect=RuntimeError("synthetic-secret-token"))
    with caplog.at_level(logging.DEBUG):
        await session._rebind_screencast_safe()
    assert "synthetic-secret-token" not in caplog.text
    assert "RuntimeError" in caplog.text


def test_saved_browser_login_is_reusable_only_by_its_owner_and_clear_fences_old_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    from deerflow.community.browser_automation.login_state import BrowserLoginConflict, clear_login_state, load_login_state, save_login_state

    state = {"cookies": [{"name": "session", "value": "test-session-token", "domain": "example.com", "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"}], "origins": []}
    assert load_login_state("alice") == (None, None)
    revision = save_login_state("alice", state, expected_revision=None)
    assert load_login_state("alice") == (revision, state)
    assert load_login_state("bob") == (None, None)
    clear_login_state("alice")
    cleared_revision, cleared_state = load_login_state("alice")
    assert cleared_revision != revision and cleared_state is None
    with pytest.raises(BrowserLoginConflict):
        save_login_state("alice", state, expected_revision=revision)
    assert load_login_state("alice") == (cleared_revision, None)
    assert not list(tmp_path.rglob("*/user-data/*"))


@pytest.mark.asyncio
async def test_browser_manager_rejects_another_users_retained_thread():
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    from deerflow.community.browser_automation.session import BrowserSessionManager
    from deerflow.runtime.user_context import reset_current_user, set_current_user

    manager = BrowserSessionManager()
    with patch.object(manager, "_ensure_loop", return_value=MagicMock()):
        alice_token = set_current_user(SimpleNamespace(id="alice"))
        try:
            alice = manager.get_session("same-key")
        finally:
            reset_current_user(alice_token)
        bob_token = set_current_user(SimpleNamespace(id="bob"))
        try:
            with pytest.raises(PermissionError):
                manager.get_session("same-key")
            assert alice.user_id == "alice"
        finally:
            reset_current_user(bob_token)
