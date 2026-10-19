# DeerFlow 学习与二次开发交接

更新日期：2026-10-19。工作区：D:\deerflow-agent-lab。本文替换旧交接内容；旧文档中的“尚未安装依赖、尚未运行、Git 无提交”已过时。

## 1. 当前任务与用户目标

用户准备 Agent 应用开发实习、测试开发实习，两条路线同等准备，每天约 8 小时，计划 11 月 1 日开始投递。希望通过真实项目学会开发、自动化测试和排错。

**当前主线已升级：在 DeerFlow 原有链路上开发开放品类的市场与竞品研究 Agent，一期优先消费者选购。** 用户明确希望高质量的完整业务流程，不满足于添加小功能。允许输入“手机”“电脑”等方向，由 Agent 发现产品、规划比较维度、收集证据、分析并交付报告；不把品类或名单写死。范围独立规则已实现，后续链路与完整业务流程尚待开发。

原版链路学习已完成若干实际观察，两个合成业务任务诊断工具已启用并做了真实模型验证，属于入门练习。暂停 T1007 取消状态与按状态查询工具的练习，不沿旧路线自动继续开发。不要另建独立 FastAPI/Agent 应用。

用户最新要求：同时结合 Agent 应用开发、测试开发岗位可能追问的面试题来带练，包括但不限于已发截图中的题目；项目结束时还会补充面试题。每个模块记录设计取舍、实现、测试、失败与排错证据，明确已实践、待实验和需专项学习的边界。详见 docs/learning/agent-testing-bootcamp/PROJECT_AND_INTERVIEWS.md。

用户核心原则：**发现问题 → 复现问题 → 定位原因 → 最小修复 → 自动化回归。**

### 最新停点：板块 1 独立规则已实现，下一步接线板块 2

2026-10-19 用户明确要求按完整板块带练：先列全部板块并纳入计划，再发整块开发任务，由用户连续实现、测试与排错，完成后集中讲注意事项、设计取舍及面试题；不每几行代码停下来，也不以“最小改动”代替完整业务交付。当前执行 docs/learning/agent-testing-bootcamp/MODULE_PLAN.md 的 10 个二次开发板块，旧 DAY_BY_DAY.md 诊断日历已标为历史参考。

本轮重新规划并实现首块“研究范围校验与确认约束”，不沿用旧预算示例作为功能边界。模块为 `backend/packages/harness/deerflow/agents/research/scope.py`，公开接口与完整示例见 `docs/learning/agent-testing-bootcamp/RESEARCH_SCOPE.md`，实际测试和全量回归限制见同目录 `RESEARCH_SCOPE_TEST_REPORT.md`。允许不完整草案；完整性、明确确认与正式研究准入分开。确认绑定研究标识、范围版本、请求标识和完整快照；所有实质变化使旧确认失效，过期回答拒绝，同一有效确认幂等。运行限制只声明，尚未执行。ThreadState、确认卡回答和研究动作尚未接线，不能冒充真实链路验收。

本轮明确的产品决定：消费者选购优先；只追问决定方向的信息，其他建议统一确认；购买预算允许明确不限；确认前不联网；对象、偏好、交付、运行限制等所有实质范围变化都重新确认。默认中国大陆／CNY／中文／调用方注入日期，建议在摘要中可见。自然语言歧义由后续澄清记录，本块不建通用语义规则引擎。

带练证据：用户按参考代码亲自完成前两个测试及对应实现，截图观察缺少模块和候选边界漏查的两次红灯，并明确报告 `2 passed`；随后说“接下来你自己执行吧，然后输出测试报告”，授权助手完成剩余实现、测试及文档。不得把助手完成部分记为用户独立实现，也不需要为了剩余部分继续停下来带练。

