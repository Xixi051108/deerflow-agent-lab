# 板块一：研究范围与确认规则

日期：2026-10-19。独立业务规则已实现；板块二已连接原确认卡、ThreadState、Gateway 和工具准入，见 [接线说明](RESEARCH_INTEGRATION.md) 与 [接线测试报告](RESEARCH_INTEGRATION_TEST_REPORT.md)。本文保留板块一接口与当时的边界说明；纯规则验证本身仍不能代替接线验证。
测试证据及全量回归限制见 [测试报告](RESEARCH_SCOPE_TEST_REPORT.md)。

## 解决什么问题

把开放品类的消费者选购需求整理成用户可确认的研究约定。两个门槛分开：

1. `assess_scope(...).ready_for_confirmation`：信息已完整，可以展示范围，请用户确认。
2. `require_confirmed_scope(...)`：当前版本已明确确认，允许进入正式研究。

前者不等于后者。板块一只有规则，没有实际搜索；“确认前不联网”目前是范围约定，板块二必须在真实执行路径接线验证。

## 范围与校验

- 对象：`topic` 或明确的 `named_candidates`；指定名单不代表已经满足筛选条件。`excluded_candidates` 不得与指定名单重叠。
- 目标：`objective`；硬约束、偏好、研究重点、必查事项分别放在 `hard_constraints/preferences/research_focus/must_check`。
- 候选边界：`allow_discovery` 必须明确；`False` 与 `None` 不同。目标数量为严格正整数，指定比较时与名单一致；自动发现可包含指定的起始对象，但不能比这些对象更少。数量是目标，后续候选不足应披露，不凑数。
- 购买预算：缺失为 `None`；明确不限为 `{"mode": "unlimited"}`；有限预算为 `{"mode": "bounded", "maximum": ..., "minimum": ...}`。金额使用 Decimal，允许零和相等端点、可省下限；拒绝负值、布尔值、非有限值、倒置区间、有限预算缺上限，以及不限预算却指定金额。
- 市场与口径：`region/currency/as_of_date/price_basis`；可另填 `product_scope`。币种校验为三位大写字母，不自动换汇，也不判断市场上是否存在该货币报价。日期接受日期对象／ISO 日期文本，不接受数字时间戳。
- 来源与交付：仅 `source_policy="public_only"`，可通过 `source_restrictions` 收紧范围。`report_language` 必须明确；一期同时交付 Markdown 和 CSV。
- 运行限制：`runtime_limits.max_duration_seconds/max_tool_calls` 必须为严格正整数，由调用方提供已解析配置。本模块只声明和检查，不计数、不停止循环。默认数值仍待后续校准。
- 默认与建议：`with_defaults(values, as_of_date=调用方提供的日期)` 只为缺失键补中国大陆／CNY／中文／指定日期，并写入 `assumptions` 供用户确认；显式 `None` 保持待定，不覆盖用户已填值。`model_validate` 本身不暗补这些条件。
- 歧义：后续澄清环节把无法确定的重要问题写入 `unresolved_questions`，每项含 `code/field/message`，存在问题时不能确认。本模块不识别自然语言中的任意矛盾，也不承诺预算内一定存在符合条件的产品。

所有嵌套模型冻结、集合为元组，拒绝未知字段。格式／结构非法抛 `ValidationError`；完整性不足返回问题而不丢弃草案。条件苛刻、可行性待查不属于格式错误。

## 公开接口与状态转换

| 接口 | 输入与结果 |
| --- | --- |
| `ResearchScope.model_validate` | 保存合法但可能不完整的草案 |
| `assess_scope` | 返回 `ScopeAssessment`，其 `issues` 可定位字段 |
| `revise_scope(session, scope, expected_version)` | 整份范围替换；版本匹配后，实质变化使版本递增并清除确认 |
| `prepare_confirmation(session)` | 完整性通过后返回新会话，内含待确认请求；已有有效请求时幂等 |
| `respond_to_confirmation(session, response)` | 校验 `research_id/scope_version/request_id/action`，只接受 `confirm` 或 `reject` |
| `require_confirmed_scope(session)` | 返回已确认范围，否则抛 `ScopeRuleError` |

`ScopeRuleError` 带 `code/field/message/issues`；主要代码为 `scope_incomplete`、`scope_unconfirmed`、`version_conflict`、`confirmation_mismatch`。

