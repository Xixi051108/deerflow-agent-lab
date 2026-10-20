### Agent System

**Research scope rules** (`research/scope.py`):
- Offline Pydantic models and immutable transitions; no Gateway, model client, tools, or I/O. `ResearchScope` accepts incomplete drafts; `assess_scope` reports missing/ambiguous information. `with_defaults(..., as_of_date=...)` labels absent market/currency/language/date defaults; explicit `None` stays unresolved.
- `ResearchScopeSession` is trusted application state. `prepare_confirmation` binds a full snapshot to research/version/request ids; `respond_to_confirmation` accepts only explicit confirm/reject responses. `revise_scope` replaces the entire scope with an expected-version check and invalidates confirmations on normalized content changes. Use validated reconstruction, never `model_copy(update=...)` for state transitions.
- `require_confirmed_scope` is wired through `research/middleware.py` at each actual tool boundary. `ThreadState.research` stores JSON `ResearchState` with owner/thread/agent identity, scope session and last processed run. `invalidate_confirmation` clears pending/confirmed receipts on every new ordinary user text, including "continue"; meaningful edits still increment the scope version.
- `AgentConfig.research_enabled` opts in. `propose_research_scope` accepts only a whole scope and expected identity/version; the middleware generates the original Human Input Card protocol and ends the turn. Explicit current-card options alone confirm/reject; duplicate confirmation never re-executes tools. Do not expose session/receipt construction to models or client-writable state.
- The run worker constructs `__deerflow_research_turn` from the current normalized input, refuses caller copies, and cleans it up after execution. Both Gateway state-writing boundaries reject `research`. The middleware remains dormant on ordinary threads but refuses an existing research thread when its agent/mode is switched off. It sits outside tool/sandbox wrappers, with sync/async parity; scope/clarification batches cannot execute research siblings, including malformed proposals.
- Scope writes still traverse the normal tool-policy chain: bind a per-call tool copy with `ToolCallRequest.override(tool=...)`, then invoke the original handler. Never execute a scope Command before authorization/skill/guardrail checks, or mutate the shared tool object. Raw proposal validation also runs before provider-schema coercion.
- Historical resume and manual historical state updates reopen selected drafts with a new research id, retaining the current-head gate if the selected checkpoint predates research. Branch writes reset receipts and bind a new research id to the new thread immediately. Use the existing admission/checkpoint reservation and whole-record writes, never a separate lock/store. Original factory ABI and generic journal/SSE contracts remain unchanged.
- Declared runtime limits are not enforced here. Hard constraints/preferences remain separately represented text; unresolved semantic questions block confirmation. No category DSL, feasibility guarantee, numeric product defaults, or preconfirmation network exploration.
- Tests: `tests/test_research_scope.py`, `tests/test_research_agent_integration.py`, `tests/test_research_gateway_{boundary,http}.py`, and strict `tests/blocking_io/test_research_{scope,agent}.py`. Root guides: `docs/learning/agent-testing-bootcamp/RESEARCH_SCOPE.md`, `RESEARCH_INTEGRATION.md`, and their test reports. SQLite close/reopen and real factory/worker HTTP/SSE tests cover full/delta; provider/tool replacements do not establish live research quality.