本轮已核实定向组合验证 `95 passed in 6.05s`（93 个范围用例、1 个新增严格 I/O 用例、1 个已有 harness 边界用例）；Ruff 检查、格式检查与文档示例执行通过。沙箱内 Windows 事件循环卡在 socketpair 初始化；沙箱外新增严格用例通过。严格全量默认临时路径为 16 failed / 128 passed / 1 skipped，短临时路径为 5 failed / 139 passed / 1 skipped；残留 5 项未导入研究模块也独立复现，不在本块修改范围内。默认离线全量最终状态以范围测试报告为准，不能声称全量绿。

默认离线全量沙箱外运行在 600.02 秒保护超时，末次完整进度行为 51%，已出现多项失败但无最终统计／详情。其失败归因尚未确定，不得统一算成既有环境问题。日志和超时元数据在 `.deer-flow/local-dev/research-scope-verification/after-offline-host.log/.json`。本轮代码与定向检查已完成，完整回归未通过；不要把外层脚本退出码 0 当作 pytest 成功。

板块 1–8 依次开发范围、链路状态、数据证据、候选维度、采集价格、预算收束、分析文件和研究面板，9 做系统回归与受控校准，10 整理演示与双岗位面试。板块 1 独立规则已有实现和离线验证；其余板块仍待开发，不重新安排基线、入门诊断或求职准备作为前置。

用户已在新对话要求浏览 handoff、确认需求，随后通过选择模式给出了下述答案；没有代建或发送其他 Codex 对话。

**以下为 2026-10-18 历史基线，当时未编写研究业务代码。** 手机研究发现当前价格证据不足；明确补证后尝试官网／京东仍未核实价格。笔记本研究先确认范围，正式研究约 10 分钟仍无报告和 CSV，由助手按临时实验保护上限点击停止，后台为 interrupted，不能算自主完成／超时停止。详见 docs/learning/agent-testing-bootcamp/BASELINE_REPORT.md。当前范围接口已实现，其余业务字段、正式评测集、权重与通过阈值仍待确定。

2026-10-18 新对话用户明确选择：

1. 两种用途都支持，一期优先消费者选购。
2. 先确认研究范围，再自动研究和交付；增加研究面板，展示对象、维度、进度和证据。
3. 按不同需求推荐候选，解释理由、取舍和不适合谁，提供对比表和证据。
4. 覆盖官方资料、独立评测、公开电商价格与用户评价，注明时间、版本和来源；无法获取时说明。用户进一步确认：必须主动查官网或京东等销售平台的当前价格，这些渠道都可作为来源，并非只接受官网；预算内补证后仍无法核实，才说明“当前价格未核实”。旧发布稿的首发价不能代替当前到手价。
5. 在约定时间和调用预算内补证，随后交付已有结果、披露缺口；证据不足不强行推荐。
6. 默认中国大陆／人民币／中文报告，每次确认范围时允许修改。
7. 先测小规模真实任务的耗时与 token，再确定可配置默认上限，正式研究前展示限制。
8. 面板之外交付带引用的 Markdown 报告和 CSV 产品对比表。

开放品类与自动发现对象保持不变；候选数量按具体任务确认，不固定 3–5 个。历史版本对比、PDF 等未纳入一期承诺。市场分析专属需求仍需细化。已有业务样例、系统链路、分层测评草案及少量真实基线观察；本轮仅实现范围独立规则，其余业务链路尚待开发。

## 2. 协作偏好与限制

