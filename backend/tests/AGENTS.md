# Backend Tests

Backend tests must preserve the runtime invariants they exercise without changing production execution topology.

## Native Windows regression runs

Keep Python bytecode writes disabled with `PYTHONDONTWRITEBYTECODE=1` (including
child processes) when security software flags the SkillScan rule cache. This does
not disable antivirus or SkillScan. Use the existing backend virtual environment;
put the installed `uv` on the test process's PATH. Make dry-run tests explicitly
skip when GNU Make is absent; they must never be reported as passing.

ReadabiliPy's real extraction tests need its JavaScript dependencies as well as
Node.js. Its upstream auto-installer invokes `npm`, which does not find `npm.cmd`
on native Windows. From `backend/.venv/Lib/site-packages/readabilipy/javascript/`,
run `npm.cmd install --ignore-scripts --no-audit --no-fund` once after installing
the Python environment. Preserve the real extractor in link-resolution tests.

Exercise real long filenames and normal pytest temporary directories. Windows
filesystem paths use the extended namespace where needed; SQLite URLs retain
ordinary paths. POSIX permission bits cannot assert Windows ACLs: keep POSIX
assertions on POSIX, and retain cross-platform persistence and failure checks.
Use events to synchronize worker tests instead of assuming assembly starts within
one second. Studio restart tests use a dedicated process group and Ctrl+Break on
Windows so shutdown flushes persisted state.

## Research data verification

`support/research_samples.py` contains synthetic phone/laptop records, never live
price evidence. Data/storage tests exercise public contracts and real temporary
files; graph/HTTP tests replace only the model boundary and inject filesystem
faults. SQLite saver close/reopen covers full/delta; cancellation tests coordinate
workers with events. Windows redirect tests use a real temporary junction (POSIX
uses a directory symlink), retaining the normal pytest temporary directory.

Resolve scripted model research-ID and scope-version placeholders independently.
For a negative case, keep other inputs valid, prove which field changed, and
assert the intended error code as well as unchanged results and no file writes.
A failed-source citation case must include a valid failure reason and matching
saved text so metadata validation does not mask the relationship check.

Keep default offline shards' collection stages separate: existing
`test_skill_review_core.py` probes a fixed `CaseProbe` in the OS temp root, so
simultaneous collections can race. Wait for the first shard to start executing
tests before launching the second; do not skip the affected test or count an
interrupted collection as a successful baseline.

## Executor starvation tests

`test_executor_starvation.py` covers the deterministic starvation semantics from RFC #4560:

- default-executor saturation and queueing;
- cancellation of an awaiter while an already-started synchronous worker continues;
- isolation between the asyncio default executor and DeerFlow's dedicated file-I/O executor.

Use explicit synchronization such as `threading.Event` rather than sleep-based timing thresholds for worker lifecycle assertions. Every test must release blocked workers and restore any process-global monkeypatches so teardown cannot leak threads or state into later tests.

Stress/soak testing, AnyIO worker instrumentation, Uvicorn multi-process behavior, and broad production executor redesign are separate concerns and should not be folded into these deterministic regressions.