确认请求的 `scope` 是完整快照，`summary` 从快照所有字段生成，不能用模型另写的摘要替代。摘要只在访问时生成，JSON 恢复后重新从同一快照派生。

用户补充信息、修改表单都不能直接确认。带修改的回答应先 `revise_scope`，再展示新请求。所有实质范围变化，包括偏好、研究重点、报告语言和运行限制，都使旧确认失效。去除首尾空白后内容不变不递增版本；改变后又改回原值也不能恢复历史确认。

拒绝后新请求使用新标识。对当前有效确认重复提交相同确认动作幂等；旧版本、其他研究、旧请求、缺少身份或夹带编辑内容均拒绝。

## 离线调用示例

以下数值仅用于演示，不是产品默认运行上限。在后端 Python 环境中调用：

```python
from datetime import date

from deerflow.agents.research.scope import (
    ResearchScope,
    ResearchScopeSession,
    ScopeRuleError,
    prepare_confirmation,
    require_confirmed_scope,
    respond_to_confirmation,
    revise_scope,
)

scope = ResearchScope.with_defaults(
    {
        "topic": "在线课程",
        "objective": "为初学者比较学习安排和总体费用",
        "allow_discovery": True,
        "target_candidate_count": 3,
        "purchase_budget": {"mode": "unlimited"},
        "price_basis": "单人完整课程费用，优惠资格另列",
        "runtime_limits": {"max_duration_seconds": 120, "max_tool_calls": 6},
    },
    as_of_date=date(2026, 10, 19),
)
pending = prepare_confirmation(ResearchScopeSession(scope=scope))
request = pending.pending_confirmation
print(request.summary)

# 下一块从经过认证的用户回答构造 response；此处仅模拟明确确认。
confirmed = respond_to_confirmation(
    pending,
    {
        "research_id": request.research_id,
        "scope_version": request.scope_version,
        "request_id": request.request_id,
        "action": "confirm",
    },
)
assert require_confirmed_scope(confirmed).topic == "在线课程"

changed_scope = ResearchScope.model_validate(
    {**scope.model_dump(), "preferences": ["偏好直播"]}
)
revised = revise_scope(confirmed, changed_scope, expected_version=1)
try:
    require_confirmed_scope(revised)
except ScopeRuleError as error:
    assert error.code == "scope_unconfirmed"
else:
    raise AssertionError("修改范围后应要求重新确认")
```

完整的“模糊草案 → 补齐 → 展示 → 确认 → 放行 → 修改 → 阻止 → 再确认”见 `test_full_offline_workflow_from_vague_input_to_reconfirmation`。

## 下一块的接线约束

本节原接线要求已由板块二实现。新增 `invalidate_confirmation(session)` 在新普通文字到达时清除待确认和已确认记录，不改变同一范围的版本；新确认请求使用新标识。其余接口与板块一规则保持一致。

`ResearchScopeSession` 和确认记录必须来自可信应用状态；模型只能提议 `ResearchScope`，不能设置“已确认”。JSON 恢复验证快照一致性，不证明回答来自用户，也不防止伪造一整套互相匹配的外部状态。

下一块需要完成：用户身份及 Thread 归属校验、确认卡回答关联、ThreadState 保存与恢复、并发写入的原子版本检查，以及研究工具执行前的准入拦截。当前 `expected_version` 只检查传入的会话快照，不提供数据库并发锁。

确认前澄清 Run 可以创建；不能把准入检查直接放在所有 Run 创建入口，误伤澄清。来源网页、模型文本、客户端自由字段都不能直接制造确认记录。实际硬约束筛选、研究预算执行与报告生成属于后续板块。

## 带练与面试复盘

前两轮测试复现了模块缺失与候选边界漏查，修复后得到 `2 passed`；后续继续补齐范围规则、边界测试与回归验证。

- Agent 开发：模型提出条件和澄清问题，程序确定校验、版本与准入；提示词不能代替执行入口的程序检查。
- 测试开发：等价类包含缺失／合法／非法；状态迁移包含草案／待确认／确认／拒绝／修改；版本与请求标识用于覆盖旧回答和重复操作。
- 证据边界：规则单测、JSON 恢复和严格 I/O 检查分别证明不同内容，都不能代替真实模型、HTTP/SSE 或 UI 接线验收。
