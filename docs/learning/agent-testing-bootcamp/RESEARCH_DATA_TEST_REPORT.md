# 板块三：研究数据与证据契约测试报告

日期：2026-10-19。环境：Windows、Python 3.12、既有 backend/.venv。不调用真实模型、不进行真实产品或价格研究。日志保存在忽略目录 `.deer-flow/local-dev/research-data-verification/`。

## 原实现验收结果（历史记录）

| 测试用例／检查 | 预期结果 | 实际结果 |
| --- | --- | --- |
| 开发前严格 I/O 全量 | 已有用例无失败；平台不适用项明确跳过 | **145 passed / 1 skipped**，19.39 秒 |
| 开发前默认离线分片 1（错开收集后重跑） | 已有离线用例无失败，正常结束 | **8504 passed / 183 skipped**，767.32 秒，退出 0 |
| 开发前默认离线分片 2 | 已有离线用例无失败，正常结束 | **8502 passed / 186 skipped**，703.02 秒，退出 0 |
| 最终定向组合：板块 1–3、原图、HTTP/SSE 与新增严格 I/O | 新增场景及所选相邻回归全部通过 | **210 passed**，22.46 秒，退出 0 |
| 开发后严格 I/O 全量 | 新增文件读写不阻塞事件循环，已有用例无回归失败 | **146 passed / 1 skipped**，27.34 秒，退出 0 |
| 后端全局 Ruff | 无 lint 错误，无待格式化文件 | `ruff check .` 通过；`ruff format --check .`：**1529 files already formatted**，均退出 0 |
| 开发后默认离线分片 1 | 新增及已有离线用例无失败，正常结束 | **8526 passed / 193 skipped**，664.99 秒，退出 0 |
| 开发后默认离线分片 2 | 新增及已有离线用例无失败，正常结束 | **8545 passed / 176 skipped**，665.88 秒，退出 0 |

开发前两分片共选中 **17,363 项：17,006 passed / 357 skipped / 0 failed**。开发后共选中 **17,428 项：17,071 passed / 357 skipped / 0 failed**，增加 65 个默认离线用例；另一个新用例位于独立严格 I/O 集合。每个分片进程的汇总都包含相同的 6 项收集阶段跳过，故不能直接将两份 skipped 相加：开发后 193 + 176 − 12 = 357 个选中用例跳过；另有 6 个共同收集阶段跳过，不重复累计。跳过项不计为通过。

原实现新增 **66 个用例**：契约 27、快照 8、图与生命周期 24、原工厂 HTTP/SSE／内嵌客户端 6、严格 I/O 1。原定向组合还包含原范围 95 项、原接线／HTTP／入口边界 49 项。它们是确定性自动化验证，不是 210 项真实模型评测。

## 两项覆盖细节补测（2026-10-19）

本次新增 **5 个测试节点**：失败来源补齐原因后仍被引用 1 项，仅研究 ID 错配在同步／异步 × full／delta 下 4 项。本块当前共 **71 项**：契约 28、快照 8、图与生命周期 28、HTTP/SSE／内嵌客户端 6、严格 I/O 1。只新增测试并修正测试替身的占位符处理，未修改生产代码。

| 测试用例／检查 | 预期结果 | 实际结果 |
| --- | --- | --- |
| 补测前契约及图测试基线 | 现有测试通过 | **51 passed**，4.23 秒；coverage-before-host.log |
| 强化旧研究 ID 负例，要求精确错误码 | 研究 ID 不符应返回 version_conflict | **1 failed / 4 passed / 19 deselected**，2.97 秒；实际返回 invalid_data，发现测试替身未替换范围占位符；coverage-placeholder-red-host.log |
| 两组独立负例及原 5 组输入负例 | 只触发目标拒绝条件，原结果与文件不发生写入副作用 | **10 passed / 46 deselected**，2.76 秒；新 5 项均通过；coverage-independent-host.log |
| 板块 1–3、原图、HTTP/SSE 与研究严格 I/O 定向回归 | 新增测试与相邻行为均通过 | **215 passed / 0 failed**，1 warning，27.83 秒，退出 0；coverage-regression-host.log |
| 严格 I/O 全量 | 文件操作及原严格检查无回归 | **146 passed / 1 skipped**，2 warnings，24.07 秒，退出 0；coverage-blocking-host.log |
| 全局 Ruff | 无 lint 或格式问题 | ruff check . 通过；ruff format --check .：**1529 files already formatted** |

