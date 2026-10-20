# 板块四测试报告：候选发现与比较维度规划

日期：2026-10-20。实现与定向验收已完成。开发阶段默认离线出现的两项同名失败保留在第 4、5 节；用户追加要求后已修复，最新完整离线 **17,132 passed／357 skipped／0 failed**，严格 I/O **148 passed／1 skipped**，证据见第 7 节。接口与限制见 [实现说明](RESEARCH_DISCOVERY.md)，任务依据见 [计划](RESEARCH_DISCOVERY_PLAN.md)。

## 1. 测试用例、预期与实际结果

以下确定性用例包含在最终研究组合 **269 passed** 中；D04 的两个额外公开契约检查另列，不冒充真实模型验证。新增离线用例为 29 项契约／规则、25 项原图／接口用例，共 54 项；另新增 2 项严格 I/O 与 3 项显式 opt-in 真实模型用例。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| D01 手机受控发现与规划 | 确认后检索／读取、写入来源与影像维度并回读 | 同步／异步 × full／delta 通过；最终真实模型保留两款全新机、排除二手机 |
| D02 编程／携带笔记本 | 使用与用途相关的维度，配置独立 | 同步／异步 × full／delta 通过；真实模型规划内存、重量、开发兼容性与接口等维度 |
| D03 仅指定名单 | 名单外对象不能成为候选，不通过旧 ID 偷换对象 | 原图负例 full／delta 通过；真实名单样例未补入搜索附带的长航 B2 |
| D04 指定加自动补充 | 保留指定对象并允许有来源的新候选；排除别名不能入选 | 额外公开接口检查 2/2 通过，日志 mixed-and-excluded-contracts；未将此路径冒充已单独实模验证 |
| D05 明确排除与绑定 | 规范名称精确排除及排除绑定生效，不能将 A 重绑 B | 规则参数化用例及 D04 排除别名检查通过 |
| D06 合并后数量上限 | 第二批使总数超限时整批拒绝，保留旧 revision 与文件 | 首轮真实图复现错误保存 3 款；修复后纯规则及原图 full／delta 通过 |
| D07 去重与配置 | 同一指定对象／品牌型号不能重复占名额；Pro 后缀和配置关系保留 | 同名、绑定别名、同品牌型号、Pro 不误合并及多个配置用例通过 |
| D08 发现来源关联 | 拒绝悬空、跨产品、重复、failed／unknown 或空文本来源 | 规则用例通过；单独更新来源为失败时也不能使旧候选失去有效依据 |
| D09 指定对象尚无来源 | 允许暂存，不伪造证据；预算／价格未知保留缺口 | 指定别名无来源正例通过；真实三例均保留价格缺口，未填写当前价 |
| D10 理由与维度口径 | 新增／更新记录须有非空理由、适用说明与 basis | 6 个空白／缺失参数用例通过，错误码命中目标规则 |
| D11 候选不足 | 允许少于目标，最终说明缺口，不凑数 | 真实笔记本与指定名单各保留 1 款，均记录研究级短缺；未生成替代产品 |
| D12 检索故障与工具缺失 | 可以保存缺口，不制造产品或断言市场不存在产品 | empty／error／unavailable 三例通过，products 与 sources 计数保持 0 |
| D13 不可信来源 | 原文保留、保留标签只在模型请求副本中中和，不进入系统指令 | 原有来源标签回归与新指引通道检查通过；未据此宣称已解决自然语言提示注入，未单独进行真实模型攻击评测 |
| D14 确认与新文字 | 未确认拦截工具；新普通文字使确认失效 | 原范围／接线回归通过；新图在确认前检索记录为空 |
| D15 研究／范围／revision 及混合批次 | 错版本、错研究、混合或多写不推进数据 | 原数据／Gateway 边界回归通过；规划沿用相同执行边界 |
| D16 权限、磁盘失败与取消 | 拒绝后不写；取消后的晚到文件不自动成为当前结果 | 原数据真实文件／权限／取消回归通过；未放宽或旁路原处理器 |
| D17 SQLite 关闭重开 | 两种 checkpoint 模式保留候选来源和规划版本 | 新增 full／delta 真关闭重开、重新确认及回读通过，未用 JSON 往返代替 |
| D18 原工厂／worker／HTTP／SSE | 真实链路保存索引、流出状态，刷新与事件历史可恢复 | full／delta 两例通过，读到 discovery_source_ids 与同一结果索引 |
| D19 用户／Thread／Agent、历史和分支隔离 | 不继承旧确认或旧结果，不跨用户读取 | 原范围、数据与 HTTP 回归通过 |
| D20 兼容与入口一致性 | 旧快照原哈希可读；普通 Agent 不注入；内嵌入口同指引 | 冻结旧字节加载与后续缺口写入通过；普通请求与两种 Gateway fixture 下的内嵌工厂检查通过 |
| IO01 规划异步文件边界 | 实际图保存／回读不在事件循环执行阻塞文件 I/O | 新增 full／delta 2 项通过；开发后严格全量 148 passed／1 skipped |
| Q01 首轮手机理由审核 | 数字必须受对应产品来源支持 | **发现不合格：** 理由写入 5120mAh，原文为 5000mAh；基础结构断言未发现，随后补入质量断言 |
| Q02 首轮笔记本缺口审核 | 不捏造确认范围里不存在的内存要求 | **发现不合格：** 缺口声称原始意图要求 32GB；随后补入固定样例质量断言 |
| Q03 首轮指定名单 | 不补入外部对象，排除二手指定对象，说明数量不足 | 基础断言及加强后的旧轨迹回放通过 |
| Q04 第二轮真实模型 | 加强理由约束后仍应在测试保护内保存规划 | 手机／笔记本通过；指定名单因反复提交非法 claims／citations 未交付，触发测试图递归上限，记为失败 |
| Q05 最后一轮真实模型 | 仅保存本阶段规划集合，满足候选、用途、来源与缺口要求 | **3/3 通过**，均无工具错误，范围未被改写；逐项审查理由、维度、缺口和最终文字，未再观察到 Q01／Q02 错误 |

