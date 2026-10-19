"""Offline scope rules; confirmation records must come from trusted application state."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


class _FrozenModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        revalidate_instances="always",
    )


def _reject_boolean_amount(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("金额不能是布尔值")
    return value


def _reject_timestamp(value: object) -> object:
    if not isinstance(value, (date, str)):
        raise ValueError("研究日期必须是日期或 ISO 日期字符串，不能是时间戳")
    return value


Money = Annotated[Decimal, BeforeValidator(_reject_boolean_amount), Field(ge=0, allow_inf_nan=False)]
Text = Annotated[str, Field(strict=True, min_length=1)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]


class PurchaseBudget(_FrozenModel):
    mode: Literal["bounded", "unlimited"]
    minimum: Money | None = None
    maximum: Money | None = None

    @model_validator(mode="after")
    def validate_amounts(self) -> Self:
        if self.mode == "unlimited":
            if self.minimum is not None or self.maximum is not None:
                raise ValueError("不限预算时不能同时指定金额")
        elif self.maximum is None:
            raise ValueError("有限预算必须提供上限")
        elif self.minimum is not None and self.minimum > self.maximum:
            raise ValueError("预算下限不能高于上限")
        return self


class ScopeIssue(_FrozenModel):
    code: Text
    field: Text
    message: Text


class RuntimeLimits(_FrozenModel):
    """Declared limits only; execution accounting belongs to the research runtime."""

    max_duration_seconds: PositiveInt
    max_tool_calls: PositiveInt


class ResearchScope(_FrozenModel):
    topic: str | None = Field(default=None, min_length=1)
    objective: str | None = Field(default=None, min_length=1)
    named_candidates: tuple[Text, ...] = ()
    excluded_candidates: tuple[Text, ...] = ()
    allow_discovery: bool | None = Field(default=None, strict=True)
    target_candidate_count: int | None = Field(
        default=None,
        strict=True,
        gt=0,
    )
    purchase_budget: PurchaseBudget | None = None
    region: Text | None = None
    currency: Annotated[str, Field(strict=True, pattern=r"^[A-Z]{3}$")] | None = None
    as_of_date: Annotated[date, BeforeValidator(_reject_timestamp)] | None = None
    price_basis: Text | None = None
    product_scope: Text | None = None
    hard_constraints: tuple[Text, ...] = ()
    preferences: tuple[Text, ...] = ()
    research_focus: tuple[Text, ...] = ()
    must_check: tuple[Text, ...] = ()
    source_policy: Literal["public_only"] = "public_only"
    source_restrictions: tuple[Text, ...] = ()
    report_language: Text | None = None
    report_formats: tuple[Literal["markdown", "csv"], ...] = ("markdown", "csv")
    runtime_limits: RuntimeLimits | None = None
    assumptions: tuple[Text, ...] = ()
    unresolved_questions: tuple[ScopeIssue, ...] = ()

    @classmethod
    def with_defaults(cls, values: Mapping[str, object], *, as_of_date: date) -> Self:
        """Apply visible proposals only to absent keys; explicit None remains unresolved."""
        data = cls.model_validate(dict(values)).model_dump(exclude_unset=True)
        assumptions = list(data.get("assumptions", ()))
        for key, value, label in (
            ("region", "中国大陆", "购买地区"),
            ("currency", "CNY", "币种"),
            ("report_language", "中文", "报告语言"),
            ("as_of_date", as_of_date, "研究截至日期"),
        ):
            if key not in data:
                data[key] = value
                assumptions.append(f"默认建议：{label}为{value}")
        data["assumptions"] = assumptions
        return cls.model_validate(data)

    @model_validator(mode="after")
    def validate_deliverables(self) -> Self:
        if len(self.report_formats) != 2 or set(self.report_formats) != {"markdown", "csv"}:
            raise ValueError("一期交付必须同时包含 Markdown 和 CSV")
        return self

    @model_validator(mode="after")
    def validate_candidates(self) -> Self:
        for names in (self.named_candidates, self.excluded_candidates):
            if len(names) != len(set(names)):
                raise ValueError("候选名单不能重复")
        if set(self.named_candidates) & set(self.excluded_candidates):
            raise ValueError("同一候选不能同时指定和排除")
        if self.named_candidates and self.target_candidate_count is not None:
            if self.allow_discovery is False and len(self.named_candidates) != self.target_candidate_count:
                raise ValueError("仅比较指定对象时，目标数量必须与名单一致")
            if self.allow_discovery is True and len(self.named_candidates) > self.target_candidate_count:
                raise ValueError("目标数量不能少于已指定对象的数量")
        return self


class ScopeAssessment(_FrozenModel):
    issues: tuple[ScopeIssue, ...]

    @property
    def ready_for_confirmation(self) -> bool:
        return not self.issues


def assess_scope(scope: ResearchScope) -> ScopeAssessment:
    scope = ResearchScope.model_validate(scope)
    issues = []

    for field, label in (
        ("topic", "研究对象"),
        ("objective", "决策目标"),
        ("allow_discovery", "是否允许发现候选"),
        ("target_candidate_count", "期望比较数量"),
        ("purchase_budget", "购买预算（可明确不限）"),
        ("region", "购买地区"),
        ("currency", "币种"),
        ("as_of_date", "研究截至日期"),
        ("price_basis", "价格口径（适用单位、费用与优惠条件）"),
        ("report_language", "报告语言"),
        ("runtime_limits", "研究时间与工具调用上限"),
    ):
        if getattr(scope, field) is None and not (field == "topic" and scope.named_candidates):
            issues.append(
                ScopeIssue(
                    code="missing_information",
                    field=field,
                    message=f"请明确{label}",
                )
            )

    if scope.allow_discovery is False and not scope.named_candidates:
        issues.append(ScopeIssue(code="missing_information", field="named_candidates", message="仅比较指定对象时，请提供候选名单"))
    return ScopeAssessment(issues=tuple(issues) + scope.unresolved_questions)


class ScopeRuleError(ValueError):
    """An actionable admission/transition failure, separate from malformed data."""

    def __init__(self, code: str, field: str, message: str, issues: tuple[ScopeIssue, ...] = ()):
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
        self.issues = issues


_SUMMARY_LABELS = {
    "topic": "研究对象",
    "objective": "决策目标",
    "named_candidates": "指定对象（仍需核实是否符合条件）",
    "excluded_candidates": "排除对象",
    "allow_discovery": "允许自动发现候选",
    "target_candidate_count": "期望比较数量",
    "purchase_budget": "购买预算",
    "region": "购买地区",
    "currency": "币种",
    "as_of_date": "研究截至日期",
    "price_basis": "价格口径",
    "product_scope": "产品版本与销售范围",
    "hard_constraints": "必须满足的硬约束",
    "preferences": "可权衡的偏好",
    "research_focus": "研究重点",
    "must_check": "必查事项",
    "source_policy": "来源权限（仅公开资料）",
    "source_restrictions": "来源限制",
    "report_language": "报告语言",
    "report_formats": "交付文件",
    "runtime_limits": "运行限制（秒数与工具调用次数）",
    "assumptions": "待统一确认的默认与建议",
    "unresolved_questions": "待解决问题",
}


class ScopeConfirmation(_FrozenModel):
    research_id: Text
    scope_version: PositiveInt
    request_id: Text
    scope: ResearchScope

    @property
    def summary(self) -> str:
        """Always derive display text from the exact snapshot, never accept model prose."""
        lines = ["研究范围确认：确认前不联网；候选数量是目标，证据不足时说明缺口，不凑数。"]
        for name, value in self.scope.model_dump(mode="json").items():
            lines.append(f"- {_SUMMARY_LABELS.get(name, name)}: {json.dumps(value, ensure_ascii=False)}")
        return "\n".join(lines)


class ResearchScopeSession(_FrozenModel):
    """Trusted state only, not a model tool input or proof of HTTP authorization."""

    research_id: Text = Field(default_factory=lambda: str(uuid4()))
    scope_version: PositiveInt = 1
    scope: ResearchScope
    pending_confirmation: ScopeConfirmation | None = None
    confirmation: ScopeConfirmation | None = None

    @model_validator(mode="after")
    def validate_confirmation_binding(self) -> Self:
        if self.pending_confirmation is not None and self.confirmation is not None:
            raise ValueError("不能同时等待确认和已经确认")
        record = self.pending_confirmation or self.confirmation
        if record is not None:
            if record.research_id != self.research_id or record.scope_version != self.scope_version or record.scope != self.scope:
                raise ValueError("确认记录与当前研究范围不匹配")
            if not assess_scope(self.scope).ready_for_confirmation:
                raise ValueError("不完整的范围不能携带确认记录")
        return self


class ScopeConfirmationResponse(_FrozenModel):
    research_id: Text
    scope_version: PositiveInt
    request_id: Text
    action: Literal["confirm", "reject"]


def _require_complete(scope: ResearchScope) -> None:
    assessment = assess_scope(scope)
    if not assessment.ready_for_confirmation:
        raise ScopeRuleError("scope_incomplete", "scope", "研究范围尚未完整，请先解决列出的问题", assessment.issues)


def _replace_session(session: ResearchScopeSession, **changes: object) -> ResearchScopeSession:
    # model_copy(update=...) skips validation; reconstruct every transition instead.
    return ResearchScopeSession.model_validate({**session.model_dump(), **changes})


def revise_scope(session: ResearchScopeSession, scope: ResearchScope | Mapping[str, object], expected_version: int) -> ResearchScopeSession:
    """Replace a whole draft; patches and text interpretation belong to the caller."""
    session = ResearchScopeSession.model_validate(session)
    if type(expected_version) is not int or expected_version != session.scope_version:
        raise ScopeRuleError("version_conflict", "scope_version", "范围已经修改，请重新读取当前版本")
    scope = ResearchScope.model_validate(scope)
    if scope == session.scope:
        return session
    return _replace_session(session, scope=scope, scope_version=session.scope_version + 1, pending_confirmation=None, confirmation=None)


def prepare_confirmation(session: ResearchScopeSession) -> ResearchScopeSession:
    session = ResearchScopeSession.model_validate(session)
    _require_complete(session.scope)
    if session.pending_confirmation is not None or session.confirmation is not None:
        return session
    request = ScopeConfirmation(research_id=session.research_id, scope_version=session.scope_version, request_id=str(uuid4()), scope=session.scope)
    return _replace_session(session, pending_confirmation=request)


def respond_to_confirmation(session: ResearchScopeSession, response: ScopeConfirmationResponse | Mapping[str, object]) -> ResearchScopeSession:
    """The caller must map an authenticated, explicit user action to this response."""
    session = ResearchScopeSession.model_validate(session)
    response = ScopeConfirmationResponse.model_validate(response)
    if response.research_id != session.research_id:
        raise ScopeRuleError("confirmation_mismatch", "research_id", "确认回答属于另一项研究")
    if response.scope_version != session.scope_version:
        raise ScopeRuleError("version_conflict", "scope_version", "确认回答的范围版本已过期")
    request = session.pending_confirmation or session.confirmation
    if request is None or response.request_id != request.request_id:
        raise ScopeRuleError("confirmation_mismatch", "request_id", "确认请求不存在或已失效")
    if session.confirmation is not None:
        if response.action == "confirm":
            return session
        raise ScopeRuleError("confirmation_mismatch", "action", "已确认的请求不能作为待确认请求拒绝")
    _require_complete(session.scope)
    return _replace_session(session, pending_confirmation=None, confirmation=request if response.action == "confirm" else None)


def require_confirmed_scope(session: ResearchScopeSession) -> ResearchScope:
    """Call at the actual research boundary in the next integration module."""
    session = ResearchScopeSession.model_validate(session)
    _require_complete(session.scope)
    if session.confirmation is None:
        raise ScopeRuleError("scope_unconfirmed", "confirmation", "当前范围尚未获得用户明确确认")
    return session.scope
