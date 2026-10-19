# 板块二：接线与持久化测试报告

日期：2026-10-19；Windows / PowerShell，已有 `backend/.venv`，开发起点 `609e88c`。

## 结论及证据边界

范围规则已接入原 Agent 的确认卡、ThreadState、执行门槛、checkpoint、HTTP/SSE 和事件历史。确认前不执行研究工具，确认后放行，新普通文字再阻止；SQLite 重开及历史／分支隔离通过确定性验证。

**本块定向验收通过；后续全量回归修复后，最终执行结果为零失败，跳过项不计为通过。** 没有运行真实模型研究、外部搜索、真实浏览器完整端到端场景或用户本机 Gateway 重启实验；研究质量、预算自动停止、报告交付和完整业务闭环尚未验收。

| 测试目的 | 理想输出 | 实际输出 | 测试是否通过 |
| --- | --- | --- | --- |
| 验证第二阶段接线及相关原功能 | 相关断言全部通过，无失败 | **782 passed / 1 skipped**，39.16 秒；pytest 成功；该数量包含原功能回归，并非全部为新增用例 | 已执行项通过；含跳过项 |
| 验证前端研究卡与原 human-input 协议 | 卡片识别、回答构造和消息恢复断言通过 | 四个测试文件 **36 passed / 0 failed** | 通过 |
| 检查前端代码规范与类型 | ESLint 和 TypeScript 无错误，退出 0 | `pnpm check` 通过，退出码 0 | 通过 |
| 检查后端代码规范与格式 | Ruff check／format 均通过 | 相关文件及后续全局检查均通过，全局格式检查为 1521 个文件已格式化 | 通过 |
| 检查改动中的空白错误 | `git diff --check` 退出 0 | 通过；HANDOFF 的 CRLF→LF 提示不是差异错误 | 通过 |
| 验证最终默认离线全集 | 完成整个集合，0 failed；明确列出跳过 | 两分片共 **17,006 passed / 357 项选中测试 skipped / 0 failed**；每进程另有相同的 6 项收集阶段跳过，不重复累计 | 已执行项通过；含跳过项 |
| 验证最终严格 I/O 全集 | 严格检查完成，0 failed；明确列出跳过 | **145 passed / 1 skipped**，19.09 秒 | 已执行项通过；含跳过项 |

第二阶段当时的全量记录保留为历史：修改前严格 I/O 为 **16 failed / 128 passed / 1 skipped**（33.99 秒），修改后为 **16 failed / 129 passed / 1 skipped**（27.77 秒），失败名称集合相同。默认离线修改前后均在 180.02 秒保护超时，末次进度分别为 9% 和 11%，均无最终统计。上述失败及超时随后专项定位和修复，最新结果见表格及 [全量回归修复记录](REGRESSION_FIX_REPORT.md)。

## 功能测试明细

以下“实际输出”来自已执行测试的返回值、状态和处理器调用记录，不是预设回复文案。模型与外部工具使用替身；图、原 Agent 工厂、中间件、RunManager、worker、StreamBridge、FastAPI 路由及 SSE 使用原实现。HTTP 测试通过 FastAPI TestClient 驱动，没有启动真实浏览器。