本次未重跑默认离线两分片全集；上节 17,071 passed 属于原实现验收，不包含本次新增 5 项。新增独立负例首跑即通过，说明现有生产规则已能拒绝这两种输入；实际红灯来自旧测试替身，不能写成新增生产缺陷。

## 测试用例、预期结果与实际结果

下面按本块用例列出结果；参数化场景在用例名称中标明项数。项数按 pytest 展开的测试节点计算，一个函数内有多个断言仍计 1 项。原实现证据为 `final-targeted-host.log`（210 passed）；本次补测已实际重跑全部定向组合，最新结果为 `coverage-regression-host.log`（215 passed）。

### 一、研究数据契约：28 项

代码：`backend/tests/test_research_data.py`。D03–D21 对应同一个非法批次参数化测试的 19 组输入，均检查原结果未被修改。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| D01 手机样本装载与 JSON 往返 | 配置、来源和关系可恢复；重量为 Decimal，未知价格为 null | 通过；恢复后与保存结果相等，重量为 Decimal("190")，价格为 None，revision=1 |
| D02 笔记本样本装载与 JSON 往返 | 同一套契约承载另一品类，不使用手机专属结构 | 通过；重量为 Decimal("1.4")，未知价格为 None，原空结果仍为 revision=0 |
| D03 事实关联不存在的配置 | 拒绝批次，不修改原结果 | 通过；抛出校验异常，原 revision=0、claims 为空 |
| D04 事实关联不存在的维度 | 拒绝悬空维度引用 | 通过；拒绝批次，原结果未变 |
| D05 事实单位与维度单位不一致 | 拒绝把 kg 与该维度的 g 混用 | 通过；拒绝单位错配，原结果未变 |
| D06 用 bool 充当事实数值 | 拒绝 True，不能将其视作 1 | 通过；拒绝批次，原结果未变 |
| D07 事实值为 NaN | 拒绝非有限数值 | 通过；拒绝批次，原结果未变 |
| D08 事实值为 Infinity | 拒绝非有限数值字符串 | 通过；拒绝批次，原结果未变 |
| D09 用空字符串充当事实值 | 拒绝，未知值须使用 null 与原因 | 通过；拒绝批次，原结果未变 |
| D10 模型提交 verified 字段 | 拒绝模型自行增加核实标记 | 通过；额外字段被拒绝，原结果未变 |
| D11 未知值缺少 missing_reason | 拒绝不说明原因的未知值 | 通过；拒绝批次，原结果未变 |
| D12 采集时间没有时区 | 拒绝无时区时间 | 通过；拒绝批次，原结果未变 |
| D13 用 bool 充当采集时间 | 拒绝布尔时间输入 | 通过；拒绝批次，原结果未变 |
| D14 来源使用 file URL | 拒绝非 HTTP(S) 来源 URL | 通过；file:///private 被拒绝，未发生文件读取 |
| D15 来源只适用于另一配置 | 拒绝将 other 配置来源引用到 base 配置事实 | 通过；拒绝错配引用，原结果未变 |
| D16 来源关联不存在的产品 | 拒绝悬空产品引用 | 通过；拒绝批次，原结果未变 |
| D17 来源标 failed 但未提供失败原因 | 拒绝不完整的失败来源记录 | 通过；拒绝批次，原结果未变；补齐原因后的独立引用负例已另由 D28 验证 |
| D18 引用摘录不在来源文本中 | 拒绝无法在保存正文中找到的摘录 | 通过；拒绝批次，原结果未变 |
| D19 引用摘录长度为 4,001 字符 | 拒绝超过 4,000 字符上限的引用 | 通过；超限引用被拒绝，原结果未变 |
| D20 引用关联不存在的事实 | 拒绝悬空事实引用 | 通过；拒绝批次，原结果未变 |
| D21 产品 ID 包含 ../escape | 拒绝不合法的标识 | 通过；ID 校验拒绝，原结果未变 |
| D22 重复 ID 与已知事实缺少引用 | 两种非法输入都应被拒绝 | 通过；重复产品 ID 和缺少直接引用分别触发校验异常 |
| D23 零值、历史首发价及价格口径 | 0 是已知值；历史价格保持 launch；缺少价格元数据时拒绝 | 通过；价格为 Decimal("0")、basis=launch、missing_reason=None；删除 price 后被拒绝 |
| D24 冲突观察与推断依据 | 保留不同来源的说法，并让推断关联已有事实 | 通过；190 与 200 两条观察并存，冲突及推断均保留对应事实 ID |
| D25 更新来源与重复提交稳定 ID | 合并后重校验旧引用；失败不修改旧结果；重复 ID 不新增记录 | 通过；破坏原摘录的更新被拒绝，旧 revision=1；重复提交后仍为 1 个产品、2 条事实 |
| D26 显式产品级来源支持产品级事实 | product_wide=true 时允许不指定具体配置的事实 | 通过；事实的 configuration_id=None；只证明适用范围结构合法 |
| D27 显式产品级来源支持产品级评价 | 同样允许有引用的产品级 opinion | 通过；评价的 configuration_id=None；不证明评价语义正确 |
| D28 来源补齐失败原因、正文仍含原摘录，却继续保留既有引用 | 来源与批次本身可装载，但完整关系校验须拒绝失败来源作为直接证据；原结果不变 | 通过；仅改变 status 与 failure_reason，精确断言 unsupported_quote、字段 citations；原结果 JSON 完全未变 |

