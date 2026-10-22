# 板块五测试报告

**2026-10-22收尾（最新）：** 已知官网购买链接辅助的真实模型四配置标价场景通过：15次模型、14次工具、54.2秒、271,749 tokens。四条list价格Claim分别绑定正确配置，保存选中状态与金额的八条精确引用，并回读评估；四张截图已核对。新增选中状态和异步弹窗回归先红后绿，相关专项156 passed；严格I/O修改前151 passed／1 skipped，修改后151 passed／1 skipped；前端19 passed、ESLint／TypeScript退出0，独立原面板合成E2E 1 passed。默认全集与完整红绿记录见[收尾验收第11节](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md#11-2026-10-22第五阶段收尾官网四配置实模验证)。按官网公开标价范围收尾，不升级为开放搜索发现、任意站点稳定性或真实账号验收。下方为历史结果，模型总数以第11节为准。

最终默认离线两个分片原始17,198 passed／356选中skipped／41 failed：40项测试PATH漏uv，修正PATH后相关完整文件219 passed／13 skipped；另1项临时目录收集偶发，原文件串行7 passed／4 skipped。41项原失败均补验通过，去重后17,239已通过／356选中跳过，不将补验重复相加或宣称单轮全绿。Ruff全量check／format通过（1547文件），指南29份／0 errors／0 warnings；失败轮、分母和限制见上述第11节。

**2026-10-21最终续作结果（优先于下方历史）：** 后端相关组合**197 passed（76.75秒）**，严格I/O **151 passed／1 skipped（27.87秒）**；前端browser-view **19 passed**，完整ESLint／TypeScript退出0；原dev脚本及Next rewrites的完整合成登录态E2E **1 passed（19.2秒）**。StrictMode多余连接及target=_blank返回旧快照修复均先红后绿，后端全量Ruff check／format通过（1547文件），指南29份／0 errors／0 warnings。较早17,234项全集不覆盖本轮最终修复，各轮不累加。

真实模型新增受控单配置轮上限8次／90秒，实际8次调用、112,842 tokens、25.42秒；第9次尝试在请求前拒绝。累计**47次／717,654 tokens**，停止追加。该轮未保存价格，但把实际c1页面的缺货Claim绑定到c2，语义失败保留；popup同步随后修复，仅做无模型官网复核，不能称模型链通过。用户最新只需官网标价、不核查地区缺货；四配置3599／3899／4099／4599元已有逐项官网证据，可以交付本次价格信息。详见[验收第10节](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md)。

以下第8、9节摘要是此前各轮，不作为最新模型总数或完整Next结论。

2026-10-21续作结果见[真实页面验收记录](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md)第8节：最终六秒版本195项专项通过、严格I/O151 passed／1 skipped，面板合成联调1 passed、前端浏览器18 passed及完整静态检查退出0；较早默认全集17,234 passed／362 skipped不覆盖最后等待小修。真实模型累计39次／604,812 tokens，四配置仅取得两条带条件的公开标价观察；官网动态正文仍不稳定，另外两配置、卖家、优惠及完整Next代理登录链仍未验收。下文历史失败全部保留，不因本轮专项通过而变成业务全部通过。

登录恢复后的无模型补证见同一验收记录第9节：沿实际官网购买链接20618，两轮逐项选择四配置取得3599／3899／4099／4599元，第二轮黑色选中态、截图、缺货及登录提示均核对；原“另外两配置未知”仍是第8节模型轮的历史结果。公开标价资料已补齐，但默认北京地区缺货、登录后到手价及模型自主端到端链尚未验证；本轮未修改生产代码、未追加模型或重跑上述自动测试。

日期：2026-10-20。实现说明见 [证据采集说明](RESEARCH_EVIDENCE.md)，计划见 [E01–E22 任务书](RESEARCH_EVIDENCE_PLAN.md)。日志根目录为 `.deer-flow/local-dev/research-evidence-verification/`；失败轮不覆盖。下面先列实际用例，再列红绿证据，三个验证边界分别报告。

同日追加的 [小米15真实电商验收](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md) **未通过**：自主搜索未取得可用来源；固定链接诊断确认两条京东HTML有目标价格，但当前Readability提取丢失价格区块，另有空壳及Reader 403。生产代码尚未修复，下列离线／冻结资料通过不能替代这次业务失败。

## 1. 用例、预期与实际

| 场景 | 预期 | 实际结果与边界 |
| --- | --- | --- |
| E01 手机规格／评测 | 分开事实、观点与引用，不推广样本 | 原图与真实 DeepSeek 保存防抖事实、单次日间评测观点、标称电池容量；未将观点推广为满意度。用户评价类型沿用契约，未以本轮三例证明普遍用户评价质量 |
| E02 笔记本不同配置 | 不把低配价或高配性能绑定目标配置 | 首轮实模发现错绑定；加强指引后目标配置未知，其他变体另建配置并重采集。最终数值保护轮保留 c1 重量与 c2 报价，评测线索未采集则留缺口 |
| E03 旧首发价＋销售页 | 主动搜索销售渠道，历史与报价分开 | 最终实模保留3999 launch与3299 public_offer，并引用不同实际采集来源；不称库存／结算已核实 |
| E04／E06 不可用／条件价 | 不猜无条件金额，保留缺口 | HTTP样本429保存明确失败；实模2999保持member和补贴资格未知。各轮并不都会读取全部返回链接，最终轮把未读取的失败线索明确留在线索层 |
| E05 伪造或自填来源 | 不得冒充实际捕获支持新价格 | 原图拒绝伪造capture，纯规则拒绝无采集价格、改正文／类型／适用范围／去掉capture |
| E07／E08 价格口径与时间 | 二手／历史／条件／市场不符分别表达 | 参数化规则保留basis，地区／时点不符降为未核实；新增错误时间或无摘录金额拒绝。起售价与配置语义不由程序通用解析 |
| E09 长中文页面尾部 | 4096字符后证据可经分页读取，片段非独立来源 | 真实Readability＋冻结HTTP，尾部3299可读取；组ID、片段位置、时区正确 |
| E10 容量 | 有界流、正文截断、保持原存储阈值 | 流超限在第三个8KiB chunk停止；中文正文128KiB封顶且各Source≤8KiB；原2MiB快照拒绝测试回归 |
| E11 超时／429／空提取 | 有可知的失败原因，不泄漏错误正文 | 显式错误码测试通过；新增永不结束流的总时限红绿。DDG空结果／异常仍无法区分 |
| E12 数值与单位 | 明确换算保留原值，其他口径不强比 | g/kg、MB/GB、MiB/GiB成功；mAh/Wh、GB/GiB等拒绝。额外复现隐式1TB→1000GB，新增采集数值必须有摘录／支持转换依据检查 |
| E13 冲突与纠错 | 保留两条可比较矛盾，不能覆盖 | 同条件不同事实必须Conflict；已有已知Claim和原Citation不可替换。自然语言同义条件与转载独立性仍属人工判断 |
| E14 摘录存在但语义不支持 | 结构通过不能当质量通过 | “公开售价并非3299”仍能命中数字检查；测试明确保留semantic_review_required，无verified字段。这是已知语义边界，未宣称自动解决 |
| E15 来源注入 | 保留原文，仅模型副本中和标签 | 实际采集含转义system标签，存储原文可回读；模型副本为转义文本，未进入系统指引。单例不证明全面提示注入防护 |
| E16／E17 确认／版本／授权／混批 | 请求前阻止，无网络与索引推进 | 旧revision、研究ID、范围版本、缺产品／错配置、猜URL、未确认、Guardrail拒绝、混批／不完整批次均覆盖 |
| E18 保存失败／取消 | 不丢旧结果，按原恢复协议处理 | 磁盘替换故障和网络取消保留旧pointer；既有文件worker取消与未引用快照回归。新增full/delta真实saver.put故障：已提交索引保留revision1，pending writes已有引用时get_state可投影revision2，其实际快照可校验读取；Run抛错，不等于成功提交 |
| E19 原链路恢复 | full／delta跨关闭重开、HTTP/SSE一致 | 新采集与价格在SQLite真正关闭重开后恢复；原工厂/worker HTTP/SSE、刷新与事件历史、内嵌客户端确认门槛通过 |
| E20／E21 隔离／旧JSON／普通入口 | 继承原生命周期、兼容旧文件 | 原跨用户、历史、分支、普通Agent、工厂与客户端回归；冻结旧JSON原哈希保持。未建立跨研究来源复用接口 |
| E22 真实模型 | 自主查渠道、正确配置和未知，逐字段审查 | 最终数值保护轮三例自动断言通过，另人工核对数值、报价条件、配置归属与摘录。是小样本固定资料结果，不是全品类或生产稳定性保证 |

## 2. 红绿与排错证据

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志前缀 |
| --- | --- | --- | --- | --- |
| 长页尾部采集／capture保护／价格规则／原图 | 原先无采集入口、保护和评估 | 最小SourceCapture、有界适配、纯规则、原中间件接线 | 分阶段定向通过 | collection-*、evidence-*、price-*、integration-* |
| 单位原值字段 | Claim不接受original_value／original_unit | 可选兼容字段、显式Decimal换算检查 | 65项组合通过 | normalization-green |
| 只更新引用重指价格来源 | 没遍历引用更新，未报错 | 已知观察原Citation不可替换；校验所有受影响claims | 原负例通过 | citation-red、boundaries-green |
| 同条件矛盾、覆盖旧观察 | 缺少冲突和覆盖保护 | 新ID保留不同观察；要求显式Conflict | 22项规则组合通过 | units-conflicts-* |
| 不结束的网络流 | 只有httpx单次读等待，没有整个请求期限 | asyncio.timeout覆盖请求生命周期 | 8项采集用例通过，严格I/O回归 | total-deadline-red、后续定向 |
| 单位错误诊断 | 只给claims，模型误改所有单位 | 返回具体claim ID及维度所需单位 | 原价unit=CNY保留，错误只针对目标修正 | unit-diagnostic-red-corrected、后续定向 |
| 实模首轮三例 | 10模型保护用尽；混用维度、单位，未完成事实保存 | 独立属性维度指引；依据实际步骤扩大测试保护为20模型/24工具/180秒 | 第二轮手机两例通过 | live-round-1、live-round-2 |
| 实模笔记本错配 | 文本说低配不适用，结构却挂到c1 | 明确其他配置必须另建ID再正确采集，或目标未知 | 失败原断言保留，单例通过 | live-round-2、live-round-3-laptop |
| 恢复测试／取消测试自身问题 | 恢复用不同scope导致清空；添加函数时断言放错位置 | 恢复同范围；原断言移回所属用例，未删断言 | 真实SQLite/取消通过 | boundaries-first、evidence-focused-final、后续绿色日志 |
| 实模3例基础断言通过后人工审核 | Gap的2999写成2919；conditions的32GB写成2GB | 增加条件/缺口的固定数字质量断言及离线回归，强调所有事实文字核对 | 原产物新断言实际报错，后续重测通过 | live-final、live-quality-final |
| 人工审核隐式存储换算 | 原文1TB被填1000GB且未保留原值 | 先补失败测试，再要求采集数值出现在摘录或给出支持的换算依据 | 57项相关组合及三例实模通过 | numeric-fact-red、numeric-fact-green、live-numeric-final |
| 开发后全量PAT时间断言 | 两次时间戳相同，测试断言third!=first；本块未改该模块 | 保留测试与日志，原文件单独复跑；没有顺手改认证代码 | 独立14 passed，根因未稳定复现；最终全量另列 | after-host-shard-2、pat-isolated |
| checkpoint故障测试 | 原断言误以为get_state只显示已提交checkpoint，实际框架会应用已持久化pending writes | 分开断言已提交索引未变、pending引用存在、恢复投影与真实快照一致；未改原框架 | full/delta 2 passed；仅落盘但未被引用的孤儿文件仍不晋升 | checkpoint-fault、checkpoint-fault-corrected |

环境错误单列：沙箱默认临时目录曾WinError 5，属于setup错误；改用宿主正常pytest临时目录，防护保持开启、禁写字节码。恢复前两次collection运行在导入langchain/langgraph的autouse初始化抛MemoryError；后来原单例和29项组合通过，未删断言，未证明具体根因。与业务断言失败分开，详见collection-green／collection-green-retry／collection-resume／collection-isolated-resume及before-*日志。

## 3. 确定性验证与命令

全部使用现有backend/.venv、`-B`、UTF-8、PYTHONDONTWRITEBYTECODE=1、UV_NO_SYNC=1、正常pytest临时目录。运行器check.py记录真实子进程exit_code，不能用外层PowerShell退出成功代替pytest结果。

开发前宿主基线：两分片8564 passed/186 raw skipped与8568 passed/183 raw skipped，均退出0；**17,489项选中：17,132 passed／357 skipped／0 failed**。每进程另有相同的6项收集跳过，原始369不能当成369个独立选中跳过。严格I/O **148 passed／1 skipped**。

开发后首轮全量：8595 passed/184 raw skipped与8594 passed/185 raw skipped/1 failed；**17,547项选中：17,189 passed／357 skipped／1 failed**，PAT时间断言失败保留。该轮不含后续补测和最终数值保护，不用它冒充最终全量。

最终结果以 final-host-shard-*、after-numeric-blocking、最终Ruff日志为准；定向 focused-final 为391 passed，之后补加的注入／伪造／数值与质量检查另有57项相关组合通过，不将重叠组合相加。最终全量汇总在本报告末节更新。

复现（从仓库根运行；LABEL每次换名，不覆盖旧日志）：

```powershell
& .\backend\.venv\Scripts\python.exe -B -X utf8 .deer-flow/local-dev/research-evidence-verification/check.py LABEL -m pytest tests/test_research_evidence.py tests/test_research_collection.py tests/test_research_evidence_integration.py tests/test_research_evidence_http.py tests/test_research_evidence_quality.py -q --tb=short -p no:cacheprovider
```

默认离线命令由同一运行器执行 `-m pytest -m "not live" --ignore=tests/blocking_io --splits 2 --group 1`（另一个group=2）`--splitting-algorithm least_duration --durations-path=.test_durations tests/ -q --tb=short -p no:cacheprovider`。两分片收集错开。严格I/O为 `-m pytest tests/blocking_io -q --tb=short -p no:cacheprovider`。

本块无前端改动，未运行新的前端UI测试；没有构建Docker、重启用户服务、Git提交推送或更改密钥。

## 4. 真实DeepSeek与人工审核

测试为test_research_evidence_live.py，显式DEER_FLOW_RUN_LIVE_TESTS=1。使用原已配置DeepSeek、原研究中间件/工具图；scope确认与候选计划经真实工具链预置，**所有第五阶段工具选择与提取由真实模型自主完成**。替换的只有web_search返回与Reader HTTP传输，不返回预先填好的claims。时间戳、提取器、文件、校验和回读均实际执行。

单请求45秒、供应商0次自动重试；初轮10模型/12工具/180秒，实际达到调用上限后调整到20模型/24工具/180秒。不是产品研究预算，也不证明已能在生产自动停止。每轮保留messages、web_calls、完整result、步数、耗时及模型usage；失败轮也计入用量。

| 最终数值保护轮 | 人工核对结果 |
| --- | --- |
| 旧首发→公开报价 | 3999首发/3299公开报价分开；c1配置、seller、优惠条件与引用支持；标称容量不充当续航实测，独立评测为opinion |
| 条件价/不可用 | 2999为member，会员与地区补贴资格未知；普通价保持缺口；未读取的渠道线索明确未采集，没有虚构实际429尝试 |
| 笔记本错配 | c1 16GB/512GB重1.35kg；c2 8GB/256GB报价3999另建配置并重采；c1价格未知；32GB/1TB性能未采集时不保存成c1事实 |

最后一轮3 passed（69.25秒pytest耗时）；并未重复足够次数来估计稳定成功率。历史自动3 passed但人工审核失败的live-final和live-quality-final仍明确记录，不能算质量合格轮或删除历史。三类来源的“类型”与配置仍有模型声明成分，所有结论都保留语义复核要求。

最终轮为32次完成模型调用、29次工具调用，input379,538／output10,059，共389,597 tokens。全部16个场景运行（含失败和人工审核不合格轮）共195次模型尝试、192次完成、2,504,482 tokens，来自保存消息的usage_metadata合计，不是计费金额或供应商账单；测试保护在调用前阻止的尝试没有供应商usage。逐轮明细见live-usage-summary.json。

## 5. 公开来源探测

三次定向DDG查询均无结果输出；旧helper混合空与异常，故只记“无结果或搜索异常”，不推断市场无产品或具体网络原因。随后对固定官方入口、官方商店、评测目录各执行一次采集，保留实际结果。

| URL | 第二次有完整产物的实际提取 | 结论 |
| --- | --- | --- |
| https://www.apple.com/cn/iphone/ | available，1393字符 | 取得产品入口与生态描述，不是完整具体型号规格证明 |
| https://www.apple.com.cn/shop/buy-iphone | available，1532字符 | 主要为换购/分期条款，未取得指定配置SKU报价；不能声称已核实当前价格，也不能认定原站页面无价格 |
| https://www.rtings.com/laptop/reviews | available，199字符 | 取得评测目录摘要，不是具体型号评测全文 |

第一次三个URL的摘要日志保留；原文产物与运行器元数据重名而被覆盖，修正文件名后只重复同三个URL一次。因此共3次搜索、6次固定读取；第二次完整产物为direct-public-probe-artifact.json，另有两轮独立日志/元数据。不运行开放式自主研究，不登录、购买或猜测商品SKU。真实可达性不能被冻结模型测试代替，当前价格采集质量仍受页面提取与站点支持限制。

## 6. 兼容与未覆盖事项

旧JSON原字节/哈希、既有文件隔离、普通Agent、工具权限、原分页与full/delta接口保持兼容。原普通批次仍可保存非价格未绑定观察，并明确标为unbound；新价格强制采集。未将所有非价格新写入一律禁止，与任务书中的更强门槛存在差异，详见实现说明。

没有宣称消除任意语义幻觉、验证全部商家、完整正文始终可提取、保证“当前可成交价”、执行研究预算、生成报告或研究面板。checkpoint故障已按原pending-writes协议补测，不能笼统写成失败后投影必不变。用户评价质量、开放网络完整任务、重复成本与成功率仍需后续补充。

## 7. 最终回归与交付检查

最终默认离线两分片均退出0，使用最新数值保护实现。按实际选中用例汇总为 **17,556项：17,199 passed／357 skipped／0 failed**。跳过项不计通过；真实模型和严格I/O分别报告。

| 验证 | 结果 | pytest耗时／运行器耗时 | 证据 |
| --- | --- | --- | --- |
| 最终默认离线分片1 | 8598 passed／185 raw skipped，exit 0 | 741.09秒／750.89秒 | final-host-shard-1.log／.json |
| 最终默认离线分片2 | 8601 passed／184 raw skipped，exit 0 | 748.39秒／767.64秒 | final-host-shard-2.log／.json |
| 最终严格I/O全量 | 150 passed／1 skipped，exit 0 | 22.82秒／26.06秒 | after-numeric-blocking.log／.json |
| checkpoint提交故障补测 | full／delta共2 passed／22 deselected，exit 0 | 单独运行，不并入全量分母 | checkpoint-fault-corrected.log／.json |
| 全局Ruff检查／格式 | check通过；1543文件已符合格式 | exit 0 | ruff-verified、format-verified |
| Agent指南 | 0 errors／4 warnings；最长继承链97,949字节 | 未改阈值或豁免 | guidance.log／.json |

两个分片各含相同的6项收集阶段跳过，原始185＋184＝369；扣除两次收集跳过后，实际选中用例跳过为179＋178＝357。通过为8598＋8601＝17,199，选中分母为17,199＋357＝17,556。两个checkpoint故障用例在本轮全量收集后增加，已独立补测，不能声称本轮全量包含它们。

最终回归包括原PAT用例，本轮未再失败；首轮after-host-shard-2中的时间断言失败及两次导入MemoryError仍保留，根因未稳定复现，没有据本轮绿灯宣称已修复。此前真实模型的失败／人工审核不合格轮也保留，最终接受的是live-numeric-final三例小样本。

交付检查：本轮涉及的文档本地链接前次126项、收尾再次60项均无缺失（范围不同，不相加）；28个开发前脏文件逐项核对，无非预期变化。冻结旧JSON仍为SHA256 `506f60fab96c30875be1a54ab0cc29eb46477cec66cb7f12f3c595eeda860e69`。会话差异与最终Git diff已检查，`git diff --check`通过；CRLF转LF提示不计业务失败。收尾证据见closeout-checks.json及session-final.diff。没有提交推送、修改凭据、重启用户服务或开始第六阶段。

## 8. 真实电商追加失败

见 [真实电商验收报告](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md)。本次真实模型4次调用、48,068 tokens，原图3次搜索、0次采集、0价格；另外2次定向搜索和6次固定链接采集诊断单列。发现文章提取遗漏商品价格，尚未修改生产代码；当前板块5核心实现不等于真实价格业务已完成，下一步先修复该缺陷再复测。
