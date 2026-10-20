# 板块五：证据采集与价格观察

实现与验证记录见 [测试报告](RESEARCH_EVIDENCE_TEST_REPORT.md)，设计依据见 [实施任务书](RESEARCH_EVIDENCE_PLAN.md)。沿用原研究 Agent、确认卡、权限处理器和快照，没有另建应用、数据库或研究循环。

最新实际限制：同日 [小米15真实电商验收](RESEARCH_EVIDENCE_WEB_ACCEPTANCE.md) 未通过。两个京东响应HTML包含目标商品价格，但当前Readability文章提取选择评论区域并丢失价格；另有搜索相关性、空壳内容及Reader 403问题。核心代码和受控测试已有，真实商品采集尚待修复与复测。

## 使用顺序

1. 用 `research_enabled: true` 的原研究 Agent 确认范围，保存候选、明确配置和比较维度。
2. `web_search` 寻找线索。只有用户消息或成功的 `web_search`／`web_fetch` 返回过的完整 URL，才能提交采集；模型自填 Source URL 不构成准入依据。
3. 单独调用 `collect_research_source`，传入产品、配置或产品级适用范围，以及当前研究 ID、范围版本和数据 revision。
4. 按返回的 source_ids 使用 `read_research_data(section="sources")` 分页读取实际提取文本，遵循 next_offset。用新 revision 提交事实、精确引用、缺口与冲突。
5. 回读 claims 的 evidence_assessment，并逐字段核对原文、配置、条件和金额。说明已保存内容与未知，不提前输出完整研究推荐或报告文件。

新普通文字仍使确认失效；同范围重新确认保留数据，范围改变、新研究、历史恢复和分支沿用原清空规则。工具授权拒绝时不改走隐藏请求通道。

## 采集工具与容量

`collect_research_source` 参数：url、product_id、configuration_ids／product_wide、kind、expected_research_id、expected_scope_version、expected_revision。配置必须属于产品，产品须先保存。kind 和配置适用范围由模型声明，程序不因此认定网站是官方或页面确实匹配该配置。

该工具与普通数据写入互斥，同批多次采集、采集加读取／其他写入、含不完整写入都不执行。它通过原 handler 接受工具权限与 guardrail 检查，然后使用既有 Jina Reader、Readability 和 Markdown 提取器；异步配置、提取和文件存储走 run_file_io。

| 边界 | 实际行为 |
| --- | --- |
| Reader 响应 | 解码后最多 512 KiB；流式读取，超限拒绝，不先把整个响应存入内存 |
| 网络时限 | 复用 web_fetch timeout／proxy／trust_env；timeout 约束为 1–60 秒，同时限制整个 Reader 请求与单次 I/O 等待 |
| 提取文本 | 最多 128 KiB UTF-8；超限标记 text_limit，不声称取得尾部 |
| Source | 按字符分段，每段紧凑 JSON 最多 8 KiB；中文、引号和反斜杠不会被字节切断 |
| 既有存储 | 快照仍为 2 MiB，读取与 checkpoint 索引仍为 16 KiB，引用最多 4,000 字符；不提高原阈值 |

Source.capture 包含服务端生成的 group_id、method、segment_index、start_char、end_char、total_chars、truncation_reason。total_chars 指保留下来的提取文本长度，不能据此计算被丢弃的原页面大小。collected_at 是实际响应之后生成的 UTC 时间。片段共享一次采集组；多段不是多个独立来源，同 URL 多次采集也不是独立交叉佐证。

采集字段、正文、适用范围与类型不能通过 `record_research_data` 伪造或改写；重新采集产生新 ID。429、超时、空响应、空提取等保存明确 failed Source，而非伪装正文；响应状态属于 Reader，不能据此证明原站的错误或反爬原因。模型只收到小型采集回执，正文经原分页读取，原文仍作为不可信数据保存；保留标签只在模型请求副本中和，不拼进系统指引。

磁盘失败或网络取消不推进索引。文件写成但尚未被checkpoint引用时保持孤儿文件，不扫描晋升。若工具更新已经进入原框架持久化pending writes，随后checkpoint提交失败，原get_state会应用这些待恢复写入：已提交checkpoint仍旧，恢复投影可显示有真实文件支持的新采集。Run仍失败，不能说最终提交成功；本块保留这一原恢复协议。