### 二、快照存储与分页：8 项

代码：`backend/tests/test_research_storage.py`。使用真实临时文件；磁盘故障在文件系统边界注入。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| S01 保存、恢复、分页及指定 ID 读取 | 快照往返一致，索引有界；两页可完整读到事实，ID 筛选正确 | 通过；恢复结果相等，索引不超过 16 KiB、claims 计数为 2；两页依次返回 190 和 null，指定 ID 返回 other 配置 |
| S02 其他归属、损坏和缺失快照 | 不能读取其他归属的数据；损坏或缺失时明确报错 | 通过；其他 Agent 被拒绝、其他用户未读到文件；篡改字节后报哈希错误，删除后报不存在 |
| S03 原子替换失败 | 新快照失败后旧快照仍可读，临时文件清理 | 通过；返回保存失败，旧结果相等，目录只保留原快照文件 |
| S04 已落盘但未被 checkpoint 引用的新快照 | 不自动提升未引用版本 | 通过；新文件为 revision=2，按原指针读取仍为 revision=1 |
| S05 标识、快照、索引及读取上限 | 拒绝路径式 ID、超限数据、非法分页和未知 ID | 通过；路径式 ID 与超限索引被拒绝，超限快照返回 snapshot_too_large，单条超限读取返回 record_too_large；负 offset 和未知 ID 报错 |
| S06 thread_id 包含 ../thread | 不允许通过线程标识逃逸目录 | 通过；返回 invalid_path |
| S07 多条大记录按字节上限分页 | 每页不超过 16 KiB，不截断或漏掉整条记录 | 通过；逐页拼接得到原产品及 long-0 至 long-4，顺序与数量一致 |
| S08 研究目录重定向到沙箱 | 识别真实目录重定向并拒绝保存 | 通过；Windows junction 返回 invalid_path，沙箱目标目录没有 JSON 快照；POSIX 路径使用符号链接分支 |

### 三、原 Agent 工具链与生命周期：28 项

