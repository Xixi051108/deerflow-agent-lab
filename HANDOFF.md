# DeerFlow 学习与二次开发交接

更新日期：2026-10-21。工作区：D:\deerflow-agent-lab。本文替换旧交接内容；旧文档中的“尚未安装依赖、尚未运行、Git 无提交”已过时。

## 2026-10-21 当前代码同步与下一步

用户明确授权将当前代码提交推送到远端。本次提交包含登录态专项、已有官网正文提取与浏览器采集接线、相关测试及文档；排除实际配置、密钥、`.deer-flow`运行数据、运行锁和AFC参考副本。下方“登录态尚未提交／不再推送”是10月20日当时的约束，已被本次明确授权取代；后续任务仍不默认获得提交推送或重启服务的授权。

推送前只整理4个待提交研究文件的格式，并修复跨日期的测试夹具：合成范围固定10月20日，但采集取运行当天时间，10月21日触发日期不匹配；冻结同一夹具的采集时钟，不修改生产价格规则或删除断言。首轮定向151 passed／1 failed、严格I/O149 passed／2 failed／1 skipped保留；日期修复定向30 passed。新验证日志统一为`.deer-flow/local-dev/browser-login-verification/push-20261021-*`。完整验证汇总见专项说明的本次同步记录。

下一对话先阅读实际Git状态与本文件，再做登录态前后端联调；继续检查已有官网／商品页提取改动，最后受控复测“小米15各配置报价”。仍在第五阶段，不进入预算、报告或研究面板开发。登录态合成验证与真实网页采集、真实模型质量分别验收；真实电商验收尚未通过，不能因本次同步写成业务已完成。保持禁写字节码，不复制整棵源码执行隔离测试，不恢复火绒删除的副本、不加白名单或关闭防护。本次未重启服务或使用真实账号。

## 最新停点：浏览器登录态专项（优先于下方历史）

本轮只处理浏览器登录态，不进入第六阶段。沿用已有 Playwright storage_state，已补用户隔离、Cookie/localStorage/IndexedDB 恢复、5秒周期／快照／关闭更新、30天上限及Cookie过期、版本墓碑、取消排空和清除后旧句柄失效。面板补标签／弹窗返回、粘贴／中文输入、拖动、登录提示及清除后停止重连。登录页不返回模型正文／元素，不保存截图或采集证据；返回URL去除回调参数，异常只记类型。上下文重建重新绑定请求防护并阻止service worker绕开。详情、实际命令和限制见 [专项说明](docs/learning/agent-testing-bootcamp/BROWSER_LOGIN_STATE.md)。

- **验证：** 开发前默认离线17,208 passed／362 skipped／1 failed；后续完整两分片分别8,607 passed／187 skipped和8,615 passed／181 skipped，均退出0。每分片相同的6项收集阶段跳过不能重复累计。最后小项修复之后串行专项120 passed（20.83秒）；严格I/O151 passed／1 skipped；前端浏览器18 passed，ESLint／TypeScript通过。较早119／117等专项与此重叠，不相加。全量在最后小项完成前启动，最终相关代码由串行专项补验，不将后加用例算入此前全集。
- **未全部绿色的检查：** 全局Ruff仍报本任务开始前已有的研究采集collection／middleware／tools长行与四文件格式问题，未修改这些无关工作区代码；本专项文件定向Ruff／format另行记录。指南曾因新增说明超限149字节，已下沉浏览器模块指南，最终0 errors／4 warnings、最长98,038字节，不改阈值。
- **失败历史：** 已保留红灯（刷新、大小写隔离、过期、隐私、清除、防护重绑、保存准入及关闭截图任务）、前端IME和静态检查失败。前端曾因仅读日志头误报通过，最终退出码检出2项测试类型错误；修复回调返回及元素泛型后，frontend-check-verified实际退出0、浏览器18项复测通过。最后并行环境下一轮后端专项出现3个失败后卡住，256.72秒核对进程后仅停止该测试树；日志无完整失败栈，单例与串行最终120项恢复通过，根因未确定，不能宣称已修复某个环境故障。所有日志在`.deer-flow/local-dev/browser-login-verification/`。
- **火绒：** 旧版隔离源码副本中的SkillScan文件触发`HEUR:Trojan/Python.ReverseShell.f`／`25B49D93CA5A73B8`并被删除，用户截图确认。未恢复文件、加白名单或关闭防护，原目录源码保留；不再执行被删副本。不能据此判定误报。保持`-B`／`PYTHONDONTWRITEBYTECODE=1`。
- **仓库：** 用户中途明确授权先推送阶段四／五及专项修复，已隔离并推送`e370ea378608b5368ec3d2cc99b5c896ffd92580`到origin/main并核实远端；不含本登录态功能及后续官网提取尝试。后者与AFC／运行锁均保留本地。本功能不再提交推送，未修改真实配置／密钥、未用真实账号或模型、未执行服务重启、未启动Docker、未用子Agent。
- **启用：** 将新代码部署加载后刷新前端；按README配置原browser工具、准备Playwright Chromium（Windows缺少其二进制时用隔离Chrome回退），每个DEER_FLOW_HOME仅一个Gateway、GATEWAY_WORKERS=1。开启Live手动登录，等待网站正常页再Remember login；新聊天复用，Forget all logins清除该用户全部保存状态并关闭其浏览器。本轮没有代用户启用或重启。
- **限制与后续：** state文件含凭据且不加密，Windows ACL未专项审计；不迁移原型旧状态，不保存sessionStorage／硬件凭据／CDP个人配置，站点撤销与未识别登录页需人工判断，强杀可能丢失最后约5秒变化。单Gateway内CAS不合并旧线程快照，冲突后重新打开Live。无真实电商登录验收，不保证所有网站原生硬件／文件选择器流程；保留网络防护和站点限制。当前下一步是用户按上述步骤实际启用；业务仍停留板块五，原价格提取／检索质量失败不因本功能而宣称解决。