## 2. 复现、红灯与修复记录

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志 |
| --- | --- | --- | --- | --- |
| 原图确认 2 款后提交 3 款；公开规则调用 | 原图成功保存 revision=1；规划规则模块尚不存在 | 新增纯检查并在合并后、保存前执行 | 2 项通过，超量不落盘 | count-public-red → count-green |
| 仅指定 A 提交 B；明确排除 A 后提交空白／大小写变体 | 数量检查之外无名单准入 | 对确认范围做保守名称归一和名单／排除检查 | 3 项通过 | scope-red → scope-green |
| 跨品类来源字段、别名绑定与无来源自动发现 | 新字段被拒绝，无来源自动发现未被阻止 | 增加可选绑定与来源字段、合并关系及来源有效性检查 | 8 项通过 | provenance-red → provenance-green |
| 缺失理由、空白维度说明、同一对象两个别名 | 缺少必要规划解释和去重 | 新／更新记录校验理由与维度口径；明确身份去重 | 15 项通过 | rationale-red → rationale-green |
| 捕获原研究模型请求 | 只有原范围／数据规则，缺少发现指引 | 在研究中间件注入固定指引，用户／网页保持数据通道 | 16 项通过，普通 Agent 无新增指引 | guide-red → guide-green |
| 8 组同步／异步 × 状态模式 × 品类接线 | 4 个同步用例触发已有测试 helper 的 recursion_limit=20，未容纳新增节点链；不是业务预算超限 | 新测试统一使用 64 个图节点步数；生产上限不变 | 原图组合 85 项通过 | graph-expanded → graph-corrected |
| 对已保存的首轮真实输出回放加强断言 | 结构绿但理由错误数字、缺口捏造需求 | 增加固定资料的数值／需求质量断言和两个离线评测回归；指引要求对照原文及范围 | 旧轨迹回放稳定识别 2 例失败；最终真实三例未再观察到这两种错误 | live-initial、quality-replay-red、live-final |
| 第二轮指定名单反复写入 | 将本阶段扩展为详细事实／价格抽取，未知值引用、字段或价格口径持续不合法 | 明确只提交规划集合；错误后移除不属于本阶段的 claims／citations；重复 URL 不再换词凑数。测试节点空间扩大但真实调用保护不放宽 | 最后一轮 3 例通过，均无工具错误 | live-corrected → live-final |
| 首次 Ruff | 导入排序与长行不合规范 | 只整理本轮文件导入／格式 | 全局 Ruff check／format 通过，1535 文件 | ruff-initial、ruff-final、format-final |