代码：`backend/tests/test_research_data_integration.py`。G01、G02、G14、G20 包含参数化组合，其余每行计 1 项。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| G01 确认后写入再读取（同步／异步 × full／delta，共 4 项） | 原工具链保存并读回样本，状态具有结果版本与哈希 | 4 项通过；result.revision=1、phase=recording，读取重量为 "190"，SHA-256 长度为 64 |
| G02 guardrail 拒绝写入（同步／异步，共 2 项） | 权限拒绝后没有文件和状态写入副作用 | 2 项通过；result=None、无 JSON 快照，并产生错误工具消息 |
| G03 expected_revision=9 | 拒绝过期或错误的数据版本 | 通过；返回错误，result=None，无 JSON 快照 |
| G04 expected_revision=True | 拒绝将布尔值作为版本 | 通过；返回校验错误，result=None，无 JSON 快照 |
| G05 expected_scope_version=9 | 拒绝不匹配的范围版本 | 通过；返回错误，result=None，无 JSON 快照 |
| G06 提交其他研究标识 | 非法写入不应落盘或更新状态，并返回 version_conflict | 通过；已修正测试替身，使范围版本占位符独立替换；精确断言 version_conflict、result=None、无 JSON 快照；隔离前提的扩展测试见 G20 |
| G07 参数中夹带 user_id | 拒绝模型指定所有者 | 通过；额外字段被拒绝，result=None，无 JSON 快照 |
| G08 写入与读取同批 | 整批不执行 | 通过；无快照、result=None，读取工具未产生结果 |
| G09 同批两次写入 | 整批不执行，避免覆盖整份状态 | 通过；无快照、result=None |
| G10 范围提议与写入同批 | 整批不执行 | 通过；无快照、result=None |
| G11 同批含格式错误的写入 | 不执行格式错误的写入或同批读取 | 通过；无快照、result=None，读取工具未产生结果 |
| G12 未确认时分别尝试读与写 | 两种动作都被门槛阻止 | 通过；均产生错误工具消息，result=None，无 JSON 快照 |
| G13 新文字、同范围重确认及范围变化 | 新文字暂停准入但保留数据；重确认可读取；实质变化清空索引 | 通过；同范围保留原指针并进入 awaiting_confirmation，重确认可读；修改范围后 result=None、版本递增，旧文件仍保留 |
| G14 SQLite 关闭重开恢复（full／delta，共 2 项） | 真实关闭重开 saver 后恢复指针，重确认后读回原数据 | 2 项通过；恢复指针与已保存指针相等，后续读取重量为 "190"；未重启用户 Gateway 进程 |
| G15 来源中含伪造 system 标签 | 仅在模型请求副本中中和标签，保留存储原文 | 通过；原工具记录仍含原标签，模型收到转义标签，来源指令未进入 system 消息 |
| G16 磁盘线程已开始后取消调用 | 晚到的快照不自动推进当前结果 | 通过；等待线程完成后文件存在，但 checkpoint 中 result=None |
| G17 已有结果后重复提交旧 revision | 不覆盖已保存版本 | 通过；返回 version_conflict，当前 revision 仍为 1，读取重量为 "190"，快照仍只有 1 份 |
| G18 相同范围另开研究 | 新研究不继承旧结果指针，旧文件保留 | 通过；research_id 改变、result=None，旧快照仍有 1 份 |
| G19 工具执行中发生磁盘替换失败 | 返回可定位错误，不推进研究状态 | 通过；返回 snapshot_write_failed，result=None，无 JSON 快照 |
| G20 当前卡确认后仅研究 ID 错配（同步／异步 × full／delta，共 4 项） | 参数结构、范围版本和数据版本合法，仅研究 ID 不同；拒绝写入且无结果和文件副作用 | 4 项通过；先校验参数并断言差异仅为 expected_research_id，再精确断言 version_conflict；确认有效，当前研究 ID 与范围版本未变，result=None，无 JSON 快照 |

G06／G20 已精确断言研究 ID 错配的 version_conflict；D28 已精确断言 unsupported_quote 及 citations 字段。其余身份与版本负例仍主要检查“返回错误且无副作用”，没有逐项断言精确错误字段。生产实现对研究 ID、范围版本、数据版本不符共用 version_conflict，错误字段为 expected_revision；本次没有扩展错误字段的细分能力。

### 四、HTTP/SSE 与内嵌客户端：6 项

代码：`backend/tests/test_research_data_http.py`。每行分别在 full／delta 下执行，共 6 项；HTTP 路径使用原认证入口、工厂、worker 和真实图，模型使用替身。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| H01 状态流、刷新、事件历史与入口隔离（2 项） | SSE 与刷新状态一致；事件保存写入消息；拒绝伪造状态和其他用户访问 | 2 项通过；claims 计数为 2，刷新状态相等，读取重量为 "190"；事件含写入工具消息；客户端直接写 research 为 422，其他用户访问为 404 |
| H02 分支、历史状态更新与历史恢复（2 项） | 新分支和历史恢复不复用旧结果与确认 | 2 项通过；分支研究 ID 改变，分支／历史更新／恢复后的 result 均为 None，历史恢复无有效确认 |
| H03 内嵌客户端工具注册与门槛（2 项） | 两个数据工具都被注册，未确认时均被拒绝 | 2 项通过；读写工具均产生工具消息，错误码为 scope_incomplete；字符串 API 未增加结构化确认能力 |

### 五、严格 I/O：1 项

代码：`backend/tests/blocking_io/test_research_data.py`。