## 当前停点：板块五核心实现与验收（优先于以下历史）

用户已确认规划并授权开始，随后要求检查运行问题再继续。本轮沿用原DeerFlow研究Agent实现第五阶段，不另建应用。新入口、价格评估、单位／冲突和兼容边界见 [实现说明](docs/learning/agent-testing-bootcamp/RESEARCH_EVIDENCE.md)，逐项测试、实际失败轮与复盘见 [测试报告](docs/learning/agent-testing-bootcamp/RESEARCH_EVIDENCE_TEST_REPORT.md)。

**同日最新补验优先：** 用户提供网页版GPT查询小米15京东各配置截图并授权相同场景验收。真实DeepSeek原研究图运行4次模型／48,068 tokens，3次搜索返回多为不相关境外商品，0采集／0价格／6缺口，正常退出但业务未通过。人工另做2次定向原DDG搜索和6次固定URL Reader诊断，确认两条京东HTML可见商品价3099.00／4099.00，Readability却主要保留评论而漏掉价格；一个京东链接空壳，三个ZOL链接Reader 403。具体失败、原始HTML哈希、独立搜索对照与下一步见 [真实电商验收报告](docs/learning/agent-testing-bootcamp/RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md)。本次仅实验脚本／证据和文档，没有改生产代码或配置；未修复，不能称第五阶段完整业务通过。

用户追问官网，已补3次实际链接读取：小米中国产品页／购买页／移动分类均Reader 200，但前后两者空壳、购买页主要为售后页脚，没有取得配置报价。详见报告第6节，未宣称确定反爬或官网无价格。用户另将AFC-code参考副本放到根目录AFC（README.md＋solve.py，标注v7.3），已读取相关检索／提取／浏览器主链并离线对比：其XPath默认会先取meta描述，两条京东样本依旧丢价；完整去脚本正文能保留金额。可借鉴中文优先检索、原始候选与有效结果分层、失败分类、缺口补读和提取回退，但不能照搬包含jd.com的噪声表、2000字符截断、全局事件循环及浏览器。详见报告第7节；未运行整份AFC、安装依赖或改参考文件。远端404／Git443失败，未核实GitHub最新提交，仅评价用户提供副本。

