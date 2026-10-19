# Backend runtime invariants and benchmark rules

Detailed development guidance linked from [backend/AGENTS.md](../AGENTS.md).
Read the relevant section before changing these mechanisms. Commands below run
from `backend/`.

## Runtime invariants

- Gateway streams `write_file` and `str_replace` argument deltas in bounded batches for multi-mode `messages-tuple` consumers; single-mode message consumers retain the original per-chunk contract. Non-message frames flush pending batches, and `values` remains an optional complete-state snapshot rather than a prerequisite for batching.
- With `stream_subgraphs`, subgraph frames keep their namespace in the SSE event name (`values|<ns>`, LangGraph Platform style) instead of impersonating root frames — a delegated subagent inherits the parent checkpoint namespace, so publishing its `values` snapshot as bare `values` replaces the whole thread view in SDK clients (#4399). Root-only consumers (file-tool chunk batcher, subagent event persistence, LLM error-fallback detection) ignore namespaced frames. The web frontend does not request subgraph streaming; subtask progress rides root-namespace `task_*` custom events.
- Background subagent identity is deliberately split: the provider `tool_call_id` remains the correlation key for `ToolMessage`, `task_*` SSE events, persisted lifecycle events, frontend cards, and the public `ExtensionData.scope_id` contract (stored as `SubagentResult.external_task_id`), while `SubagentExecutor.execute_async()` generates a full server-side `execution_id` for `SubagentResult.task_id`, the process-wide registry, polling, cancellation, timeout handling, and cleanup. Provider IDs are not globally unique across parent runs, so they must never become registry ownership keys; scheduler closures retain their own `SubagentResult` rather than resolving ownership again through the mutable registry. Terminal subagent token usage travels in the current run's `ToolMessage.additional_kwargs` and is attributed from message state, never through a process-global provider-ID cache.
- Scheduled tasks dispatch through the normal Gateway run path. `launch_scheduled_thread_run` reads `get_app_config()` at dispatch and passes `scheduler.recursion_limit` (default 1000, matching the web UI; clamped by `max_recursion_limit`), so YAML changes apply on the next run without restarting Gateway.
- Run-history `status` filters are occurrence states, not task states. `ScheduledTaskRunStatus` in `persistence/scheduled_tasks/model.py` is the shared API/repository vocabulary and must match the active and terminal occurrence-status sets. Keep owner lookup before reading history, and apply SQL task/status predicates before pagination; omitted status preserves the existing response.
- The background scheduler is single-instance by default. `scheduler.multi_instance=true` opts into lease-aware recovery across Gateway instances and requires shared Postgres, `run_ownership.heartbeat_enabled=true`, and `run_events.backend=db`; otherwise startup rejects the configuration. Live scheduled runs are preserved when a peer starts; expired launch claims return to the durable queue, expired run leases are atomically taken over, stale launch writes are fenced by lease ownership, and the Postgres advisory-locked budget makes `max_concurrent_runs` a shared global cap for `launching`/`running` rows.
- Long-running MCP work uses a separate durable task runtime (`McpTaskService` + `mcp_tasks`, lease-based recovery) rather than keeping remote task IDs or status polling inside the Agent loop; only submit remains Agent-visible, the database is the source of truth, and `ThreadState` receives only a bounded current-thread projection. Full contract (leases, cancellation fencing, delivery idempotency, management-tool exposure): [packages/harness/deerflow/mcp/AGENTS.md](../packages/harness/deerflow/mcp/AGENTS.md).
- MCP task notification retries, dead-lettering, and the cancel endpoint's worker-stopped 503 are part of that same contract — see [packages/harness/deerflow/mcp/AGENTS.md](../packages/harness/deerflow/mcp/AGENTS.md).
- Scheduled-task dispatch permits one active occurrence per task via `uq_scheduled_task_run_active` (`task_id WHERE status IN ('queued','launching','running')`). Durable `queued` rows survive restarts; only lease-fenced `launching` may call Gateway launch; `running` references the durable run. Stable admission idempotency keys reuse that run after recovery. Reused-thread `ConflictError` returns `launching` to `queued`; other launch errors become `failed`. Atomic queue claims enforce `max_concurrent_runs`, excluding waiting rows; the budget count and its UPDATE are separate statements, so writers must serialize before the count (Postgres advisory lock; SQLite `BEGIN IMMEDIATE`, whose deferred transaction otherwise reserves the writer only at the UPDATE) or claims on distinct rows overshoot the cap. Repeated triggers coalesce; same-thread FIFO blocks behind older active rows. Queue admission, PATCH/resume, pause and delete lock the parent before the occurrence, freezing active task definitions. Pause/delete atomically cancel `queued` work but reject `launching`/`running`; PATCH/resume reject all active states. Only queued conflicts offer pause cancellation. Manual triggers may queue/run while paused. Recovery locks task/run pairs in task-id/run-id order and restores `run_id`, `started_at` and live errors before releasing launch claims. Launch/failure/timeout updates use one parent-first transaction to prevent interleaved claims. Queue timeout fails the occurrence and advances scheduled work to prevent immediate requeue. Repository boundaries coerce serialized timestamps before SQL `DateTime` binding.
- `POST /api/scheduled-tasks/preview-cron` requires authenticated `threads:read`. Bounded cron previews call the shared scheduler calculator in `asyncio.to_thread`, preserving its DST semantics. Capture the optional aware reference once; return UTC and offset-bearing local occurrences without acquiring task/thread/run stores or dispatching work. This advisory API does not reserve execution.
- `extensions_config.json` is written at runtime by the Gateway (`PUT`/`PATCH /api/mcp/config`, the MCP enable switch, skill updates), so the production compose mounts it read-write while `config.yaml` stays `:ro`; Helm copies its ConfigMap seed into a writable home-volume directory before Gateway starts. Every read-modify-write holds both `extensions_config_write_lock` and the sidecar advisory `extensions_config_file_lock`, because the process-local lock alone loses updates across workers. Docker mounts the compose file as its own mount point, and Linux refuses `rename()` over a mount point with `EBUSY` even when the mount is writable — so `atomic_write_extensions_config` keeps the temp-file-plus-rename path and falls back to an in-place overwrite only on `EBUSY`. That fallback is deliberately non-atomic (a crash mid-write truncates the file); it exists because the alternative is a write that can never succeed, and only its first occurrence per target is logged at warning level. Any other `errno` still propagates. Pinned by `tests/test_compose_extensions_config_writable.py`, `tests/test_extensions_config_atomic_write.py`, and `tests/test_helm_extensions_config_writable.py`.

## Backend benchmarks

`scripts/benchmark/context_snapshot/`: explicit `run-live` needs provider env
vars; `summarize` and pytest are offline. See its README for the protocol.

Benchmarks in `scripts/benchmark/` must be standalone and reproducible. Import
production functions; never duplicate them or introduce an alternative runtime.

- Pin every external dataset by immutable revision and SHA-256. Callers provide
  the local dataset path; evaluation commands must not silently download data.
- Never commit upstream dataset text, credentials, complete provider requests,
  or response headers. Committed manifests may contain stable IDs and source
  locators. Synthetic cases must identify themselves as synthetic.
- Read provider credentials and endpoints from named environment variables.
  Version model IDs, inference parameters, prompts, retry rules, clocks, and
  random seeds in the evaluation config.
- Public raw results may contain case IDs, policy decisions, model hypotheses,
  grades, and non-secret response metadata. Keep dataset questions, reference
  answers, memory content, and full provider payloads in ignored local run
  directories.
- Use fixed clocks and deterministic ordering for offline selection. Results
  must record the config, manifest, prompt, dataset, and git revisions used.

`scripts/benchmark/deermem_eviction/` evaluates the production
`select_facts_for_capacity()` implementation used by DeerMem. It compares only
the historical `confidence` policy and PR #4789's opt-in `hybrid-v1`; do not add
another eviction strategy to this evaluation. Run its offline checks from
`backend/`:

```bash
PYTHONPATH=. uv run python -m scripts.benchmark.deermem_eviction validate-contracts
PYTHONPATH=. uv run python -m scripts.benchmark.deermem_eviction validate --dataset "$LONGMEMEVAL_ORACLE_PATH"
PYTHONPATH=. uv run python -m scripts.benchmark.deermem_eviction run-policy \
  --dataset "$LONGMEMEVAL_ORACLE_PATH" \
  --output-dir /tmp/deermem-eviction-policy-run
PYTHONPATH=. uv run pytest tests/test_bench_deermem_eviction_*.py -q
```

The offline test suite must not require network access, provider credentials,
or the LongMemEval dataset. Small LongMemEval-shaped fixtures must be synthetic
and generated by tests.

`scripts/benchmark/concurrency/` measures multi-process contention on the
`users` table (N separate OS processes, not asyncio tasks) for SQLite vs
Postgres -- the scenario `CONFIGURATION.md` requires Postgres for. `worker.py`
connects directly via SQLAlchemy (skipping the ~8.5s Alembic bootstrap the
orchestrator already ran once) and mirrors the app's per-connection SQLite
PRAGMAs; `run_concurrency_bench.py` seeds a disposable per-run Postgres schema,
synchronises workers on a READY/GO barrier before timing, and exits non-zero on
any crash, short op count, or `errors > 0`. Postgres runs need a throwaway
database via `--pg-url`; nothing here touches `public`. Run from `backend/`:

```bash
uv run python scripts/benchmark/concurrency/run_concurrency_bench.py \
  --backend sqlite --workers 2,4,8,16 --ops-per-worker 50 --read-ratio 0.7
uv run pytest tests/test_bench_concurrency.py tests/test_bench_worker.py -q
```