| 测试目的 | 理想输出 | 实际输出 | 测试是否通过 |
| --- | --- | --- | --- |
| 未确认时，模型直接调用搜索 | 拒绝研究，底层搜索处理器调用为 0；同步、异步一致 | 两种调用均记录 `invocations == []`，确认记录为 `None`，消息包含未确认提示 | 通过 |
| 未确认时，模型调用其他研究工具 | 命令、MCP、浏览器、写文件、普通／批量委派均不执行 | 六类工具替身处理器调用均为 0 | 通过 |
| Run A 提交完整范围 | 保存待确认快照，生成绑定当前请求的卡片，不执行搜索 | 卡片与状态的 `request_id` 相同，摘要含价格口径，搜索记录为空 | 通过 |
| Run B 明确确认当前卡片 | 保存确认，允许本 Run 研究 | 确认记录绑定原请求，搜索记录由空变为 `["手机"]` | 通过 |
| 重复提交已生效的确认 | 幂等处理，不重复研究 | 再次提交后搜索记录仍为 `["手机"]`，未增加调用 | 通过 |
| Run C 发送“继续”或修改条件 | 先清除旧确认，再阻止研究 | 确认记录变为 `None`；搜索累计次数保持 1，未新增研究调用 | 通过 |
| 范围内容不变时主动取消确认 | 清除待确认及已确认记录；重新出卡使用新请求标识 | 失效规则断言通过；原 93 项范围规则测试继续通过 | 通过 |
| 使用旧请求、错误选项／来源／正文或自由文字回答 | 不能生成有效确认，不放行研究 | 各组非法回答的确认记录均为空，搜索处理器调用为 0 | 通过 |
| 同次输入混入条件修改与确认 | 保持未确认，要求复核 | 混合输入后确认记录为 `None`，搜索记录为空；额外编辑字段和非法协议类型也被拒绝 | 通过 |
| 范围提议与搜索同批提交 | 仅处理范围，不允许搜索并行执行 | 合法提议产生待确认记录，搜索处理器调用为 0；多个／格式错误提议的兄弟研究调用同样受阻 | 通过 |
| 修改范围或开始新研究后回答旧卡 | 旧版本／旧研究确认失效 | 新研究使用新标识；旧卡不能确认当前研究，相关断言通过 | 通过 |
| 不同用户／Agent 或关闭研究开关尝试继续旧研究 | 不能借配置或身份变化绕过确认 | 非所属身份、切换 Agent 和关闭开关的绕过测试均通过，未放行研究工具 | 通过 |
| SQLite full／delta 关闭重开 | 新 saver、新图恢复同一数据库中的待确认及已确认状态 | 两种模式重开后状态分别与保存值相等；恢复后可确认并搜索，第三次重开修改条件后再次阻止，搜索总计 1 次 | 通过 |
| 原 Gateway HTTP/SSE 跨 Run 衔接 | HTTP 成功、SSE 携带研究卡与状态；确认前阻止、确认后放行、修改后再阻止 | full／delta 均返回 HTTP 200；搜索记录依次为 `[]`、`["search"]`、`["search"]` | 通过 |
| 重新读取状态和事件历史 | 能读取同一范围、卡片及已提交回答，支持前端恢复所需数据 | 状态接口返回的 `research` 与 Run 输出相等；历史消息含匹配的卡片和隐藏回答请求标识 | 通过 |
| 前端识别研究卡并恢复回答状态 | 进入原确认卡分组，回答正确绑定请求；已回答卡片不再待答 | 分组为 `assistant:clarification`；回答携带正确请求／选项／来源；恢复后 `latestOpenRequestId` 为 `null` | 通过 |
| 客户端直接写 `research` 或伪造可信上下文 | 拒绝服务端状态写入；客户端不能构造有效操作标记 | Run 输入和手动状态接口写入返回 HTTP 422；两个配置区的可信标记注入均未生效 | 通过 |
| 其他用户访问当前 Thread | 不泄露或运行他人研究 | 状态读取与运行请求均返回 HTTP 404，搜索未执行 | 通过 |
| 历史 checkpoint 回放及手动历史更新 | 不复用历史确认；选择研究前状态也不能移除门槛 | 回放后未确认，搜索累计次数未增加；切换默认 Agent、手动历史更新的绕过断言均通过 | 通过 |
| 创建分支 | 保留草案，生成新研究标识，清除父研究确认 | 原分支接口返回的新 Thread 中，范围相等、研究标识不同，待确认和确认记录均为 `None` | 通过 |
| 使用内嵌 `DeerFlowClient.stream` | 使用同一研究门槛并输出研究状态 | 跳过确认的搜索记录为空，`values` 事件中含 `research` 状态 | 通过 |
| 范围工具遭原权限策略拒绝 | 不越过原权限链产生范围写入或确认卡 | 同步／异步 guardrail 拒绝测试通过，拒绝时没有范围提议写入 | 通过 |
| 范围数据含模型上下文保留标签 | 模型请求投影中和标签，原始范围及确认快照不被篡改 | 模型上下文与持久化原始快照的相关断言通过 | 通过 |
| 普通聊天、原澄清及非交互配置 | 普通功能兼容；非交互标记不能代替研究确认 | 普通 Thread／原澄清回归通过，非交互绕过测试未放行研究 | 通过 |
| 新异步图是否阻塞事件循环 | 范围提议、确认及准入通过严格 I/O 探测 | 新增用例在原 Blockbuster 探测器下通过 | 通过 |
| 原 Agent API、SQL 存储及运行链路回归 | 配置保留、状态归并、双模式 checkpoint、分支和事件契约无回归失败 | 纳入 782 项相关组合并通过；总数同时包含上述研究场景和原功能，未重复累计 | 通过 |

SQLite 重开验证的是持久化适配和图恢复；Gateway 测试验证原 HTTP/SSE 链路。二者是分层证据，没有把它们写成已经真实重启用户服务或完成线上部署实验。

主要用例源码：[图与跨 Run／SQLite 测试](../../../backend/tests/test_research_agent_integration.py)、[Gateway HTTP/SSE 测试](../../../backend/tests/test_research_gateway_http.py)、[输入边界测试](../../../backend/tests/test_research_gateway_boundary.py)、[前端卡片协议测试](../../../frontend/tests/unit/core/messages/research-card.test.ts)。

## 尚未执行的验收