| 测试用例 | 预期结果 | 实际结果 |
| --- | --- | --- |
| B01 真实异步图写入并读取快照 | 严格检测器不报告事件循环内阻塞 I/O，且真实文件读写成功 | 通过；sources 计数为 1，读回标题为“合成受控来源”；该用例同时纳入严格全量 146 passed / 1 skipped |

## 红绿灯复现与修改记录

以下记录开发时实际出现的红灯；首轮模块缺失、业务缺陷和测试断言问题分别说明。日志文件均位于本文开头的日志目录。

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志 |
| --- | --- | --- | --- | --- |
| 手机与笔记本样本装载，2 failed | data 模块尚不存在，导入失败 | 增加契约、批次合并与 JSON 往返能力 | 首轮 2 passed；后续契约组合 23 passed | 红灯：contract-red.log；首轮绿灯见当时执行输出，后续日志：contract-green.log |
| 价格契约用例，1 failed / 22 passed | 尚无价格维度及必须携带口径的规则 | 增加 kind=price、价格元数据与金额／币种一致性校验 | 23 passed | contract-rules-red.log → contract-green.log |
| 快照接口，1 failed | storage 模块尚不存在，导入失败 | 增加原子快照保存、恢复和分页读取 | 24 passed，包含当时契约组合 | storage-red-host.log → storage-green-host.log |
| 真实图 4 failed，原工厂 HTTP 4 failed | RESEARCH_TOOLS 和数据状态接线尚不存在 | 统一注册研究工具，通过原 handler 绑定受校验实现，保存结果索引 | 57 passed，包含旧接线回归 | integration-red-host.log、http-red-host.log → integration-first-host.log |
| 来源标签场景，1 failed / 1 passed | 来源 ToolMessage 的保留标签原样进入模型请求 | 只在模型请求副本中中和标签，存储及原工具记录保持原文 | 当时组合 59 passed；最终 G15 通过 | source-context-red-host.log → data-combined-host.log、final-targeted-host.log |
| Windows junction 重定向场景，1 failed | 只检查线程根，允许研究目录指向同线程沙箱 | 将解析后的路径限制到当前研究及范围的专属目录 | 快照组合 8 passed | path-redirect-red-host.log → path-redirect-green-host.log |
| 扩展生命周期场景，1 failed / 22 passed | 测试将初始范围版本写死为 2，忽略首次草案提议已递增版本 | 修改测试，基于实际已记录范围版本判断相对递增；未修改生产逻辑 | 最终定向组合 210 passed，对应 G13 通过 | integration-expanded-host.log → final-targeted-host.log |
| 补测强化旧 ID 负例，1 failed / 4 passed | 测试替身将范围占位符替换绑定到研究 ID 占位符；故意换错研究 ID 后范围仍为字符串，提前触发 invalid_data | 两个占位符独立替换；另增只改变研究 ID 的 4 项图测试，以及失败来源补齐原因后的 1 项契约测试；未改生产代码 | 所选 10 passed，完整定向 215 passed；新增 5 项首跑即通过 | coverage-placeholder-red-host.log → coverage-independent-host.log、coverage-regression-host.log |

### 环境失败与处理

环境准备失败不计为业务测试通过，也不与生产缺陷混合统计。

| 复现 | 红灯原因 | 怎么修改 | 修改后 | 日志 |
| --- | --- | --- | --- | --- |
| 沙箱内异步测试长期无最终输出 | 最小 asyncio 的 faulthandler 栈停在 _fallback_socketpair → accept，尚未完成事件循环初始化 | 核实并停止本次卡住的进程，在宿主环境重跑；不修改事件循环或防护设置 | 宿主开发前后严格 I/O 分别为 145 passed / 1 skipped、146 passed / 1 skipped | 当次最小诊断见执行输出；before-blocking-host.log、after-blocking-host.log |
| 沙箱快照测试在 setup 阶段失败 | pytest 临时目录创建失败，尚未验证 storage 模块 | 在宿主正常临时目录重跑 | 得到真正的模块缺失红灯；补齐模块后组合通过 | storage-red.log → storage-red-host.log → storage-green-host.log |
| 开发前分片 1 收集失败，1 error | 两分片同时收集，对已有固定 CaseProbe 临时文件产生竞争 | 另一分片开始执行后单独重跑分片 1；未跳过或修改相关用例 | 分片 1 为 8504 passed / 183 skipped，分片 2 为 8502 passed / 186 skipped | before-shard-1-host.log → before-shard-1-host-retry.log、before-shard-2-host.log |

