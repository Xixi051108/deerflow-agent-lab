# Browser login persistence

Per-user storage state lives in host `browser-auth/{identity-hash}`, outside sandbox/evidence. Revisions fence stale saves and clears; only an existing owned isolated browser can opt in. Save through `run_file_io` with cancellation draining. Clear revokes live sessions before disk I/O and prevents retained handles from reopening.

Keep one Gateway process per data home, request guards on rebuilt contexts and blocked service workers. Never expose storage state, login input values or raw browser exceptions to tools, APIs or logs. Login screenshots are Live-only. Remote pages remain untrusted; persistence never bypasses network restrictions or CAPTCHA.

Tests: `test_browser_login_state.py`, `test_browser_router.py`, browser lifecycle regressions and strict `blocking_io/test_browser_login_state.py`. Usage, references and limitations: root `docs/learning/agent-testing-bootcamp/BROWSER_LOGIN_STATE.md`.