通用 `web_fetch` 的原签名、返回和 4096 字符预览没有改变；研究采集使用新增的有界方法。DDG helper 仍把真正无结果和异常都返回空列表，本块没有将它改成可靠的故障分类器。

## 价格评估的含义

新增已知 Price 必须引用服务端采集的可用正文；观察时间须等于某条引用的实际 collected_at，金额须出现在摘录中。不是随意填入“今天”。程序保留地区、币种、卖家、渠道、配置、口径和条件，返回以下派生评估，不保存模型可写的 verified 标记。

| status | 含义 |
| --- | --- |
| captured_offer_observation | 结构上具备采集、对应时点与范围、声明配置级官方／销售来源的公开报价观察 |
| conditional_price | 会员、促销、补贴等条件报价，不能假定任何人都可享用 |
| historical_or_list_price | 首发价或标价；不能当作当前可成交价 |
| used_price | 二手口径 |
| unverified_price | 未绑定采集、市场／币种不符、时间不符、金额无摘录支持或缺少声明销售配置绑定 |
| unknown／inference／conflicting_observation | 未知、推断或已关联冲突，须查看原因／依据 |
| captured_observation／unbound_observation | 非价格观察来自采集或未绑定正文 |

所有评估都有 `semantic_review_required: true`。即使返回 captured_offer_observation，程序也不能识别所有否定句、起售价、配置差异、转载、伪店铺或旧缓存。页面今天取得，不证明内容今天有效、实际库存、优惠资格或结算金额。日期检查采用带时区 observation 的 date 与范围 as_of_date 比较，不提供统一跨地区时区或有效期策略。

兼容选择：旧 JSON 保持原字节／哈希可读；原普通批次仍能保存未绑定的**非价格**观察，但回读明确是 unbound_observation，不能当实际读页的证据。新采集流程要求模型使用采集正文；程序当前强制采集门槛覆盖新增价格，未对所有非价格新写入一律拒绝。它是相对于任务书“全部新增已知事实均强制采集”的保留边界，不能隐藏为已完成的来源真实性保障。

## 单位、冲突和纠错

明确换算使用 Decimal，仅支持 g／kg、MB／GB、MiB／GiB 各自内部；Claim 保留 original_value／original_unit 并校验转换值。mAh／Wh、GB／GiB、不同测试条件拒绝直接换算。不同属性分别建维度，单位必须和维度相同，不能把电池值放到影像维度，也不能把价格 unit 改为 null 来规避错误。

已知非推断 Claim 与原 Citation 不可同 ID 替换，保留新 ID 并用冲突／缺口解释更正。相同产品、配置、维度、单位和明确条件下不同事实要求 Conflict；不同卖家、时间、价格条件可并存，不强行判冲突。自然语言同义条件、任意实体别名和转载独立性仍需要语义判断。

配置不匹配时，不能只在文字中写警告却把低配价关联高配 ID。为其他变体保存独立 Configuration 并正确采集绑定，或只在 Gap 说明差异，让目标值保持 null。缺口和条件里的数字也属于事实输出，必须逐项核对，不能只查 Claim.value。

## 双岗位复盘

| 追问 | 本次可解释的证据 |
| --- | --- |
| 引用存在为什么仍会幻觉？ | 摘录“并非3299”可通过数字出现检查；语义否定和适用配置仍须审核，不能升级为 verified |
| 怎样防止模型冒充实际采集？ | 采集字段只能通过原工具 handler 生成，普通批次不能造或改；未绑定非价格观察明确降为 unbound |
| 为什么 10 次调用不够？ | 首轮真实模型在读三页与纠错时触发测试上限，随后用 20 模型／24 工具／180 秒重新验证；不是业务预算实现 |
| 为什么真实模型通过后还审核？ | 自动断言未覆盖 Gap／conditions，人工发现2919／2GB错误，新增数字质量检查后重测 |
| 替身和网站探测各证明什么？ | 冻结 HTTP 证明可复现行为；真实 DeepSeek 观察自主决策；公开探测只证明取得当次提取文本，不能互相替代 |

第六阶段仍需预算、重试及完成状态；第七阶段交付报告；第八阶段研究面板。没有重启现有服务、创建生产专用实例、提交推送或进行完整开放网络研究。