- **实现：** collect_research_source通过原确认／授权／独立写入处理器，保存有界提取文本、真实UTC时间、不可伪造／改写的采集字段与分段。新增价格须采集引用、实际时间和摘录金额；非价格数值核对摘录或支持的显式换算；保留已知观察／原引用，以新ID解释冲突。规划后继续采集，显式只规划任务仍可单独运行。
- **验证：** 最终默认离线两分片均退出0，共选中17,556项：17,199 passed／357 skipped／0 failed，每进程相同的6项收集跳过不重复累计。checkpoint故障2例在全量收集后独立补测通过。原链路与共享工具定向391 passed；随后数值／质量／注入等组合57 passed（重叠，不相加）。最终数值保护轮真实DeepSeek固定资料3例通过并人工核对；严格I/O全量150 passed／1 skipped，Ruff check／format通过（1543文件），指南0 errors／4 warnings。最终diff、文档链接和28项原脏文件核对通过；具体分母／耗时见报告第7节。
- **运行问题：** 两次MemoryError在测试导入初始化中出现，原单例和组合恢复通过，根因未稳定复现；沙箱WinError 5是测试临时目录setup错误，宿主正常目录运行。首轮开发后全量另出现PAT时间戳相同断言失败，独立原文件14 passed，最终全量未复现；未改认证模块／原测试，不能声称已修复该偶发问题。所有日志在 `.deer-flow/local-dev/research-evidence-verification/`，失败不覆盖。
- **重要边界：** capture仅证明取得此次提取响应，不认证类型、配置、语义、新鲜度、库存或结算。非价格未绑定观察保留原写入兼容并明确unbound，与任务书更强的全部新事实强制采集门槛有差异。pending writes已持久化时，checkpoint提交失败的get_state可展示待恢复新结果；已提交索引仍旧，真实文件须一致，不能说任意失败后投影必不变。公开商店页本轮主要提取到条款，未核实真实SKU现价。
- **仓库：** main／HEAD 0a8d5db，既有阶段4与扩展／Windows修复的未提交改动及运行锁保留；未提交推送、重启用户服务、改密钥或启动Docker。未用子Agent。旧JSON哈希仍为506f60fab96c30875be1a54ab0cc29eb46477cec66cb7f12f3c595eeda860e69。
- **下一步：** 先修复板块5文章提取遗漏商品价格的问题：缩小离线商品页失败样本→红灯→保留配置／价格／条件正文→相关回归→同场景实模复测；再改善查询与来源相关性。原HTML及对比脚本在 `.deer-flow/local-dev/research-evidence-verification/xiaomi15-*`，`xiaomi15_audit.py`可无网络复核。不得以换模型、扩大重试或进入板块6掩盖提取缺陷；预算、报告、面板仍归6／7／8。

下方为早期阶段历史，包含当时未完成描述与旧HEAD；与本节冲突时以本节及实际git状态／日志为准。

2026-10-20 两项失败修复补充（最新，优先于下方历史）：用户明确要求修复扩展／ACP 两项失败并保留失败测试。已保留两个原测试函数及全部断言，新增粗时钟分辨率回归；原失败日志均未覆盖。扩展以 asyncio 超时上下文的 expired() 判断预算来源，触发后跳过后继，避免早触发计时器误记 ERROR 和继续执行；ACP 的完整栈实际是创建子进程时的 NotImplementedError，根因为 backend/sitecustomize.py 全局强制 Windows Selector，已移除以恢复 Python 原生默认。原真实 ACP 测试通过，相关组合 123 passed、最终生命周期 15 passed；默认离线两分片均退出 0，共选中 17,489 项：17,132 passed／357 skipped／0 failed，每进程相同的 6 项收集阶段跳过不重复累计；严格 I/O 全量 148 passed／1 skipped。Ruff check／format 通过（1534 文件），指南 0 errors／4 warnings，最长链 97,334 字节，未改阈值或豁免。原函数源码一致性、冻结旧 JSON 哈希、文档链接与最终 diff 检查通过。本轮没有重跑 DeepSeek、重启用户服务、提交推送或启动 Docker；事件循环默认的变化对新启动进程生效。新日志统一 timeoutfix-*，详见本块报告第 7 节；下一业务板块仍为 5。

以下两段为专项修复前的第四阶段开发记录，保留失败历史；其中“两项尚未修复”的描述以最新补充为准。

2026-10-20 开发补充（优先于下方规划停点）：板块四代码与定向验收已完成。`research/planning.py` 将固定指引接入原研究中间件；合并后保存前校验数量、名单／排除、重复、来源与新理由／维度口径。Product 新增可选 scope_name／discovery_source_ids，冻结旧 JSON 字节和原哈希兼容通过。研究定向 269 passed、严格 I/O 148 passed／1 skipped、Ruff check／format 通过（1535 文件）。开发后默认离线选中 17,488 项：17,129 passed／357 skipped／2 failed；开发前同口径 17,075 passed／357 skipped／2 failed。两项同名失败为扩展生命周期超时日志等级与 ACP 子进程超时，修改生产代码前已出现；前者独立复测过、后者独立复测仍失败，未修改这两个无关模块。每进程另有相同的 6 项收集阶段跳过，不能重复累计。完整证据见 `RESEARCH_DISCOVERY_TEST_REPORT.md`，不能声称全量绿。

