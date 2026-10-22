# Browser login persistence

Per-user storage state lives in host `browser-auth/{identity-hash}`, outside sandbox/evidence. Revisions fence stale saves and clears; only an existing owned isolated browser can opt in. Save through `run_file_io` with cancellation draining. Clear revokes live sessions before disk I/O and prevents retained handles from reopening.

Keep one Gateway process per data home, request guards on rebuilt contexts and blocked service workers. Never expose storage state, login input values or raw browser exceptions to tools, APIs or logs. Login screenshots are Live-only. Remote pages remain untrusted; persistence never bypasses network restrictions or CAPTCHA.

Tests: `test_browser_login_state.py`, `test_browser_router.py`, browser lifecycle regressions and strict `blocking_io/test_browser_login_state.py`. Usage, references and limitations: root `docs/learning/agent-testing-bootcamp/BROWSER_LOGIN_STATE.md`.

Research DOM capture compares the complete requested URL inside the session before redacting query/fragment data. Preserve SKU query differences. A six-second bounded render window includes the network-idle wait; the research caller still enforces its ten-second capture deadline and rechecks login after settling. This is not a universal SPA-ready signal. Visible text capture excludes site chrome and form values, keeps inline price digits together and retains configuration navigation inside content. Reader filtering in `agents/research/collection.py` follows the same chrome policy; neither extraction proves the active SKU or offer semantics.

The opt-in panel integration uses `tests/support/browser_login_gateway.py` and `frontend/tests/support/build-browser-login-panel.mjs`: real panel, HTTP/WebSocket routes and isolated Chrome, synthetic site/auth and temporary storage only. Never mount its test endpoints in the application Gateway. The full Next.js proxy run uses the original dev script with synthetic auth; neither run validates production JWT/CSRF.

For explicit `target=_blank` clicks, await the bounded popup event and snapshot the adopted active page, including login redaction, instead of returning refs from the source tab. The popup regression is in `test_browser_login_state.py`; arbitrary delayed JavaScript popups remain asynchronous and need a fresh snapshot.

Snapshots best-effort wait up to three seconds for network idle before login screening and ref stamping. Visible ARIA/checked states and active/selected list items provide selection hints; capture preserves visible selected labels in its bounded text. These are untrusted DOM hints, not SKU verification. Never expose input values. Tests cover asynchronous popup options and configuration switching through the public snapshot/capture interfaces.
