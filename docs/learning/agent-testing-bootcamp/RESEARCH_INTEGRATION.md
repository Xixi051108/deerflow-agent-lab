# 板块二：原 Agent 接线与持久化

日期：2026-10-19。范围规则及本块接线已实现；确定性验证与全量回归限制见 [测试报告](RESEARCH_INTEGRATION_TEST_REPORT.md)。

后续进展：板块 3 已在同一工具链增加结构化数据读写、快照和有界状态索引，见 [数据说明](RESEARCH_DATA.md) 与 [数据测试报告](RESEARCH_DATA_TEST_REPORT.md)。下文保留板块 2 当时的交付范围与历史验证；此前全量失败已另做专项修复。

## 本块交付

复用原自定义 Agent、Gateway、Agent 图、工具包装、checkpoint、SSE、事件历史和 Human Input Card。当前交付的是范围确认及研究准入闭环；候选与证据契约、实际预算计数／停止、报告和研究面板仍属后续板块。

实际路径：用户文字 → Gateway 归一化当前输入 → worker 构造可信操作 → `ResearchScopeMiddleware.before_agent` → 模型提议范围 → 程序生成原确认卡 → 下一 Run 消费明确操作 → 工具执行前 `require_confirmed_scope`。

这里“确认前不联网”指禁止模型工具进行研究检索、抓取、浏览器、命令或委派等动作；整理需求所用的模型 API 仍会被调用。尚未进行真实模型的研究质量或运行成本验收。

## 创建和选择专用 Agent

在已登录的原应用中，通过现有 `POST /api/agents` 创建。以下是请求体示例，不含密钥；模型省略时沿用现有模型配置：

```json
{
  "name": "competitor-research",
  "display_name": "竞品分析 Agent",
  "description": "开放品类消费者选购研究，先确认范围再研究",
  "research_enabled": true,
  "skills": [],
  "allowed_subagents": [],
  "soul": "帮助用户整理消费者选购研究范围。只追问决定研究方向的缺口，其他建议在完整范围里公开确认。开放品类，不写死产品名单；时间和工具调用上限由用户明确提供。"
}
```

可在原应用浏览器开发者控制台使用同源、携带现有登录 cookie 的请求；无需复制 cookie 或提供密码：

```javascript
const body = {
  name: "competitor-research",
  display_name: "竞品分析 Agent",
  description: "先确认范围，再研究",
  research_enabled: true,
  skills: [],
  allowed_subagents: [],
  soul: "开放品类的消费者选购研究助手。先整理范围，只追问关键缺口，时间和工具调用上限由用户明确提供。",
};
const response = await fetch("/api/agents", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
console.log(response.status, await response.json());
```

已有同名 Agent 返回 409 时，使用现有 `PUT /api/agents/competitor-research` 提交 `{"research_enabled": true}`，不要反复创建。随后从原 Agent 列表选择并开始新聊天。没有增加新的页面或设置开关。

`research_enabled` 默认为 false；创建、读取和更新接口均支持。未携带该字段的更新保留原值；文件与 SQL Agent 存储均复用现有配置文档，不需要迁移。关闭该配置不会删除已有 Thread 的研究约束；旧研究须恢复原 Agent 配置后继续，普通任务可使用普通 Thread。

本轮仅提供代码和配置示例，没有创建本机真实 Agent、修改实际模型配置或替用户提交真实研究请求。

## 接口与状态归属

| 接口／字段 | 职责 |
| --- | --- |
| `AgentConfig.research_enabled` | 配置决定研究能力；不以 Agent 名称硬编码 |
| `ThreadState.research` | 服务端管理的完整 JSON 记录，省略本轮写入时保留 |
| `ResearchState` | Thread、用户、Agent、当前 `ResearchScopeSession` 和 `last_run_id` |
| `propose_research_scope(scope, expected_research_id, expected_version, new_research=False)` | 模型提交完整草案及预期版本，不能提交确认记录 |
| `invalidate_confirmation(session)` | 新普通文字清除待确认请求和确认记录；内容未变时不虚增范围版本 |
| `require_confirmed_scope(session)` | 每次实际研究工具执行前的程序准入 |

状态读取时重新校验。范围实质变化递增版本，所有新确认请求有独立标识；新文字即便只是“继续”，也清除旧确认。新的研究分配新 `research_id`，只保存当前研究；历史对话仍是历史，不能作为当前确认凭据。后续候选／证据数据还需在板块三按研究标识校验归属。