用户在本对话明确要求开发时验证真实 DeepSeek 的回答质量，不能仅用脚本模型代表真实行为。已用原中间件／工具图和固定搜索页面做三轮真实模型验证：首轮基础断言过但审核发现错误电池容量、捏造 32GB 用户要求；第二轮指定名单因非法引用重复修正失败；收紧为只提交本阶段规划集合、对照证据和停止重复查询后，最后三例通过。最终轮 20 次模型／180,957 tokens，包含失败轮及连通性共 66 次／665,808 tokens，非计费金额。每例有测试专用的 10 模型／12 工具／180 秒保护，不能当业务预算已实现。未创建持久化专用实例、未查真实产品或价格；没有提交推送、启动 Docker、改密钥或使用子 Agent。轨迹与红绿日志在 `.deer-flow/local-dev/research-discovery-verification/`，完整说明见 `RESEARCH_DISCOVERY.md` 与本块测试报告。文档链接与最终 diff 已检查，下一业务板块是 5；两项开发前已有全量失败仍保留，不把它们描述成已修复。

2026-10-20 规划补充：已阅读交接、10 个板块计划、需求及研究数据说明，并核对现有 scope／data／middleware／tools、原工厂、客户端和相关测试。当前 `main`、HEAD `0a8d5db`。新增板块四整块实施任务书 `docs/learning/agent-testing-bootcamp/RESEARCH_DISCOVERY_PLAN.md`，同步总计划入口；本轮只改规划文档，未实施业务、未运行本块业务测试、未创建真实研究 Agent 或调用模型。板块 4 仍为待开发；候选来源关联、保存前名单／数量检查、动态维度及受控验收按任务书继续。运行时 `.extensions_config.json.lock` 保持原样。下方历史提交和工作区快照以实际 Git 核实为准。

## 1. 当前任务与用户目标

用户准备 Agent 应用开发实习、测试开发实习，两条路线同等准备，每天约 8 小时，计划 11 月 1 日开始投递。希望通过真实项目学会开发、自动化测试和排错。

**当前主线已升级：在 DeerFlow 原有链路上开发开放品类的市场与竞品研究 Agent，一期优先消费者选购。** 用户明确希望高质量的完整业务流程，不满足于添加小功能。允许输入“手机”“电脑”等方向，由 Agent 发现产品、规划比较维度、收集证据、分析并交付报告；不把品类或名单写死。板块 1–3 的范围、原 Agent 接线与研究数据契约已实现，候选发现、真实采集核实、预算收束、交付与研究面板尚待开发。

原版链路学习已完成若干实际观察，两个合成业务任务诊断工具已启用并做了真实模型验证，属于入门练习。暂停 T1007 取消状态与按状态查询工具的练习，不沿旧路线自动继续开发。不要另建独立 FastAPI/Agent 应用。

用户最新要求：同时结合 Agent 应用开发、测试开发岗位可能追问的面试题来带练，包括但不限于已发截图中的题目；项目结束时还会补充面试题。每个模块记录设计取舍、实现、测试、失败与排错证据，明确已实践、待实验和需专项学习的边界。详见 docs/learning/agent-testing-bootcamp/PROJECT_AND_INTERVIEWS.md。

用户核心原则：**发现问题 → 复现问题 → 定位原因 → 最小修复 → 自动化回归。**

### 最新停点：板块 3 数据与证据契约已实现，下一步板块 4 候选发现与比较维度规划

仓库同步与 CI 跟进：板块二／三及回归修复的 77 个文件已提交并推送为 `377b726`。用户随后报告 agent-guidance 失败；按同一提交区间复现 4 条 AG002 继承链超限，前后端 lint 在截图中均通过。本轮将后端总指南的运行／基准细节原文移到 `backend/docs/DEVELOPMENT_INVARIANTS.md` 并保留指引，新增真实仓库继承链预算回归。工作区检查 0 errors／4 warnings、最长链 96,278 字节；宿主 13 项测试通过，Ruff 与内容保留／链接检查通过。沙箱三项临时目录准备错误已另列，不计通过。完整红绿表与命令见 REGRESSION_FIX_REPORT.md 末节，日志在 `.deer-flow/local-dev/agent-guidance-verification/`。本轮未改阈值、豁免、工作流或业务代码；提交后需核对远程 Actions，本地结果不等于远程已通过。继续沿用用户对仓库同步的明确授权。

