# 板块三：研究数据与证据契约

状态：本块实现、定向验收及开发后默认离线／严格 I/O 全量已完成，实际结果和未验证边界见同目录 `RESEARCH_DATA_TEST_REPORT.md`。

## 要解决的问题

研究范围确认只解决“允许研究什么”。候选、配置和来源如果只存在于模型回答中，后续分析、面板和文件生成无法可靠共享数据，也无法判断某段引用究竟支持哪个配置。

本块沿用原 Agent、工具权限链和线程 checkpoint，建立受校验的数据记录与读取能力。模型提交观察，程序保证结构、归属、引用和存储一致性；事实真实性、来源独立性和当前价格仍需板块五核对。

## 数据关系

`deerflow.agents.research.data` 提供离线 Pydantic 契约：

| 集合 | 表达的内容 |
| --- | --- |
| products | 产品、品牌、型号，候选／排除状态及理由 |
| configurations | 属于一个产品的具体配置；标签和属性可明确未知 |
| dimensions | 动态维度、单位、口径；kind 区分 measurement、qualitative、price |
| sources | HTTP(S) URL、标题、类型、获取状态、带时区采集时间、可选发布时间、保存文本与适用范围 |
| claims | fact／opinion／inference、产品与配置、维度、值、单位、条件、未知原因及推断依据 |
| citations | 事实／评价与来源之间的关系、原文摘录及定位描述 |
| gaps | 产品／配置／维度的资料缺口及原因 |
| conflicts | 同产品、配置、维度下的不同说法及冲突说明 |

ID 在一份结果中全局唯一，使用 1–64 个 ASCII 字母、数字、下划线或连字符，首位是字母或数字。批次不能包含身份、路径、确认凭据或 verified 等额外字段。

`ResearchBatch` 允许只提交部分集合；`apply_batch(result, batch)` 按稳定 ID 整条替换或新增，再校验合并后的完整结果。不会删除其他记录；失败时不修改原结果。重复提交相同 ID 不产生重复记录，但成功写入仍递增 revision。冲突说法必须使用不同 ID 保存。

数字在 Python 中使用 Decimal，JSON 中使用字符串，避免金额精度损失。数值拒绝 bool、NaN 和 Infinity。未知使用 `value: null` 并填写 missing_reason；真实零值是已知事实，需要来源。字符串不能以空白代替未知。

来源必须明确为产品级 `product_wide: true`，或通过 configuration_ids 指定配置级适用范围。引用不能跨产品或借用另一配置。直接引用要求来源 available／truncated、有保存正文、quote 是正文的精确子串；truncated 仍明确表示资料不完整。事实和评价的已知值需要直接引用，推断只关联已有已知事实／评价，不伪装成来源原文。

价格维度的已知事实必须有 price：amount、region、currency、channel、seller、basis、conditions、observed_at；金额、币种与事实值一致，配置必须明确。basis 区分 launch、list、public_offer、promotion、member、subsidized、used。保留历史首发价不证明当前可买价格；记录工具不会自动认证这些口径的真实性。

## 原工具链接口

研究模式统一注册三个工具：原 propose_research_scope，以及：

```text
record_research_data(batch, expected_research_id, expected_scope_version, expected_revision)
read_research_data(section, ids=None, offset=0, limit=20)
```

当前研究标识、范围版本与数据 revision 由模型上下文提供；尚未写数据时 revision 为 0。工具的身份来自可信运行上下文，不能由参数指定。确认前均不放行，普通新文字仍先使确认失效。模型一次必须独立提交一个写入工具调用；同批多个写入、读写混合、写入与其他工具混合均不执行。

写入经过原权限与 guardrail 后才执行，成功返回 revision、counts 和 affected_ids；关系验证、预期版本或文件写入失败均不推进 checkpoint。错误返回 `error.code/field/message`，不包含原始整批数据。

读取返回 research_id、scope_version、revision、section、total、offset、records、next_offset 和 `authority: unverified_research_data`。limit 范围为 1–100，默认 20；指定 ids 时只在筛选结果内分页，未知 ID 报错。达到字节上限时在完整记录边界分页；单条记录过大则明确报错，不静默截断来源正文。

所有来源内容是数据，不是系统指令；仅在模型请求的 ToolMessage 副本中中和保留标签，存储和原工具记录保留原文。工具结果不表示已核实事实，也不意味着已解决自然语言提示注入。没有新增 REST 接口、前端面板或自定义事件。

## 快照、恢复与故障窗口

完整结果放在 `Paths.thread_dir(thread_id, user_id=...)` 下的 `research/{research_id}/scope-{scope_version}/{sha256}.json`，位于沙箱 user-data 目录之外。内容包含 schema_version=1、研究／范围／数据版本和服务端绑定的所有者身份。

状态只保存 result 索引：研究标识、范围版本、数据版本、SHA-256、集合计数和最多三个产品名称预览。快照与 checkpoint 不组成跨文件数据库事务：

1. 校验批次和合并结果。
2. UTF-8 编码，检查上限；写临时文件、flush／fsync 后原子替换到内容哈希路径。
3. 返回 Command，由原图提交 checkpoint 中的当前索引。

磁盘失败不更新状态；文件成功而 checkpoint 未提交只产生未引用快照。读取只根据 checkpoint 的索引，不扫描目录选“最新文件”。没有增加垃圾回收服务。异步工具经现有 run_file_io 执行文件操作；取消等待不能撤销已开始的文件线程，但晚到的文件不会自动成为当前结果。

| 上限 | 行为 |
| --- | --- |
| 单份 JSON 2 MiB | 拒绝写入，保留原索引 |
| result 状态投影 16 KiB | 拒绝超限索引 |
| 每条引用摘录 4,000 字符 | 拒绝超限引用 |
| 单次读取 16 KiB | 按完整记录分页；单条超限明确报错 |

这些是工程上限，不是研究预算或候选数量默认值。读取重新检查文件大小、哈希、契约、归属、revision 和计数；文件缺失、损坏及版本冲突不被视为空研究。

旧 checkpoint 没有 result 时正常加载。新文字但范围版本不变时保留结果、暂停工具准入；重新确认后可继续。范围实质变化、新研究、历史回放和分支清除当前结果索引，保留旧文件，避免混入新范围。phase 只反映 awaiting_confirmation／recording，不声称任务完成、预算已执行或报告已交付。

## 整块实践与复盘

按契约 → 存储 → 工具链 → 恢复和 HTTP/SSE 顺序完成，每个边界先看失败，再实现与回归。受控手机和笔记本样本位于后端 tests/support/research_samples.py；它们不是产品白名单，也不提供真实购买建议。

Agent 岗应能解释：为什么模型回答不是结果库；为什么配置需要独立 ID；模型声明的来源为何不能直接变成 verified；为什么 checkpoint 指针决定当前快照。

测试岗应能解释：契约校验与语义核实分别证明什么；JSON 往返为何不等于重启恢复；怎样复现配置错配、磁盘失败、未引用快照和跨用户访问；如何区分环境初始化失败与业务回归。

不把未执行的检查、跳过项或模型替身测试写成真实研究质量验收。默认离线全集、严格 I/O、Ruff 与最终 diff 的实际结果在测试报告中逐项记录。