- 用中文，解释正在做什么、为什么以及证据；按完整板块教学，让用户连续实现、验证和解释，完成后集中复盘，卡住时及时给提示。
- 新对话先总结已确认目标、现有可复用能力和待定项；必要问题使用用户要求的选择模式，每次不超过三个。先查仓库能回答的问题，不重复询问已确认需求或本机配置。
- 用户曾明确表示“不知道你在干嘛，真的可以学到东西吗”。不要静默完成大量代码，也不要把助手执行当作用户掌握。
- 编码前理解需求和代码；只改当前必要内容，保留现有结构，不顺手重构。
- 先解释再实践，用户亲自实现和验证。入门诊断工具已经启用；主项目改为竞品研究，不能把助手已有参考代码当作用户独立贡献。
- **Docker 镜像等开发完成再构建。当前使用 Windows 本机开发；不启动 Docker 构建。**
- 模型使用已有 DeepSeek；不重复询问选供应商或创建 OpenAI 密钥。
- 不读取或输出密钥/完整 .env，不索取登录凭据。账号由用户亲自在 UI 创建，保留认证。
- 不声称未执行的测试、全量通过、用户独立完成或安全问题已彻底解决。
- 2026-10-19 用户已明确授权将当前尚未上传的项目文件提交并推送到 `origin/main`（`Xixi051108/deerflow-agent-lab`）。此授权限于本轮上传，不包含运行时锁文件、密钥或本地运行数据；后续提交以新的用户授权为准。仍未授权建新 Codex 对话或发送其他对话消息。
- 不主动使用子 Agent。后续读根目录与相关模块 AGENTS.md，编码按后端 TDD 要求执行。

## 3. 仓库与未提交状态

- 当前分支：main。
- 当前 HEAD：768124c（chore: initialize DeerFlow v2.1.0 source and local setup scripts）。
- 上游源码基线：DeerFlow v2.1.0，提交 345f08be00c8a9495079b732a39b46aa9af1584e。
- 上游引入、完整性、安全软件拦截历史：docs/UPSTREAM.md。
- 本次交接前 git status：
  - 修改：README.md、backend/AGENTS.md、config.example.yaml。
  - 新增：backend/packages/harness/deerflow/community/task_diagnosis/。
  - 新增：backend/tests/test_task_diagnosis_tools.py。
  - 新增：backend/tests/blocking_io/test_task_diagnosis_tools.py。
  - 新增：docs/learning/（下述学习资料）。
  - 运行时未跟踪文件：.extensions_config.json.lock，勿当功能文件提交。
- 本节列的是提交前工作区快照；本轮已获得上传授权，实际提交与远程同步状态以 `git status`、`git log` 和远程分支核对为准。不要覆盖已有改动。
- 最后检查还发现 frontend/AGENTS.md 有修改，diff 仅追加 BEGIN:nextjs-agent-rules 提示块；本轮未编辑或删除该文件，已保留。不要把它混入竞品研究业务实现。
- config.yaml、extensions_config.json、.env、.deer-flow/ 与虚拟环境属于本地配置/运行数据，保持忽略。

## 4. 当前运行环境与复核证据

Windows / PowerShell，Python 3.12。开发入口：