本轮按用户确认的整块计划实施，不再规划旧五阶段草案的“自动研究与交付”。新增 `research/data.py` 的开放品类产品／配置／维度／来源／事实／评价／推断／引用／缺口／冲突契约，以及 `research/storage.py` 的不可变 UTF-8 JSON 快照和分页读取。`record_research_data` / `read_research_data` 通过同一 `RESEARCH_TOOLS` 在 Gateway 原工厂及内嵌客户端注册，沿用范围准入和工具权限链。实际使用与限制见 `docs/learning/agent-testing-bootcamp/RESEARCH_DATA.md`，完整证据见 `RESEARCH_DATA_TEST_REPORT.md`。

`ThreadState.research.result` 只存归属／范围／数据版本、哈希、计数和最多三个产品预览；完整结果在当前用户线程根的 research 子目录，位于沙箱 user-data 外。限制为快照 2 MiB、索引 16 KiB、引用 4,000 字符、读取 16 KiB。整批校验成功并落盘后才返回 checkpoint 更新。文件成功但 checkpoint 未提交或异步调用被取消时，只留下未引用文件，不自动提升。

新普通文字仍使确认失效；范围不变保留结果，重新确认后可读写。范围实质变化、新研究、历史恢复和分支清空当前结果索引。旧 checkpoint 无结果字段正常加载。结构与摘录检查不等于语义核实；本块不提供 verified 标记、不证明当前价格、预算停止或完整研究交付。

原实现验收定向组合 **210 passed**，包含原范围／接线回归及本块 **66 个新用例**；真实 SQLite saver 关闭重开、原工厂／worker／HTTP/SSE／历史与分支均覆盖 full／delta。内嵌客户端验证工具注册和确认门槛，其字符串 API 仍不新增结构化确认入口。真实 Windows junction 重定向和来源标签进入模型请求的问题已先复现再修复；取消文件线程通过事件同步验证。开发后严格 I/O **146 passed / 1 skipped**（27.34 秒），全局 Ruff check／format 通过（1529 文件）。开发后默认离线两分片分别 **8526 passed / 193 skipped**（664.99 秒）和 **8545 passed / 176 skipped**（665.88 秒），均退出 0；共选中 **17,428 项：17,071 passed / 357 skipped / 0 failed**，每个进程另含相同的 6 项收集阶段跳过，不重复累计。原实现最终 diff 空白检查和 84 个本地文档链接检查通过。

2026-10-19 按用户要求完成两项覆盖细节补测：失败来源有原因且正文仍匹配摘录时，关联校验仍拒绝（unsupported_quote／citations）；当前卡有效确认后只改研究 ID，同步／异步 × full／delta 均拒绝（version_conflict），无快照或结果写入。新增 **5 项**，本块当前 **71 项**；最新完整定向 **215 passed**（27.83 秒），严格 I/O 全量 **146 passed / 1 skipped**（24.07 秒），全局 Ruff check／format 通过（1529 文件）。旧 ID 负例强化后实际出现红灯：测试替身未独立替换范围占位符，提前报 invalid_data；仅修正测试替身，未改生产代码。新增独立负例首跑即通过。日志为同目录 coverage-*.log，详见板块三报告 D28／G20 及红绿表。**本次补测未重跑默认离线全集**，上述 17,071 passed 属于原实现历史结果，不包含新增 5 项。

开发前默认离线基线再次得到 **17,006 passed / 357 个选中用例 skipped / 0 failed**；两分片汇总分别 8504 passed / 183 skipped、8502 passed / 186 skipped，每次另包含相同的 6 个收集阶段跳过。沙箱内最小 asyncio 卡在 socketpair，相关进程已核对并停止，验证改在宿主执行，保持防护开启和禁写字节码。两个分片不能同时收集：已有技能测试使用固定 CaseProbe 临时文件，首次收集竞争失败，错开后重跑通过。日志：`.deer-flow/local-dev/research-data-verification/`。

板块三开发起点为 main、HEAD `609e88c`；开发及补测期间保留原有未提交改动和 `.extensions_config.json.lock`，未新建本机真实研究 Agent、未运行真实模型研究、未改密钥或实际配置、未启动 Docker、未提交推送、未使用子 Agent。补测完成后用户明确授权将全部应版本管理的文件提交并推送至已配置仓库；排除本地配置、运行数据及锁文件，远程实际状态以 Git 核实结果为准。后续从板块 4 的受控候选发现／筛选理由／动态维度写入开始，复用本块数据工具；价格核实、预算和报告仍属于板块 5–7。