**Research data and evidence** (`research/data.py`, `research/storage.py`):
- `ResearchBatch` / `ResearchResult` validate products, configurations, dimensions, sources, claims, quotations, gaps and conflicts; upserts revalidate the entire merged graph. Known facts/opinions need configuration-matched quotations; inferences cite known facts/opinions. Unknowns remain null with a reason; finite numeric values and money use Decimal. Price observations keep their basis and conditions, never acquire a verified flag.
- `record_research_data` / `read_research_data` are registered through the common `RESEARCH_TOOLS` tuple in both original factories. Bind per-call implementations through the existing handler, after policy checks; validate raw arguments before provider coercion. Reject mixed/multiple/malformed write batches, and check expected research/scope/data versions.
- Checkpoint `research.result` is a bounded `ResultRef` (identity/version/hash/counts/preview); `phase` is derived from confirmation as awaiting_confirmation/recording. Scope changes, new studies, replay and branching clear the pointer. Same-scope reconfirmation retains it. Old checkpoints load without migration; invalid persisted research stops rather than being silently replaced by an empty study.
- UTF-8 JSON snapshots live at the owner's thread root, `research/{research_id}/scope-{version}/{sha256}.json`, outside user-data. Resolve confinement to that exact directory, including Windows junctions. Use temp+flush+fsync+replace, immutable snapshots and checkpoint selection; never scan for a latest file. Unreferenced files after checkpoint failure/cancellation are not promoted. Async tool I/O runs through `run_file_io`.
- Limits: snapshot 2 MiB, result projection 16 KiB, quote 4,000 characters, read response 16 KiB. Pages stop at complete records; oversized single records error explicitly. Sources remain untrusted data: sanitize reserved tags only in model-request ToolMessage copies and preserve raw stored text. These checks do not establish semantic support/current price validity.
- Tests: `test_research_data.py`, `test_research_storage.py`, `test_research_data_integration.py`, `test_research_data_http.py`, and strict `blocking_io/test_research_data.py`. Root guide and actual red/green evidence: `RESEARCH_DATA.md` / `RESEARCH_DATA_TEST_REPORT.md` in the learning directory.

**Discovery planning** (`research/planning.py`): static instructions use the research middleware, even with `skills: []`. After batch merge and before save, validate confirmed candidate count, named/excluded bindings, duplicates, touched reasons/dimension rationale and discovery evidence. `Product.scope_name` is a model-declared scope-name binding, not identity verification; `discovery_source_ids` references product-owned sources, not proof of retrieval or truth. Optional defaults preserve old snapshots; do not enforce new-write requirements while loading them. Save planning before collection unless the user requests planning only. Opt-in `test_research_planning_live.py` uses real configured DeepSeek with frozen web tools and test-only limits; it cannot prove live-web quality. See root `RESEARCH_DISCOVERY.md` and its test report in the learning directory.

**Source capture** (`research/collection.py`, `evidence.py`): `collect_research_source` uses the same confirmation/policy/single-write gate. Only observed URLs; bounded Reader/text/segments; file I/O offloaded. Ordinary batches cannot mint/change captures or overwrite known observations/citations. New prices require capture/time/amount support; non-price unbound writes remain compatible and explicitly unbound. Read claims derive assessment before page sizing, never verified truth. See root learning `RESEARCH_EVIDENCE.md` and its test report for limits and semantic boundaries.

**Lead Agent** (`packages/harness/deerflow/agents/lead_agent/agent.py`):
- Entry point: `make_lead_agent(config: RunnableConfig)` registered in `langgraph.json`.
  Its signature and bare-graph return type are a published ABI: LangGraph Server calls it
  directly, so neither may change.
- `assemble_lead_agent(config, *, app_config=None) -> LeadAgentAssembly(graph, descriptor)`
  is the richer entry point the Gateway uses; `make_lead_agent` is a thin wrapper returning
  `.graph`. The descriptor is built by
  `deerflow/agents/assembly_descriptor.py::build_assembly_descriptor()` and captures what
  only the factory knows — the model resolved after runtime overrides, the rendered prompt
  hash, the tool list left by authorization, and the composed middleware stack in order.
  Consumers of a factory result must unwrap `.graph` defensively (see
  `runtime/runs/worker.py::_agent_graph`), because a third-party factory still returns a
  bare graph.