| 测试目的 | 理想输出 | 实际输出 | 测试是否通过 |
| --- | --- | --- | --- |
| 本机专用研究 Agent 的真实浏览器流程 | 页面选择 Agent、真实模型出卡、点击确认、重新打开页面恢复 | **未执行**；本机专用 Agent 尚未创建，前端协议测试不能代替浏览器验收 | 未执行 |
| 真实 DeepSeek 与外部搜索研究质量 | 模型正确理解需求、提交范围并获得可核实的研究资料 | **未执行**；本块使用模型和外部工具替身 | 未执行 |
| 用户本机 Gateway 进程重启恢复 | 重启实际服务后读取原研究状态并继续交互 | **未执行**；已执行的是临时 SQLite saver 与图的关闭重建 | 未执行 |
| 预算自动停止、报告与研究面板 | 预算到限停止，生成报告与对比表并在面板展示 | **未实现／未验收**；属于后续板块 | 未验收（尚未实现） |

## 实际 red→green 与排错

本机原始日志位于 `.deer-flow/local-dev/research-integration-verification/`，该目录属于忽略的本地验证数据，不提交。

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志 |
| --- | --- | --- | --- | --- |
| 新文字即使未改变范围也需失效 | 缺少 `invalidate_confirmation` 操作，无法主动清除旧确认 | 补充不可变状态转换，清除待确认及确认记录，保留原范围版本 | 通过：内容未变也能清除确认；新文字触发后研究工具再次受阻 | `01-invalidate-red-host.log`、`02-guard-green.log` |
| 原图执行前门槛 | 缺少研究中间件，原图没有研究确认准入检查 | 在真实同步／异步工具处理链外接入研究中间件 | 通过：未确认时底层研究工具处理器调用为 0 | `02-graph-red.log`、`02-guard-green.log` |
| 跨 Run 卡片确认 | 范围提议工具尚未生成确认卡，无法衔接后续回答 | 从可信范围快照生成卡片，处理明确回答并写回状态 | 通过：Run A 出卡且不搜索，Run B 确认后搜索，Run C 新文字再次阻止 | `03-cross-run-red.log`、`04-boundary-green.log` |
| Agent 配置／状态写入边界 | API 缺少研究字段，客户端可写入研究状态或伪造操作上下文 | 补齐原 Agent 接口，保护 Run 输入、手动状态更新及配置中的可信上下文 | 通过：研究配置可读写；直接写 `research` 返回 422，可信操作注入未生效 | `04-boundary-red.log`、`04-boundary-green.log` |
| 前端沿用原卡 | 研究 ToolMessage 被归入普通工具处理组 | 在原消息分类器中识别研究范围工具的确认消息 | 通过：进入原确认卡分组，回答绑定当前请求，恢复时识别已回答状态 | `06-card-red-host.log`、`frontend-unit-final.log` |
| 旧 checkpoint＋Agent 切换 | 旧记录可重新确认，选择研究前状态可移除研究门槛 | 同时检查当前 head 与所选状态，将历史范围恢复为新研究草案 | 通过：历史确认不能复用；切换默认 Agent 和选择早期状态均未放行搜索 | `08-replay-red.log`、`08-replay-green.log` |
| 手动历史状态写入 | 从旧 checkpoint 手动更新状态，可间接恢复旧待确认记录 | 在原 checkpoint 写入预约内，将历史研究重开为未确认草案 | 通过：旧待确认记录被清除，再提交旧回答不增加搜索次数 | `09-manual-replay-red.log`、`09-manual-replay-green.log` |
| 格式错误的范围提议与搜索并行 | 仅检查合法 `tool_calls`，漏掉 `invalid_tool_calls` 中的范围提议 | 将格式错误的范围提议也作为停止同批研究调用的信号 | 通过：即使已确认，格式错误提议同批的搜索也不执行 | `10-malformed-red.log`、`11-edited-answer-green.log` |
| 确认夹带编辑及运行身份 | 解析器忽略额外字段、将 bool 当作版本 1，未校验正文及运行 Agent | 在当前操作入口和中间件补充字段、类型、正文及运行身份校验 | 通过：夹带编辑、非法协议类型和不匹配回答不能确认或放行研究 | `11-edited-answer-red.log`、`11-edited-answer-green.log` |
| 内嵌客户端漏接 | 已读取 Agent 配置，但未将研究开关及用户操作传入运行链路 | 为 `DeerFlowClient` 接入相同装配、可信操作和工具门槛 | 通过：跳过确认的搜索未执行，`values` 事件包含研究状态 | `12-embedded-red.log`、`12-embedded-green.log` |
| 分支创建时记录复制 | 新 Thread 仍使用父研究标识和确认记录 | 创建分支写入状态时，立即生成新的未确认研究会话 | 通过：分支保留范围草案、研究标识不同，待确认及确认记录均为空 | `13-branch-red.log`、`13-branch-green.log` |
| 范围写入跳过既有权限链 | 原 guardrail 已拒绝范围工具，但仍能生成确认卡 | 按调用绑定工具副本并调用原 handler，原权限／技能策略／guardrail 通过后才产生状态 Command | 通过：同步／异步拒绝时待确认记录为空，工具消息返回错误 | `18-policy-red.log`、`18-policy-green.log` |
| 研究数据上下文保留标签 | 范围数据中的模型上下文保留标签未中和 | 复用原输入中和函数，仅修改发送给模型的请求投影 | 通过：模型上下文不含原始 `<system>` 标签，持久化范围保留原始内容 | `19-context-red.log`、`19-context-green.log` |