### 板块 2 接线及全量回归修复历史

板块二按计划完成实现。已选定专用自定义 Agent 入口、每次明确填写运行限制、确认后所有新普通文字（包括“继续”）先重新确认。不要重复询问这些选择。

新增 `AgentConfig.research_enabled`、原 Agent／内嵌客户端的研究中间件与 `propose_research_scope`；`ThreadState.research` 保存用户／Thread／Agent 绑定、范围会话与最后处理 Run。当前卡的明确选项通过验证后才能放行工具；普通文字使旧确认失效，重复确认不重复执行研究。worker 从本次输入产生可信操作；Run 输入和手动状态更新拒绝客户端直接写研究状态。旧 checkpoint、手动历史状态与分支仅恢复草案，避免切换默认 Agent 绕过。

使用及创建专用 Agent 的请求示例见 `docs/learning/agent-testing-bootcamp/RESEARCH_INTEGRATION.md`；逐项证据和限制见 `RESEARCH_INTEGRATION_TEST_REPORT.md`。真实原工厂／worker／HTTP/SSE／事件历史流程和 SQLite 关闭重开均覆盖 full/delta；相关组合验证 **782 passed / 1 skipped**，前端原确认卡相关 **36 passed**。最终审查还修复了范围写入绕过内层权限策略和模型上下文保留标签未中和的问题，均有红绿证据。板块 2 当时的严格全量同名 16 项失败和默认离线保护超时属于历史结果，后续已完成下面的专项修复。

2026-10-19 全量回归修复已完成：修复 Windows 文件长路径、上传元数据、扩展路径声明，适配测试启动器和进程退出，补齐 ReadabiliPy JS 依赖，并以事件同步消除脆弱时序假设。最终默认离线两分片分别 **8504 passed / 183 skipped**（684.45 秒）和 **8502 passed / 186 skipped**（692.34 秒），均退出 0；共选中 17,363 项，其中 **17,006 passed / 357 skipped / 0 failed**，各进程另有相同的 6 项收集阶段跳过，不重复累计。严格 I/O **145 passed / 1 skipped**（19.09 秒）；全局 Ruff check／format 和前端 ESLint／TypeScript 通过。跳过项没有视为通过，Windows ACL、真实外部服务及真实模型质量未据此验证。详情和红绿日志索引见 `docs/learning/agent-testing-bootcamp/REGRESSION_FIX_REPORT.md`，日志位于 `.deer-flow/local-dev/full-regression-fixes/`。根 README 已按阶段追加本轮过程，未改写原有历史记录。

继续验证需保持 `-B`／`PYTHONDONTWRITEBYTECODE=1`，测试进程 PATH 加入已有根 `.venv/Scripts` 中的 uv，配置升级测试使用 `UV_NO_SYNC=1`，专测同步的临时项目会清除此变量。ReadabiliPy 当前 venv 内 JS 依赖已用 `npm.cmd install --ignore-scripts --no-audit --no-fund` 准备；重建 venv 后需重新准备，操作说明在 `backend/tests/AGENTS.md`。GNU Make 本机未安装，依赖它的检查明确 skipped。没有重启用户服务。

未创建本机真实研究 Agent、未运行真实模型研究、未构建 Docker、未提交／推送。运行限制仍只保存和展示，不能用确认卡里的数字声称已自动停止；下一块从结构化产品／证据契约开始。

### 板块 1 历史交付记录

2026-10-19 用户明确要求按完整板块带练：先列全部板块并纳入计划，再发整块开发任务，由用户连续实现、测试与排错，完成后集中讲注意事项、设计取舍及面试题；不每几行代码停下来，也不以“最小改动”代替完整业务交付。当前执行 docs/learning/agent-testing-bootcamp/MODULE_PLAN.md 的 10 个二次开发板块，旧 DAY_BY_DAY.md 诊断日历已标为历史参考。

本轮重新规划并实现首块“研究范围校验与确认约束”，不沿用旧预算示例作为功能边界。模块为 `backend/packages/harness/deerflow/agents/research/scope.py`，公开接口与完整示例见 `docs/learning/agent-testing-bootcamp/RESEARCH_SCOPE.md`，实际测试和全量回归限制见同目录 `RESEARCH_SCOPE_TEST_REPORT.md`。允许不完整草案；完整性、明确确认与正式研究准入分开。确认绑定研究标识、范围版本、请求标识和完整快照；所有实质变化使旧确认失效，过期回答拒绝，同一有效确认幂等。运行限制只声明，尚未执行。ThreadState、确认卡回答和研究动作尚未接线，不能冒充真实链路验收。