日志均在 `.deer-flow/local-dev/research-discovery-verification/`，同名 `.json` 保存实际命令、退出码、耗时及日志位置。前两份 draft 失败复现日志保留，但不计入新增正式用例数。

## 3. 真实 DeepSeek 的结果与用量

模型使用本机已有 `deepseek-flash`，未改密钥、模型配置或供应商。搜索和页面读取返回冻结合成资料；模型本身为真实调用，没有用预设工具调用替代决策。验证用测试图安装原研究中间件、原工具及原状态模式；原完整工厂／worker／HTTP 链路另由离线接口用例验证，不把两者混称为生产环境完整实模验收。

### 最后一轮逐例结果

| 样例 | 实际候选／排除 | 模型调用 | 工具调用 | 耗时（秒） | 输入／输出 tokens |
| --- | --- | --- | --- | --- | --- |
| 手机 | 极光 A1、长航 B2 入选；旧机 C3 因仅二手排除 | 7 | 11 | 16.30 | 61,468／3,144 |
| 笔记本不足 | 行远 L1 入选；桌面 D2 因台式机／重量、性能 L3 因重量排除；记录缺 1 款 | 7 | 9 | 18.28 | 62,083／3,295 |
| 仅指定名单 | 极光 A1 入选；旧机 C3 排除；不补入长航 B2；记录缺 1 款 | 6 | 7 | 12.19 | 48,860／2,107 |

最后一轮共 20 次模型调用、27 次工具调用，172,411 输入／8,546 输出，共 **180,957 tokens**；pytest 总耗时 49.90 秒（含准备和断言）。来源元数据、理由、维度、缺口、最终说明与实际调用逐项核对，三例均保持完整提供的 scope 不变，没有当前价格事实或报告完成声明。只读轨迹审查另确认：抓取 URL 在此前搜索结果中出现，保存的来源正文与实际返回文本相同，三例通过，日志 final-trace-audit；这不将模型填写来源提升为通用程序认证。

不能只报告最后成功轮：首轮 20 次模型调用／194,489 tokens，第二轮 25 次／290,348 tokens，最后一轮 20 次／180,957 tokens，合计 **65 次／665,794 tokens**。另有独立 READY 连通性检查 1 次、14 tokens；本次已记录合计为 **66 次／665,808 tokens**。数量依据保留 AIMessage 的 usage_metadata 汇总，不是供应商账单；没有计费单价，不推算金额。

原始业务轨迹分别位于 `live-initial/`、`live-corrected/`、`live-final/`，每目录包含 phone、laptop-shortage、named-only JSON。失败轮不覆盖、不删除。每例保护：10 次模型、12 次工具、180 秒总时限、请求 45 秒超时、每次最多 3,000 输出 tokens，供应商不自动重试。

**结论边界：** 最后三例通过只证明当前代码、指引和模型在这些冻结资料下的行为；实际已见过语义错误和重试失败，不能给出整体稳定性、全网召回率或生产可用率。没有联网核实真实产品、当前价格或站点可达性；没有创建本机持久化专用 Agent 实例；完整采集、预算停止、报告和面板继续按后续板块实施。

## 4. 回归与检查汇总

| 检查 | 实际结果 | 退出码／说明 |
| --- | --- | --- |
| 开发前默认离线分片 1 | 8,531 passed／190 skipped／1 failed | 1；扩展超时日志等级断言失败 |
| 开发前默认离线分片 2 | 8,544 passed／179 skipped／1 failed | 1；ACP 子进程超时用例失败 |
| 开发前严格 I/O | 146 passed／1 skipped，33.54 秒 | 0 |
| 最终研究定向组合 | 269 passed，25.58 秒 | 0；新增离线 54 项，原研究回归 215 项 |
| 新严格规划用例 | 2 passed，4.52 秒 | 0 |
| 开发后严格 I/O 全量 | 148 passed／1 skipped，25.97 秒 | 0 |
| 真实模型最后一轮 | 3 passed，49.90 秒 | 0；历史失败另列 |
| 开发后默认离线分片 1 | 8,563 passed／185 skipped／1 failed，634.08 秒 | 1；与开发前同名的扩展超时日志等级断言失败 |
| 开发后默认离线分片 2 | 8,566 passed／184 skipped／1 failed，608.60 秒 | 1；与开发前同名的 ACP 子进程超时失败 |
| 全局 Ruff check／format | 通过，1535 文件格式正确 | 各退出 0 |
| Agent guidance | 0 errors／1 warning，最长有效链 97,172 字节 | 0；未改阈值或豁免 |
| 最终文档链接／diff | 9 个 UTF-8 文档、89 个本地链接通过；已审查最终业务及新增文件 diff，空白检查通过 | 检查输出及 doc-links-final 日志；未提交推送 |