- 页面：http://localhost:3000
- 当前诊断练习聊天：http://localhost:3000/workspace/chats/906e3726-3eaa-454f-bb94-719c14b341ba；早先 ls 实验聊天为 c68990cb-e819-42f4-ad78-75cd9dd559a2。
- Gateway：http://127.0.0.1:8001
- 早先本对话实际 GET：前端首页、/health、/health/ready 均 HTTP 200。本次最后更新交接时再次尝试这三个 GET，均被当前执行环境的套接字权限拒绝（“以一种访问权限不允许的方式做了一个访问套接字的尝试”），未取得 HTTP 响应；不能据此断言服务已停止，也不能声称本次重新确认了 200。没有为此重启服务。
- Next.js rewrites 将 /api/langgraph/* 转发到 Gateway /api/*，本机无需 Nginx。
- 已保留原有认证，用户自行创建本地管理员。
- 模型：deepseek-flash，根目录 .env 中已有 DEEPSEEK_API_KEY；禁止打印内容。
- 本地 config.yaml 使用 deerflow.models.patched_deepseek:PatchedChatDeepSeek，官方 DeepSeek API。两个合成诊断工具现已启用：用户取消注册项注释，助手只修正六行多出的一个空格，并验证解析、注册、导入与直接调用。
- extensions_config.json 是空 MCP 等扩展配置。
- 后端锁定环境：backend/.venv。根 .venv 用于早期环境检查/uv，勿混淆。
- 本次通过 backend/.venv 的包元数据复核：langchain 1.3.14、langchain-core 1.4.9、langchain-deepseek 1.0.1、langgraph 1.2.9。
- 本次复核 sandbox.use 为 deerflow.sandbox.local:LocalSandboxProvider。/mnt/user-data 是统一虚拟路径，并不能证明运行在 Linux 或 Docker；此前已核对 ls 实验 Thread 的 workspace 实际位于 D 盘的 .deer-flow/users/{user_id}/threads/{thread_id}/user-data/workspace。
- 实际检查到的 SQLite 文件为 backend/.deer-flow/data/deerflow.db；线程文件根目录则为根目录 .deer-flow。核对原始 checkpoint 时使用 SQLite URI mode=ro，只提取指定 Thread 的必要字段，不输出隐含上下文或敏感数据。
- 前后端锁定依赖已经安装，勿默认重新安装。

本地记录：

- .deer-flow/local-dev/services.json：记录 Gateway PID 14676、前端父进程 PID 14816。PID 可能过时，停止前核对实际进程。
- .deer-flow/local-dev/start_gateway.py：本地启动辅助。
- .deer-flow/local-dev/gateway.err.log、gateway.out.log。
- .deer-flow/local-dev/frontend.err.log、frontend.out.log。
- 原版无工具回答截图：.deer-flow/local-dev/deerflow-first-chat.png。

**服务仍正常时不要再启动一份。** 重启命令见 docs/learning/agent-testing-bootcamp/LOCAL_RUN.md（先阅读）。后端用 -B / PYTHONDONTWRITEBYTECODE=1；前端使用原项目 scripts/pnpm.py 和 dev.mjs。此前受限环境继承失效代理 127.0.0.1:9，曾导致外网失败；具备正常网络的环境重启后真实请求成功。区分环境连通问题与 Agent 问题。

## 5. 用户已接触的概念及真实运行

已经解释：

- Thread：持续对话的容器。
- Run：一次提交触发的执行过程。
- State：运行使用与更新的状态/消息。
- 一个 Run 可多次调用模型和工具；工具调用不会各自新建用户 Run。
- create_agent 负责装配图；agent.astream 才执行图。
- 模型选择工具名/参数，程序执行工具，结果作为 ToolMessage 再给模型。

用户曾正确回答：“一个 thread，一个 run”（针对一问中多次工具调用的练习）。不要据此声称用户已经完全掌握。

### 本对话后续实际观察

- workspace 查询 Run 7e628c71-1a54-4ccd-881b-02b99bd72712：同一 ls 实验 Thread，2 次主循环模型调用、1 次 ls，原始 ToolMessage 为 (empty)。
- demo 查询 Run 76644bc8-7561-4ea4-a619-52d55f45b9e3：2 次主循环模型调用、1 次 ls，原始返回 Error: Directory not found: /mnt/user-data/workspace/demo/。
- 不指定工具名的检查 Run c2fe0790-7b05-4e8f-ac00-ad29251ef425：模型自主选 ls 查询 workspace，返回 (empty)，2 次模型调用、1 次工具调用。以上 Run 均正常结束。
- 模型回答“在哪个盘”时没有调用工具，并根据 /mnt 猜测 Linux／Docker；实际配置和 thread_data 证明是 Windows LocalSandbox、D 盘映射。这是模型推断需要事实核查的学习案例，没有修改提示词或沙箱代码来修复。
- 新诊断 Thread 906e3726-3eaa-454f-bb94-719c14b341ba：T1001 的 Run 9c1beaf0-9f52-4802-a868-e50543b6ba76 为 query_task_status(T1001) → failed/E_TIMEOUT → lookup_error_code(E_TIMEOUT) → 上游请求超时／排查建议 → 最终回答，共 3 次主循环模型调用、2 次工具调用，success。
- 同一诊断 Thread 后续 T9999：只调用 query_task_status，ToolMessage 返回 synthetic、found:false、task_id:T9999，然后回答证据不足；没有调用 lookup_error_code。未查到任务不同于“查到任务但错误码为空”（例如 T1006）。
- 已结合源码解释 @tool("ls")、config.yaml 中 use、resolve_variable、get_available_tools、create_agent、ToolNode 按名称路由，以及模型提供 path／description、框架注入 runtime 的区别。未开展市场研究功能开发。

### 无工具基线

Thread：309da99f-d672-4c8a-b2db-26a7d8d79083
Run：58505146-4490-4e19-93fd-00a901c0c0fe

用户输入：“请用两句话中文介绍你能做什么。这次不要调用工具或子智能体。”
实际 UI 显示回答，日志 run success；约 2 秒，输入 11535 / 输出 69 token。是完整 Agent 基线。另有 14 token 供应商连通请求，只验证连接，勿混为同一次运行。

### 当前只读工具实验：工具失败，Run 完成

Thread：c68990cb-e819-42f4-ad78-75cd9dd559a2
用户任务 Run：3af42b41-e677-4825-9ae9-edd3d5ad441a

用户按指导发送：
> 请使用 ls 工具列出 /mnt/user-data/ 下的内容，再用一句话解释结果。不要使用 bash。

用户截图显示 ls 调用和 Permission denied，随后模型解释父目录不能访问、建议子目录。**模型的解释不是设计意图的权威证据。**

已核对日志：12:25:35 running；两次 DeepSeek HTTP 200；12:25:38 success，沙箱释放。
本次任务主循环：模型（input 10528/output 66）→ ls 工具错误 → 模型（input 10617/output 74）→ 最终回答。
所以用户任务是 1 Thread、1 Run、2 次模型调用、1 次工具调用。
注意日志后面还有后台记录/标题或记忆相关活动，不能把后续所有请求都计入这次主循环，也不能声称 Thread 永远只有一个内部 Run。

教学点：
- 工具被调用 ≠ 工具执行成功。
- Run 正常结束 ≠ 用户目标完成。
- 工具出错可被正常处理，模型继续回答。
- 自然语言故障解释仍须代码和运行证据核实。

## 6. 当前路径权限问题：已查到什么，尚未做什么

相关源码：

- backend/packages/harness/deerflow/sandbox/tools.py:2225，ls_tool。
- tools.py:904，validate_local_tool_path。
- tools.py:986，_resolve_and_validate_user_data_path。
- tools.py:958，_validate_resolved_user_data_path，仅接受 workspace/uploads/outputs 的实际路径及其后代。
- tools.py:711，replace_virtual_path。
- backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py:314 附近，为 /mnt/user-data 聚合父目录建立映射，注释明确支持父级 ls。
- backend/packages/harness/deerflow/sandbox/local/local_sandbox.py:771，list_dir。

ls_tool 先初始化沙箱和线程目录，再校验/映射路径，再 sandbox.list_dir。PermissionError 被捕获并变为 Error: Permission denied 字符串。

细节：
- 无尾斜杠 /mnt/user-data 在 validate_local_tool_path 入口就被拒绝。
- 有尾斜杠 /mnt/user-data/ 能通过前缀检查，但映射到父目录后，不能通过只允许三个子目录的实际路径检查。
- 底层沙箱已支持父目录映射，而工具层校验更严格。原始工具错误和源码均已核对，但没有新增工具级自动化复现或确定修复需求，勿直接认定需要放宽边界。
- 现有 test_sandbox_tools_security.py:457 明确测试拒绝无尾斜杠根目录。
- test_local_sandbox_virtual_path_contract.py:131 与 :146 覆盖底层父目录列出，但不等于覆盖完整 ls_tool。

相关测试还包括：
backend/tests/test_sandbox_windows_path_normalization.py
backend/tests/test_sandbox_search_tools.py

**没有修改权限或沙箱代码，没有新增此问题的测试，也没有执行这些路径相关测试。** 本轮只读源码/日志。

用户截图：
C:/Users/43521/AppData/Local/Temp/codex-clipboard-5a13f1e2-da9e-416c-ba4e-d2e29ff9109f.png

## 7. 新对话最先执行的步骤

1. 阅读根目录 AGENTS.md、本文件、PROJECT_AND_INTERVIEWS.md 和 RESEARCH_AGENT_REQUIREMENTS.md（后两者在 docs/learning/agent-testing-bootcamp/）。先区分已确认产品需求、方案草案与待实测项，不恢复旧小功能练习。
2. 第 1 节选择题已有明确答案，不要重复询问。市场分析专属范围在该用途实施前细化；当前先形成消费者完整闭环。
3. 需求草案已有手机、电脑与证据不足样例，以及业务／系统链路、复用模块和分层测试方案；据用户反馈调整，不把草案当作已通过的验收。
4. 先读 BASELINE_REPORT.md，手机与笔记本的少量真实基线已运行，不重复当作未做。笔记本 Thread 为 09bde3a7-7c4a-4a10-94eb-b880933b587a，研究 Run 为 9785ba42-507f-465c-8393-e2630369aece，后台 interrupted、53 次汇总模型调用、1,409,915 tokens，其中主 Agent 1,215,543、中间件 194,372。没有报告文件；10 分钟是本次外部实验保护，不是产品默认预算。先用受控用例定位有限检索／停止／部分交付，再校准默认上限；来源失败根因不能仅凭模型解释认定。
5. 先读 RESEARCH_SCOPE.md 与 RESEARCH_SCOPE_TEST_REPORT.md，确认板块 1 的接口和验证限制；不要重新从预算示例或两个入门测试开始。下一步规划板块 2：可信用户回答 → 确认记录 → ThreadState 保存恢复 → 实际研究动作准入；范围内普通澄清 Run 仍须可创建。JSON 恢复不是 checkpoint 接线，也不证明认证；expected_version 不是数据库并发锁。
6. workspace 空目录、demo 不存在、自主调用 ls，以及 T1001／T9999 均已核对；无需重复当作尚未运行的实验。市场研究的功能和评测尚未完成。
7. 如用户另要求修复根目录 ls，再按工具级复现、失败测试、最小修复和隔离回归推进，不能仅删除安全校验。当前没有要求修复它。

不要把“新 Codex 对话”与“DeerFlow Thread/Run”混淆。用户当前要求先确认需求，未要求自动创建新对话。

## 8. 真实 Agent 链路源码导航

行号为本轮已查位置，若文件后续改动先用 rg 确认：

| 环节 | 文件与定位 |
| --- | --- |
| 前端接收/提交 | frontend/src/core/threads/hooks.ts:1850 useStream，assistantId lead_agent；:2402 thread.submit |
| HTTP 入口 | backend/app/gateway/routers/thread_runs.py:941 POST /{thread_id}/runs/stream；:943 stream_run |
| 创建与调度 Run | backend/app/gateway/services.py:1459 start_run，创建记录并后台调用 run_agent |
| 执行 Worker | backend/packages/harness/deerflow/runtime/runs/worker.py:807 run_agent；:1295 agent.astream |
| 装配主 Agent | backend/packages/harness/deerflow/agents/lead_agent/agent.py:801 assemble_lead_agent；:1178 get_available_tools；:1239 create_agent |
| 动态加载工具 | backend/packages/harness/deerflow/tools/tools.py:115 附近 resolve_variable(cfg.use, BaseTool) |
| ThreadState | backend/packages/harness/deerflow/agents/thread_state.py:280 |
| SSE 返回 | backend/app/gateway/services.py:1954 sse_consumer，订阅 StreamBridge |

主路径：页面 → Next.js 代理 → Gateway → start_run → run_agent → assemble_lead_agent → astream 模型/工具循环 → StreamBridge/SSE → 页面。

## 9. 已有二次开发代码与学习材料

早先误建的独立示例已删除，**不要重建**。当前真实 DeerFlow community 工具代码：

- backend/packages/harness/deerflow/community/task_diagnosis/{__init__.py,tools.py,tasks.json,errors.json}。
- 两个工具：query_task_status、lookup_error_code。
- 合成固定数据，Pydantic 参数校验，异步 run_file_io，标注 data_source: synthetic、found；建议动作不实际执行。
- config.example.yaml 中注册项和工具组仍默认注释；本地 config.yaml 已启用两工具，完成 T1001、T9999 两个真实模型场景，属于入门样例。
- 单测覆盖输入、事实、未知记录、动态加载/分组、真实 assemble_lead_agent（仅模型替身）及执行；另有 blocking-I/O 测试。
- README.md 与 backend/AGENTS.md 记录新增工具。
- 不把助手已写出的代码当作用户个人贡献，后续需要讲解和用户独立改动/故障练习。

资料目录：docs/learning/agent-testing-bootcamp/

- MODULE_PLAN.md：10 个二次开发板块、开发任务与退出条件；板块 1 独立规则已实现，板块 2 待接线。
- README.md：学习入口；DAY_BY_DAY.md：旧诊断日历，已标为历史参考，不再执行。
- PROJECT_AND_INTERVIEWS.md：新主项目方向、双岗位能力与证据地图、已完成记录。原日历后续内容需按新项目重新核定，不能机械继续小功能练习。
- RESEARCH_AGENT_REQUIREMENTS.md：已确认产品需求与 2026-10-19 范围确认决策，其他业务／系统链路、验收和测评草案仍待实现。
- RESEARCH_SCOPE.md / RESEARCH_SCOPE_TEST_REPORT.md：本轮独立规则接口、完整示例、信任边界、测试证据、回归限制和本人／AI 贡献。
- BASELINE_REPORT.md：首轮真实手机研究、价格补证及笔记本研究的观察；笔记本人工中止，后台用量与 UI 口径分开记录，不能宣称业务验收通过。
- WORKBOOK.md、LESSON_01.md：练习与第一课。
- LOCAL_RUN.md：原版启动、真实基线、命令与链路。
- VERIFICATION.md：已执行验证与限制。
- cases/001-skillscan-antivirus-alert.md：安全软件告警记录。
- practice/ 个人练习被忽略。

### 新主项目的只读调研结果与待核定项

- skills/public/deep-research/SKILL.md 已有多角度检索、读取全文、交叉验证与综合研究的方法；已读其内容，但没有运行竞品研究或检验报告质量。新功能不能仅把既有研究技能换名当作完整二次开发。
- 当前配置已有 web_search（deerflow.community.ddg_search.tools:web_search_tool）与 web_fetch（deerflow.community.jina_ai.tools:web_fetch_tool），继续复用前先核对业务需要的返回信息与失败语义。
- 已读 ddg_search/tools.py：_search_text 在依赖缺失或异常时返回 []，与真正无结果在该返回层面可能混淆。已读 jina_ai/tools.py:68：通用 web_fetch 最终返回 Markdown 的前 4096 个字符。它们是代码事实和后续设计关注点，尚未修改或做网络实验，不应据此直接扩展共享工具。
- frontend/src/core/projects/types.ts 与现有 Gateway／前端说明显示已有项目、线程、项目文档和文件产物能力；原前端可预览 Markdown 与 CSV/TSV。用户已确认增加研究面板，并交付 Markdown 报告和 CSV 对比表。前端 core/threads/stream-state.ts 目前只显式处理 title/artifacts/todos/goal，研究字段及其刷新恢复仍需开发。
- 已有运行事件和记录／回放测试基础，参考 backend/docs/RUN_EVENT_STREAM.md、backend/docs/REPLAY_E2E.md。这些是可复用基础，不等于新业务已具备评测；模型替身回放不能证明真实模型研究质量。
- 已新增研究范围规则及对应测试；没有新增业务路由、ThreadState 字段、数据库表、业务技能、面板或真实模型评测集。范围接口已实现；运行预算默认值、其余业务接口和正式评测门槛仍待确定。规则验证不代表完整研究交付。
- 本次最后更新交接时确认：tasks.json 中没有 T1007，测试文件中没有 test_cancelled_task_returns_status_without_error；取消状态练习尚未实施，且已暂停。

## 10. 测试结果：历史证据，交接本轮未重跑

证据文档：docs/learning/agent-testing-bootcamp/VERIFICATION.md。

下述为早先诊断练习证据：终端截图显示 test_missing_evidence_is_explicit 两组参数 2 passed in 2.69s；test_failed_task_returns_synthetic_evidence 为 1 passed in 1.49s。这些不能归给新主项目。本轮范围规则和全量回归尝试的结果另见 RESEARCH_SCOPE_TEST_REPORT.md；不要把历史测试与本轮结果混计。

在 backend 目录用锁定环境执行过：

    .\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/test_task_diagnosis_tools.py tests/test_local_bash_tool_loading.py tests/test_lead_agent_model_resolution.py tests/blocking_io/test_task_diagnosis_tools.py -q --tb=short -p no:cacheprovider

结果 77 passed。离线模型替身，不是 77 条真实模型评测。
新增 Python 的 Ruff format/check 和当时 git diff --check 通过。

广泛回归曾 fail-fast 停止：
- 默认后端：1732 passed、30 skipped、3 deselected、1 failed。首个失败 test_bench_sandbox_provider.py::test_boxlite_shim_workaround_retries_after_fixing_permissions，Windows st_mode & 0o111。
- 严格 blocking-I/O：36 passed、1 failed。test_channel_runtime_config_store.py::test_runtime_config_store_file_is_owner_only，Windows mode 0666 vs 0600。
- 位于未改模块，尚未解决；不能声称全量绿。尤其凭据存储要核实实际 ACL，不能只改断言/skip。
- 部分受限测试启动曾 WinError 5（临时目录权限），属于环境准备失败。
- 记录：backend/.diagnosis-default.local、.diagnosis-blocking.local、.diagnosis-check.local。

尚未完成：真实模型 20 场景评测、完整 HTTP 模型替身链路的全部计划验收、UI 自动化、故障练习 3 例、性能实验、远程 CI、简历/演示/投递材料。不要把两周计划写成全部已交付。

## 11. 火绒告警与不得重复的风险操作

用户报告火绒删除：
backend/packages/harness/deerflow/skills/skillscan/__pycache__/orchestrator.cpython-312.pyc

HEUR:Trojan/Python.ReverseShell.f，病毒 ID 25B49D93CA5A73B8。
当时进程 D:\index\python.exe，命令 python.exe -，父进程为 Codex pwsh。

此前已核对源码未修改且匹配固定上游：
- blob be09e74aa5177731155b02a76f61da13f06d7ea8。
- SHA256 d7b084ceff7ed413e6c7c086b5b9e66330d46c7ba69d69a0f138f61b5b9002b9。
- 静态 AST 检查支持“源码是检测规则”判断，不能据此断言已确认误报或整机安全。
- 当前采用 python -B / PYTHONDONTWRITEBYTECODE=1，避免写可丢弃字节码。是临时环境处理，非厂商确认解决。
- 保持防护开启，不新增白名单，不恢复被删除 pyc，不删扫描逻辑。
- 更早源码引入阶段用户曾自行信任/恢复源码，历史见 docs/UPSTREAM.md；不要抹掉历史，也不要把它当作本轮可继续信任其他告警的授权。

其他坑：
- Next.js dev 可能自动追加 frontend/AGENTS.md 框架提示；最后检查已重新出现 BEGIN:nextjs-agent-rules 块（见第 3 节），本轮保留，别覆盖原指南或未经核对清理其他修改。
- 浏览器句柄可能失效，用户当前只留一个 tab。需要 UI 操作时先按 computer-use 技能和 CUA 文档重新绑定，勿假设旧 tab ID。
- 不混用受限环境网络失败、前端首次编译、工具权限错误、模型回答错误这几种不同问题。
- 用户主张先理解，不要以“效率”跳过讲解和用户实践。