本轮明确的产品决定：消费者选购优先；只追问决定方向的信息，其他建议统一确认；购买预算允许明确不限；确认前不联网；对象、偏好、交付、运行限制等所有实质范围变化都重新确认。默认中国大陆／CNY／中文／调用方注入日期，建议在摘要中可见。自然语言歧义由后续澄清记录，本块不建通用语义规则引擎。

验证记录：前两个测试复现模块缺失和候选边界漏查，修复后结果为 `2 passed`；随后补齐剩余实现、测试及文档。

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
- 持续解释实现目的、验证证据与问题定位，避免静默完成大量改动。
- 编码前理解需求和代码；只改当前必要内容，保留现有结构，不顺手重构。
- 先解释再实践。入门诊断工具已经启用；主项目改为竞品研究。
- **Docker 镜像等开发完成再构建。当前使用 Windows 本机开发；不启动 Docker 构建。**
- 模型使用已有 DeepSeek；不重复询问选供应商或创建 OpenAI 密钥。
- 不读取或输出密钥/完整 .env，不索取登录凭据。账号由用户亲自在 UI 创建，保留认证。
- 不声称未执行的测试、全量通过或安全问题已彻底解决。
- 测试报告先列“测试用例／预期结果／实际结果”表；红绿灯记录放在用例表后，固定列为“复现／红灯原因／怎么修改／修改后／日志”。环境准备失败单列，实际结果依据执行日志，不用覆盖概述或汇总数字代替用例结果。
- 项目 README、计划、说明和测试报告聚焦业务流程、实现、问题处理与验证结果，不记录用户与助手的贡献分工。README 后续按阶段追加；本次按明确要求删除既有分工表述。
- 板块 3 开发期间不提交或推送；补测完成后用户已明确授权提交并推送全部应版本管理的文件，取代开发期间的限制。运行时锁文件、密钥及本地运行数据不纳入业务提交。仍未授权建新 Codex 对话或发送其他对话消息。
- 不主动使用子 Agent。后续读根目录与相关模块 AGENTS.md，编码按后端 TDD 要求执行。

## 3. 仓库与未提交状态

本节下方保留早期交接快照。本轮开发起点 HEAD 为 `609e88c`；板块二改动尚未提交，实际状态以 `git status` 为准。`.extensions_config.json.lock` 原已存在，保持未跟踪，不纳入业务改动。

- 当前分支：main。
- 早期基线 HEAD：768124c（chore: initialize DeerFlow v2.1.0 source and local setup scripts）；当前实际 HEAD 为第 1 节核实的 609e88c。
- 上游源码基线：DeerFlow v2.1.0，提交 345f08be00c8a9495079b732a39b46aa9af1584e。
- 上游引入、完整性、安全软件拦截历史：docs/UPSTREAM.md。
- 本次交接前 git status：
  - 修改：README.md、backend/AGENTS.md、config.example.yaml。
  - 新增：backend/packages/harness/deerflow/community/task_diagnosis/。
  - 新增：backend/tests/test_task_diagnosis_tools.py。
  - 新增：backend/tests/blocking_io/test_task_diagnosis_tools.py。
  - 新增：docs/learning/（下述学习资料）。
  - 运行时未跟踪文件：.extensions_config.json.lock，勿当功能文件提交。
- 本节列表保留早期工作区快照，当时有上传授权；本次板块 3 明确不提交推送。实际状态以第 1 节和 `git status` 为准，不要覆盖已有改动。
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
- 本地 config.yaml 使用 deerflow.models.patched_deepseek:PatchedChatDeepSeek，官方 DeepSeek API。两个合成诊断工具现已启用：取消注册项注释并修正六行多出的一个空格，已验证解析、注册、导入与直接调用。
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
5. 先读 RESEARCH_SCOPE.md、RESEARCH_INTEGRATION.md、RESEARCH_DATA.md 及对应报告，确认板块 1–3 已实现；不要重做范围、接线、数据契约或入门测试。下一步是 MODULE_PLAN.md 板块 4 的候选发现与比较维度规划。确认前普通澄清 Run 仍可创建；引用结构检查不等于事实核实，expected_revision 也不是数据库并发锁。复用当前工具和原运行互斥，不另建研究执行器。
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
- 后续通过讲解、需求变更与故障练习复盘实现和验证方法。