开发前两进程输出合计 17,075 passed／369 skipped／2 failed；每个进程另含同样的 6 个收集阶段跳过，剔除这 12 次非选中事件后：**选中 17,434 项，17,075 passed／357 skipped／2 failed**。开发后同口径为 **选中 17,488 项，17,129 passed／357 skipped／2 failed**，选中数量增加 54 项，与新增离线用例一致。开发后两进程原始 skipped 合计也是 369，包含重复收集事件。不将跳过视为通过，不把重复收集跳过累计为独立测试；未因已知失败删除或过滤任何默认用例。

## 5. 环境准备错误与开发前失败（单列）

| 项目 | 实际观察 | 处理及边界 |
| --- | --- | --- |
| 沙箱存储组合 | 54 passed／9 setup errors；WinError 5，不能访问正常 pytest 临时目录 | 宿主同参数复测 63 passed；9 个准备失败不计为通过，未改 ACL 或防护 |
| 沙箱首次纯规则复现的缓存 | pytest 无法创建缓存，并留下两个本轮临时缓存目录 | 业务失败原因另有明确断言；本轮目录已核对路径和非重定向属性后清理，保留已有缓存 |
| 开发前扩展超时日志 | 预期 WARNING，实际 ERROR，开发后全量仍同名失败 | 独立复测 1 passed；未定位整套下失败根因，未改扩展代码，不归因于本次研究修改 |
| 开发前 ACP 子进程超时 | 预期包含 timed out，实际空错误文本，开发后全量仍同名失败 | 独立复测仍 1 failed／18 deselected；修改研究代码前已复现，保留失败证据，未顺手修改 ACP 模块 |

全量与异步图在宿主运行，使用现有 backend 虚拟环境，保持 `-B`／`PYTHONDONTWRITEBYTECODE=1`、UTF-8、已有 uv PATH 和相关 `UV_NO_SYNC=1` 环境。没有停用户服务、启动 Docker、修改密钥或关闭安全软件。

## 6. 实际命令与复核方式

原始命令由忽略目录中的 check.py 包装，JSON 元数据记录的是实际 Python／pytest 子进程退出码，不用外层 shell 成功代替测试成功。核心参数（工作目录 backend）如下：

```text
python -B -m pytest -m "not live" --ignore=tests/blocking_io --splits 2 --group 1 --splitting-algorithm least_duration --durations-path=.test_durations tests/ -q --tb=short
python -B -m pytest -m "not live" --ignore=tests/blocking_io --splits 2 --group 2 --splitting-algorithm least_duration --durations-path=.test_durations tests/ -q --tb=short
python -B -m pytest tests/blocking_io -q --tb=short
python -B -m pytest tests/test_research_scope.py tests/test_research_agent_integration.py tests/test_research_gateway_boundary.py tests/test_research_gateway_http.py tests/test_research_data.py tests/test_research_storage.py tests/test_research_data_integration.py tests/test_research_data_http.py tests/test_research_planning.py tests/test_research_planning_integration.py tests/test_harness_boundary.py -q --tb=short -p no:cacheprovider
python -B -m pytest tests/test_research_planning_live.py -q --tb=short -p no:cacheprovider
python -B -m ruff check .
python -B -m ruff format --check .
```

真实模型命令仅在显式设置 `DEER_FLOW_RUN_LIVE_TESTS=1` 时执行，输出目录与保护详见 [实现说明](RESEARCH_DISCOVERY.md)。两个离线分片错开收集，沿用仓库对固定 CaseProbe 临时文件的限制。代码与测试结果均对应本轮工作树；没有提交或推送。

## 7. 两项失败的专项修复（2026-10-20，用户追加要求）