测试自身也有过修正：新增图 hook 后原测试的 8 步递归限制不足；一次补测试时把原测试尾部放错位置造成 NameError；SSE 解析最初没有排除 id 行；分支接口起初写成单数路径并使用了用户消息，按现有 `/branches` 助手消息契约修正后才复现真正的标识复制问题。内嵌客户端测试也先修正了配置所属用户。这些测试准备错误不计作产品缺陷。

早期一次工具执行因自动审批账号用量限制未运行；恢复时间后经正常审批重新执行。未执行的那次不计为任何测试结果。

## 第二阶段复现命令与历史全量限制

在仓库根目录使用已有虚拟环境；Windows 沙箱中曾复现 socketpair 初始化阻塞，沙箱外本机 socketpair 正常，因此异步验证在正常审批后的宿主环境运行。无需重新安装依赖或提供密钥。

```powershell
$env:PYTHONUTF8 = '1'
backend/.venv/Scripts/python.exe -B -m pytest backend/tests/test_research_scope.py backend/tests/test_research_agent_integration.py backend/tests/test_research_gateway_boundary.py backend/tests/test_research_gateway_http.py backend/tests/blocking_io/test_research_scope.py backend/tests/blocking_io/test_research_agent.py -q
backend/.venv/Scripts/python.exe -B scripts/pnpm.py rstest run research-card human-input
backend/.venv/Scripts/python.exe -B scripts/pnpm.py check
```

最终 782 项组合还包含 `test_agents_router_model_settings.py`、`test_agent_store_sql.py`、`test_harness_boundary.py`、原澄清两个测试文件、`test_lead_agent_model_resolution.py`、`test_client.py`、`test_thread_state_reducers.py`、`test_gateway_services.py`、`test_gateway_checkpoint_mode.py`、`test_threads_checkpoint_mode.py`、`test_branch_history_seed.py` 和 `test_run_event_stream_contract.py`。执行命令、pytest 输出保留在 `related-complete.log`；36 项前端结果在 `frontend-unit-final.log`，最终前端检查在 `frontend-check-final.log`。

第二阶段当时修改前后都按 `backend/Makefile` 两个离线目标的参数调用同一锁定环境：

- 默认离线：`pytest -m "not live" --ignore=tests/blocking_io tests/ -q --tb=short`，180 秒保护。
- 严格 I/O：`pytest tests/blocking_io -q --tb=short`，120 秒保护；两次均在超时前结束。

与 Makefile 的默认离线目标相比只改变详细输出格式及增加外层保护，不声称执行过 `make`。`before-host-*.log/.json`、`after-final-host-*.log/.json` 分别保留 pytest 退出码、是否超时和耗时；不能把外层日志脚本退出码当成 pytest 成功。数据通道单行中和修复后重跑了 782 项相关组合；当时两项大套件的记录来自此前的权限链修复后，仍有失败／超时，属于历史结果。后续最终全量复现命令和日志见专项修复报告。

当时严格全量失败于 channel runtime config store、Lark auth completion、project documents／promotion／trash 等既有测试；默认离线无最终统计。这些问题后来已逐项定位、修复并完成全量复跑，不覆盖或改写原失败记录。

## 后续工作

已确定使用专用 Agent、每次明确填写运行限制，以及新普通文字触发重新确认。

下一步是板块三的研究数据与证据契约。实际预算计数／停止、受控真实模型质量验证、报告和面板仍按后续板块推进；历史失败／超时及后续修复结果均保持公开，不把本块定向通过扩写为整个项目完成。

## 后续全量回归修复（2026-10-19）

上述全量失败与超时保留为本阶段历史记录。后续专项修复完成后，默认离线两分片合计 **17,006 passed、357 项选中测试 skipped、0 failed**（每进程另有相同的 6 项收集阶段跳过）；严格 I/O **145 passed / 1 skipped**，Ruff 与前端检查通过。原因、修复和验证边界见 [全量回归修复记录](REGRESSION_FIX_REPORT.md)。