资料目录：docs/learning/agent-testing-bootcamp/

- MODULE_PLAN.md：10 个二次开发板块、开发任务与退出条件；板块 1–3 已实现，下一步板块 4。
- README.md：学习入口；DAY_BY_DAY.md：旧诊断日历，已标为历史参考，不再执行。
- PROJECT_AND_INTERVIEWS.md：新主项目方向、双岗位能力与证据地图、已完成记录。原日历后续内容需按新项目重新核定，不能机械继续小功能练习。
- RESEARCH_AGENT_REQUIREMENTS.md：已确认产品需求与 2026-10-19 范围确认决策，其他业务／系统链路、验收和测评草案仍待实现。
- RESEARCH_SCOPE.md / RESEARCH_SCOPE_TEST_REPORT.md：本轮独立规则接口、完整示例、信任边界、测试证据与回归限制。
- RESEARCH_INTEGRATION.md / RESEARCH_INTEGRATION_TEST_REPORT.md：板块二接口、配置示例、原确认卡与准入链路、SQLite／HTTP／SSE 证据、历史回放与分支隔离、red→green 记录。
- RESEARCH_DATA.md / RESEARCH_DATA_TEST_REPORT.md：板块三数据契约、快照和分页、权限与生命周期、受控样本、红绿／定向／全量结果和双岗位复盘。
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

## 10. 测试结果：早期诊断历史证据

证据文档：docs/learning/agent-testing-bootcamp/VERIFICATION.md。以下保留早期记录；最新全量结果见第 1 节和 REGRESSION_FIX_REPORT.md，不以本节历史状态代替当前结果。

下述为早先诊断练习证据：终端截图显示 test_missing_evidence_is_explicit 两组参数 2 passed in 2.69s；test_failed_task_returns_synthetic_evidence 为 1 passed in 1.49s。这些不能归给新主项目。本轮范围规则和全量回归尝试的结果另见 RESEARCH_SCOPE_TEST_REPORT.md；不要把历史测试与本轮结果混计。

在 backend 目录用锁定环境执行过：

    .\.venv\Scripts\python.exe -B -X utf8 -m pytest tests/test_task_diagnosis_tools.py tests/test_local_bash_tool_loading.py tests/test_lead_agent_model_resolution.py tests/blocking_io/test_task_diagnosis_tools.py -q --tb=short -p no:cacheprovider

结果 77 passed。离线模型替身，不是 77 条真实模型评测。
新增 Python 的 Ruff format/check 和当时 git diff --check 通过。

广泛回归曾 fail-fast 停止：
- 默认后端：1732 passed、30 skipped、3 deselected、1 failed。首个失败 test_bench_sandbox_provider.py::test_boxlite_shim_workaround_retries_after_fixing_permissions，Windows st_mode & 0o111。
- 严格 blocking-I/O：36 passed、1 failed。test_channel_runtime_config_store.py::test_runtime_config_store_file_is_owner_only，Windows mode 0666 vs 0600。
- 当时位于未改模块，尚未解决；本轮已修复平台适配并完成全量复跑。凭据存储的 Windows ACL 安全仍未专项核实，POSIX 权限位适配不构成 ACL 安全证明。
- 部分受限测试启动曾 WinError 5（临时目录权限），属于环境准备失败。
- 记录：backend/.diagnosis-default.local、.diagnosis-blocking.local、.diagnosis-check.local。

后续仍需：真实模型 20 场景评测、UI 自动化、故障练习 3 例、性能实验、远程 CI、简历/演示/投递材料。板块 2 HTTP/SSE 模型替身验收已完成，详见对应报告；不要把两周计划写成全部已交付。

## 11. 火绒告警与不得重复的风险操作

用户报告火绒删除：
backend/packages/harness/deerflow/skills/skillscan/__pycache__/orchestrator.cpython-312.pyc

HEUR:Trojan/Python.ReverseShell.f，病毒 ID 25B49D93CA5A73B8。
当时进程 D:\index\python.exe，命令 python.exe -，父进程为 Codex pwsh。

后续严格 pytest 与临时 LangGraph Studio 服务也触发同一路径、同一病毒 ID 的告警；已停止当时测试并核对临时服务退出。之后所有测试继承禁写字节码设置。源码再次核对与 Git 一致，不能据此鉴定已被删除的 pyc 或宣称厂商确认误报。

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