本节是第 4、5 节之后的修复记录；保留之前全部失败日志、原测试及原断言，没有通过删除、跳过用例或放宽时限来过关。本轮没有重新调用真实模型或付费 API。

| 原失败／新增回归 | 定位证据与根因 | 最小修复 | 定向重试 |
| --- | --- | --- | --- |
| `test_budget_exhaustion_mid_hook_logs_a_warning_not_a_traceback` | asyncio 允许计时器在一个时钟分辨率内提前触发；事后比较 `loop.time() >= deadline` 会把预算超时误判为扩展自身异常 | 使用 `asyncio.timeout_at(...).expired()` 判断来源，触发后耗尽共享预算，后续扩展跳过；保留扩展自身 TimeoutError 的 ERROR 和主机取消传播 | 原测试保留；生命周期组合 15 passed |
| 新增 `test_budget_timeout_with_early_timer_still_warns_and_skips_successors` | 模拟粗时钟分辨率并主动让出事件循环；修改前实现同时误记 ERROR、继续执行后继扩展 | 与上行共享修复；新增用例保留在原生命周期测试文件 | 原实现 1 failed，修复后通过 |
| `test_invoke_acp_agent_times_out_and_kills_hung_subprocess[asyncio]` | 完整异常栈落在 `asyncio.create_subprocess_exec`，类型为字符串为空的 `NotImplementedError`；尚未进入 ACP 握手。仓库 `backend/sitecustomize.py` 强制全进程使用不支持子进程的 Windows Selector 循环 | 移除该强制覆盖，恢复 Python 原生 Windows 事件循环；没有改 ACP prompt 超时逻辑或测试时限 | 原真实子进程测试原样通过；ACP／配置／严格 I/O 组合 38 passed |

相邻通知调用方（任务、子 Agent、系统模型、compaction、Gateway 清理）与 ACP 组合 **123 passed**；最终生命周期组合 **15 passed**。本轮完整重试结果如下，均为实际 pytest 子进程退出 0：

| 检查 | 实际结果 | 耗时（pytest） |
| --- | --- | --- |
| 默认离线分片 1 | 8,564 passed／186 skipped，无失败 | 724.16 秒 |
| 默认离线分片 2 | 8,568 passed／183 skipped，无失败 | 714.73 秒 |
| 严格 I/O 全集 | 148 passed／1 skipped | 27.08 秒 |
| 全局 Ruff check／format | 通过，1534 文件格式正确 | 各退出 0 |
| Agent guidance | 0 errors／4 warnings，最长链 97,334 字节，低于 98,304 硬上限 | 退出 0，未改阈值或豁免 |

两分片原始合计 17,132 passed／369 skipped；剔除每进程相同的 6 项收集阶段跳过后，**共选中 17,489 项：17,132 passed／357 skipped／0 failed**。比修复前新增 1 项保留的确定性回归；另外两项由失败转通过，没有删除或过滤任何默认用例。跳过不计通过。两个原失败函数的源码与 HEAD 完全一致，冻结旧 JSON 哈希仍一致；最终 UTF-8／本地链接和 diff 检查通过。

事件循环默认变更对新启动的 Python 进程生效；本轮未重启用户正在运行的 Gateway，也未验证真实站点或价格。本轮不涉及新的真实模型质量结论。

本轮日志位于 `.deer-flow/local-dev/research-discovery-verification/`，使用独立 `timeoutfix-*` 标签。原 `before-*`／`after-*` 及真实模型失败轨迹不覆盖：

- `timeoutfix-acp-red-trace.log`：原 ACP 测试失败及完整根因栈；首次调试插件导入错误另存 `timeoutfix-acp-red.log`，不计业务测试结果。
- `timeoutfix-extension-red.log`、`timeoutfix-extension-red-deterministic.log`：新增回归在原实现上的红灯；后者只在独立测试进程装入修改前函数，不改运行中的生产文件。
- `timeoutfix-extension-final.log`、`timeoutfix-acp-green.log`、`timeoutfix-related.log`：定向绿灯。
- `timeoutfix-after-shard-1.log`／`timeoutfix-after-shard-2.log`、`timeoutfix-after-blocking.log`：本轮完整重试；各有 JSON 命令、真实退出码与耗时。