所有测试子进程继承 `PYTHONDONTWRITEBYTECODE=1`，调用带 `-B`；保持防护开启，没有白名单或 SkillScan 改动。沙箱内部分纯测试退出时出现 pyreadline3 清理句柄诊断，宿主最终验证没有用它代替测试结果。

## 可证明边界

已知事实必须有来源与摘录，不代表摘录语义一定支持数值或结论；来源 available 是采集方记录，不是联网认证。真实可达性、时效、独立来源、评测条件合理性与当前价格归属板块 5。来源标签中和也不等于所有自然语言注入都已解决。

没有新增正式报告、CSV、面板、预算计数或停止规则；没有真实 DeepSeek 质量评测、Docker 构建、部署、提交或推送。前端未修改，本块没有重跑前端检查；先前通过的前端记录属于历史证据。

## 复现命令

本次补测的精确筛选命令（其余定向组合、严格 I/O 与 Ruff 命令见下方；默认离线分片仅为历史复现命令，本次未执行）：

```text
python -B -m pytest tests/test_research_data.py tests/test_research_data_integration.py -k "failed_source_with_reason or only_foreign_research_id or invalid_write_identity" -v --tb=short
```

从 backend 目录使用既有环境，PATH 加入根 `.venv/Scripts` 中已有 uv；设置 UTF-8、禁写字节码。配置升级测试使用 `UV_NO_SYNC=1`，专测依赖同步的临时项目会清除该变量。无需安装 GNU Make，直接执行对应 pytest／Ruff 命令。

```text
python -B -m pytest tests/test_research_data.py tests/test_research_storage.py tests/test_research_data_integration.py tests/test_research_data_http.py tests/test_research_scope.py tests/test_research_agent_integration.py tests/test_research_gateway_boundary.py tests/test_research_gateway_http.py tests/blocking_io/test_research_data.py -q --tb=short
python -B -m pytest tests/blocking_io -q --tb=short
python -B -m pytest -m "not live" --ignore=tests/blocking_io tests/ --splits 2 --group 1 --splitting-algorithm least_duration --durations-path=.test_durations -q --tb=short
python -B -m pytest -m "not live" --ignore=tests/blocking_io tests/ --splits 2 --group 2 --splitting-algorithm least_duration --durations-path=.test_durations -q --tb=short
python -B -m ruff check .
python -B -m ruff format --check .
```

开发前分片使用 `--ignore=tests/test_research_data.py` 排除当时新建的失败测试；原生产接线在两个开发前分片完成后才应用。其他新增测试是在这些进程完成收集后加入，没有纳入开发前分母。纯数据／存储新文件在基线期间实现，当时尚未被原 Agent 引用。

原实现主要日志：`final-targeted-host.log`、`before-blocking-host.log`、`before-shard-1-host-retry.log`、`before-shard-2-host.log`、`after-blocking-host.log`、`after-shard-{1,2}-host.log`、`after-ruff-{check,format}.log`。本次补测日志：`coverage-before-host.log`、`coverage-placeholder-red-host.log`、`coverage-independent-host.log`、`coverage-regression-host.log`、`coverage-blocking-host.log`。具体异常定位和变更见上表红绿日志。

原实现最终检查：全局 `git diff --check` 通过，另用 `git diff --no-index --check` 检查相关目录的 21 个未跟踪文件，未发现空白错误；相关文档的 84 个本地链接均存在。no-index 的退出 1 表示新文件与空文件不同，不能误当空白错误；首次辅助检查已据此修正。原实现已检查新增契约／存储／工具代码以及原工厂、客户端和文档 diff，保留进入本轮前的所有改动及运行时锁文件，未提交推送。本次补测另外检查两份测试、报告及交接／计划／测试指南的变更，并复查跟踪文件与本次涉及未跟踪文件的空白。

## 集中复盘

Agent 开发：结构化结果让采集、分析和交付共享同一对象；产品配置和范围版本防止错配；程序约束写入与归属，模型提出观察和解释。引用合法只是第一道检查，不能替代语义核实。

测试开发：契约、图、HTTP/SSE 和重启恢复分别证明不同边界；磁盘失败与取消要观察当前 checkpoint 是否推进，不能只检查文件是否存在；失败报告区分测试准备、断言错误和生产缺陷。既有测试回归不代替真实模型质量评测。