完整性不足时出补充信息卡；完整时调用 `prepare_confirmation`，卡片问题来自 `ScopeConfirmation.summary`，不能用模型改写的摘要代替。模型上下文仅注入当前范围、研究标识、版本与确认状态；不把用户范围文本放进系统指令。

## 回答及执行规则

- 沿用 `human_input` v1 回答协议与 `source=ask_clarification`。卡片有固定的 `confirm`／`reject` 操作；`request_id` 精确关联可信状态里的研究标识、版本和快照，不新增前端可写确认字段。
- 只有当前请求的明确选项可确认；普通文字“确认”、自由文本回答、来源网页、模型输出和普通澄清选项均不能制造确认。协议额外字段、非法类型、不匹配正文和旧回答被拒绝。原前端 `buildHumanInputResponseText` 格式与明确选项值正文均受支持。
- 普通文字或同次提交的文字与确认混合输入先使旧确认失效。拒绝、重复确认和不匹配回答终止本 Run 的研究动作；有效重复确认不再次执行工具。
- worker 只从本次已归一化的输入提取操作，经服务端上下文 `__deerflow_research_turn` 传递；不扫描整段历史。`last_run_id` 防止同一 Run 的内部续轮重复处理。
- 研究中间件位于 sandbox／工具处理器外侧；未确认只允许范围提议与 `ask_clarification`，其余工具在处理器调用前被拦截。确认后每次工具调用仍校验运行归属和范围准入。
- 范围工具也必须经过原有权限／技能策略／guardrail 和 ToolNode。中间件使用公开的 `ToolCallRequest.override(tool=...)` 给当前调用绑定受校验状态转换，不修改共享工具对象、不提前写状态；原处理链拒绝时不会产生范围写入。
- 澄清优先结束本轮；范围提议不与研究动作并行，同批多个或格式错误的范围提议也不执行研究兄弟调用。使用原工具调用克隆工具移除结构化及 provider 内容块中的兄弟调用。
- 非交互标记不会代替用户确认；普通 Thread 无研究状态时走原行为。`DeerFlowClient` 也启用相同配置与工具门槛，其 `values` 输出携带研究状态；其字符串聊天接口尚无结构化确认参数，确认交互使用原 Web 卡片。

Gateway Run 输入和手动状态更新接口都拒绝直接写 `research`（422）；客户端也不能提供可信操作上下文。用户和 Thread 所属关系沿用原认证与存储边界。直接图调用属于可信宿主集成，必须安装相同中间件并提供当前运行身份与由输入构造的操作，缺少时不放行。

## 恢复、并发与历史

- 使用现有 full／delta checkpoint，不另建数据库表、锁或旁路状态文件。SQLite 关闭再打开后，范围及待确认请求仍可供下一 Run 使用。
- 复用 `RunManager` 的同 Thread 运行互斥和 durable admission；独立状态写入沿用 `reserve_checkpoint_write`，范围工具另检查预期研究标识和版本。同批只允许一个范围写入，避免并行 ToolNode 写覆盖。
- 历史 checkpoint 回放同时读取选中状态与当前 head；即便选中研究创建前的状态，也不能删除已有研究约束。历史范围转为新标识的未确认草案；手动状态接口从旧 checkpoint 派生时遵守同一规则。
- 分支在建立时就保存新的研究标识、目标 Thread 绑定和未确认草案；保留原范围，清除父研究的确认与待确认请求。原中间件还会防御性处理未迁移的跨 Thread 复制记录。
- 重启恢复状态不等于自动续跑中断 Run。本块不新增后台恢复执行器，也不把一次澄清 Run 的 success 当成研究完成。

## 整块复盘

| 面试追问 | 应能说明的实际证据 |
| --- | --- |
| Thread、Run、State 如何关联？ | 同一 Thread 的不同 Run 从 checkpoint 读写同一研究记录；`last_run_id` 只用于当前操作去重 |
| 为什么不用提示词保证确认？ | 模型替身故意跳过确认时，真实图中的工具处理器仍未执行 |
| 版本号和请求标识分别防什么？ | 版本约束范围修订；请求标识使同版本重新出卡后旧回答仍失效 |
| 幂等是否等于再次执行？ | 有效确认重复回答返回说明，不重复触发搜索 |
| JSON 往返证明持久化了吗？ | 不足；测试真正关闭／重开 SQLite saver 和图，再跨 Run 确认 |
| 如何复现绕过和修复？ | 旧 checkpoint、切换 Agent、手动历史更新、格式错误的并行范围调用均有 red→green 记录 |
| 哪些证据尚未取得？ | 未验证真实模型提议质量、真实网络研究质量、预算停止、报告交付或真实浏览器完整端到端操作 |
