"""Private per-user browser storage, never a model-visible research artifact."""

import hashlib
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from uuid import uuid4

from deerflow.config.paths import get_paths

MAX_LOGIN_BYTES = 1024 * 1024
MAX_LOGIN_AGE_SECONDS = 30 * 24 * 3600
_lock = threading.RLock()


class BrowserLoginConflict(RuntimeError):
    """A newer save/clear invalidated the browser's loaded state."""


def _path(user_id: str) -> Path:
    root = get_paths().user_dir(user_id)
    # Case-sensitive identities must remain distinct even on Windows filesystems.
    directory = root / "browser-auth" / hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    if directory.resolve() != directory or (directory / "state.json").resolve() != directory / "state.json":
        raise ValueError("Browser login storage cannot follow redirected paths")
    return directory / "state.json"


def load_login_state(user_id: str) -> tuple[str | None, dict | None]:
    with _lock:
        target = _path(user_id)
        if not target.exists():
            return None, None
        if target.stat().st_size > MAX_LOGIN_BYTES:
            raise ValueError("Browser login storage exceeds its size limit")
        value = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("revision"), str) or "state" not in value or (value["state"] is not None and not isinstance(value["state"], dict)):
            raise ValueError("Invalid browser login storage")
        if value["state"] is not None:
            saved_at = value.get("saved_at")
            if not isinstance(saved_at, (int, float)) or time.time() - saved_at >= MAX_LOGIN_AGE_SECONDS:
                return _write(user_id, None), None
            state = value["state"]
            cookies = state.get("cookies", [])
            live_cookies = [cookie for cookie in cookies if cookie.get("expires", -1) == -1 or cookie.get("expires", 0) > time.time()]
            if cookies and not live_cookies and not state.get("origins"):
                return _write(user_id, None), None
            state = {**state, "cookies": live_cookies}
            return value["revision"], state
        return value["revision"], value["state"]


def _write(user_id: str, state: dict | None) -> str:
    revision = uuid4().hex
    payload = json.dumps({"revision": revision, "saved_at": time.time(), "state": state}, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(payload) > MAX_LOGIN_BYTES:
        raise ValueError("Browser login storage exceeds its size limit")
    target = _path(user_id)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, name = tempfile.mkstemp(prefix=".state-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    return revision


def save_login_state(user_id: str, state: dict, *, expected_revision: str | None) -> str:
    if not isinstance(state, dict) or set(state) != {"cookies", "origins"} or not all(isinstance(state[key], list) for key in ("cookies", "origins")):
        raise ValueError("Invalid browser login state")
    with _lock:
        revision, _ = load_login_state(user_id)
        if revision != expected_revision:
            raise BrowserLoginConflict("Browser login state changed; reopen the browser before saving")
        return _write(user_id, state)


def clear_login_state(user_id: str) -> None:
    with _lock:
        # Keep a new revision tombstone so an older live tab cannot restore it.
        _write(user_id, None)