- Dynamic model selection via `create_chat_model()` with thinking/vision support
- Tools loaded via `get_available_tools()` - combines sandbox, built-in, MCP, community, and subagent tools
- System prompt generated by `apply_prompt_template()` with skills, memory, and subagent instructions
- Custom Agent `memory_enabled: false` disables memory reads, writes, tools, and compaction flushes while retaining date context; manual compaction trusts the state-producing checkpoint's agent binding, and global disable stays authoritative. Embedded clients cache the named policy by agent/user until `reset_agent()`; unreadable configs keep the legacy enabled default and log a warning.
- **Prompt trust**: framework authority uses the system channel; user/model-influenced text uses the sanitized `HumanMessage` data channel. Never interpolate untrusted values into system text—even escaped tags do not neutralize natural-language injection (PR #5090).
- Pass the same rendered prompt and middleware objects to the graph and assembly descriptor so observers describe the live graph, including Custom Agent `allowed_subagents` scope.

**ThreadState** (`packages/harness/deerflow/agents/thread_state.py`):
- Extends `AgentState` with: `sandbox`, `thread_data`, `title`, `artifacts`, `todos`, `uploaded_files`, `viewed_images`, `goal`, `promoted`, `delegations`, `skill_context`, `summary_text`, `research`
- Uses custom reducers: `merge_artifacts` (deduplicate), `merge_viewed_images` (merge/clear), `merge_goal` (preserve the active goal across ordinary state updates unless the goal writer replaces it), `merge_promoted` (catalog-hash-scoped deferred tool promotions), `merge_delegations` (append task delegation entries, same id latest wins, terminal status never downgraded, capped to the most recent entries), and `merge_skill_context` (dedupe active-skill references by path, keep the most recently read entries; entries store a name/path/description reference, not the SKILL.md body). `summary_text` is a LastValue channel updated by summarization and projected into model requests as durable context data instead of being stored as a `messages` item.
- Delta-mode `merge_message_writes` normalizes the current message state once,
  then folds normalized writes in order with message-ID position indexes and
  deferred tombstone compaction. It preserves public `add_messages` behavior,
  including duplicate IDs, replacement position, removal errors,
  `REMOVE_ALL_MESSAGES`, null-write errors, and missing-ID allocation order,
  without rescanning the accumulated state for every write. Keep this
  full-parity contract covered by differential tests: LangGraph's private
  `_messages_delta_reducer` is also linear, but intentionally omits some of
  those public `add_messages` semantics and cannot be substituted directly.

**Runtime Configuration** (via `config.configurable`):
- `thinking_enabled` - Enable model's extended thinking
- `model_name` - Select specific LLM model
- `is_plan_mode` - Enable TodoList middleware
- `subagent_enabled` - Enable task delegation tool
- `max_concurrent_subagents` - Per-response `task` call concurrency limit (clamped by `SubagentLimitMiddleware`)
- `max_total_subagents` - Optional per-run total delegation cap override (falls back to `subagents.max_total_per_run`, clamped to 1-50)
  Gateway and `DeerFlowClient.stream()` always provide the runtime `run_id`; custom
  graph integrations must do the same. If it is absent, enforcement deliberately
  counts the thread's full delegation ledger (fail-restrictive) and emits a warning.

**Direct subagent runtime**: `create_deerflow_agent(..., subagent_runtime=runtime)` is the explicit dependency-injection path for direct graph callers. Reuse one `deerflow.subagents.SubagentRuntime` across every graph that belongs to the same application capacity boundary. With the default subagent feature it binds middleware concurrency/total limits, the ordinary `task` tool, one real execution controller, and any active durable-batch submitter to the same snapshot. A caller-owned batch repository requires `await runtime.start()` (or `async with runtime`) before graph construction and `stop()` at shutdown; the factory fails closed while that worker is stopped, and already-built bound batch tools must fail unavailable after it stops rather than falling through to another process-global submitter. The factory never creates SQL infrastructure, renders the caller-owned `system_prompt`, or mounts Gateway API/UI routes. Full middleware takeover cannot be combined with this runtime; direct callers and custom subagent middleware remain responsible for model-visible call-policy wording.
