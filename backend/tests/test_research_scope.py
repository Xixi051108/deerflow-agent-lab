from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_vague_scope_is_saved_but_not_ready_for_confirmation():
    from deerflow.agents.research.scope import ResearchScope, assess_scope

    scope = ResearchScope.model_validate({"topic": "扫地机器人"})

    assessment = assess_scope(scope)

    assert scope.topic == "扫地机器人"
    assert assessment.ready_for_confirmation is False
    assert any(issue.field == "objective" for issue in assessment.issues)


def test_objective_does_not_replace_candidate_boundaries():
    from deerflow.agents.research.scope import ResearchScope, assess_scope

    scope = ResearchScope.model_validate(
        {
            "topic": "扫地机器人",
            "objective": "为养猫家庭选择清理毛发方便的产品",
        }
    )

    assessment = assess_scope(scope)

    assert assessment.ready_for_confirmation is False

    missing_fields = {issue.field for issue in assessment.issues}
    assert "objective" not in missing_fields
    assert "allow_discovery" in missing_fields
    assert "target_candidate_count" in missing_fields


@pytest.mark.parametrize(
    "budget",
    [
        {"mode": "bounded", "maximum": -1},
        {"mode": "bounded", "minimum": 200, "maximum": 100},
        {"mode": "bounded", "minimum": -1, "maximum": 100},
        {"mode": "bounded"},
        {"mode": "bounded", "maximum": True},
        {"mode": "bounded", "maximum": "NaN"},
        {"mode": "bounded", "maximum": float("inf")},
        {"mode": "unlimited", "maximum": 100},
    ],
)
def test_purchase_budget_rejects_invalid_values(budget):
    from deerflow.agents.research.scope import ResearchScope

    with pytest.raises(ValidationError):
        ResearchScope.model_validate({"purchase_budget": budget})


@pytest.mark.parametrize("minimum,maximum", [(None, "199.99"), ("100", "100"), (0, 0)])
def test_purchase_budget_keeps_exact_amounts(minimum, maximum):
    from deerflow.agents.research.scope import ResearchScope

    scope = ResearchScope.model_validate({"purchase_budget": {"mode": "bounded", "minimum": minimum, "maximum": maximum}})

    assert scope.purchase_budget.maximum == Decimal(str(maximum))
    assert scope.purchase_budget.minimum == (None if minimum is None else Decimal(str(minimum)))


def test_missing_purchase_budget_differs_from_explicitly_unlimited():
    from deerflow.agents.research.scope import ResearchScope, assess_scope

    missing = ResearchScope()
    unlimited = ResearchScope.model_validate({"purchase_budget": {"mode": "unlimited"}})

    assert any(issue.field == "purchase_budget" for issue in assess_scope(missing).issues)
    assert all(issue.field != "purchase_budget" for issue in assess_scope(unlimited).issues)


def complete_scope(**changes):
    from deerflow.agents.research.scope import ResearchScope

    values = {
        "topic": "在线课程",
        "objective": "为初学者选择适合业余时间学习的数据分析课程",
        "allow_discovery": True,
        "target_candidate_count": 3,
        "purchase_budget": {"mode": "unlimited"},
        "price_basis": "单人完整课程费用，优惠资格另列",
        "runtime_limits": {"max_duration_seconds": 120, "max_tool_calls": 6},
    }
    values.update(changes)
    return ResearchScope.with_defaults(values, as_of_date=date(2026, 10, 19))


def test_complete_scope_is_ready_with_visible_injected_defaults():
    from deerflow.agents.research.scope import assess_scope

    scope = complete_scope()

    assert assess_scope(scope).ready_for_confirmation
    assert scope.region == "中国大陆"
    assert scope.currency == "CNY"
    assert scope.report_language == "中文"
    assert scope.as_of_date == date(2026, 10, 19)
    assert any("中国大陆" in item for item in scope.assumptions)
    assert scope.report_formats == ("markdown", "csv")


@pytest.mark.parametrize("field", ["region", "currency", "as_of_date", "price_basis", "report_language", "runtime_limits"])
def test_required_conditions_remain_missing_when_explicitly_unresolved(field):
    from deerflow.agents.research.scope import assess_scope

    scope = complete_scope(**{field: None})

    assert any(issue.field == field for issue in assess_scope(scope).issues)


def test_defaults_do_not_replace_explicit_market_or_mutate_input():
    from deerflow.agents.research.scope import ResearchScope

    values = {"region": "日本", "currency": "JPY", "report_language": "日文", "assumptions": ["建议优先关注易用性"]}
    scope = ResearchScope.with_defaults(values, as_of_date=date(2026, 9, 1))

    assert scope.region == "日本"
    assert scope.currency == "JPY"
    assert scope.as_of_date == date(2026, 9, 1)
    assert not any("中国大陆" in item for item in scope.assumptions)
    assert values == {"region": "日本", "currency": "JPY", "report_language": "日文", "assumptions": ["建议优先关注易用性"]}


@pytest.mark.parametrize(
    "change",
    [
        {"target_candidate_count": True},
        {"target_candidate_count": "3"},
        {"target_candidate_count": 0},
        {"allow_discovery": "false"},
        {"topic": "   "},
        {"hard_constraints": [" "]},
        {"currency": "人民币"},
        {"report_formats": ["markdown"]},
        {"source_policy": "paid_sources"},
        {"confirmed": True},
        {"runtime_limits": {"max_duration_seconds": 0, "max_tool_calls": 1}},
        {"runtime_limits": {"max_duration_seconds": 10, "max_tool_calls": True}},
    ],
)
def test_scope_rejects_malformed_values(change):
    with pytest.raises(ValidationError):
        complete_scope(**change)


def test_unresolved_semantics_block_readiness_but_demanding_conditions_do_not():
    from deerflow.agents.research.scope import assess_scope

    scope = complete_scope(hard_constraints=["必须适合初学者"], preferences=["价格越低越好"], purchase_budget={"mode": "bounded", "maximum": 1})
    ambiguous = complete_scope(unresolved_questions=[{"code": "ambiguous_requirement", "field": "hard_constraints", "message": "是否允许只有录播课程？"}])

    assert assess_scope(scope).ready_for_confirmation
    assert any(issue.code == "ambiguous_requirement" for issue in assess_scope(ambiguous).issues)


@pytest.mark.parametrize("topic", ["扫地机器人", "在线课程", "咖啡机"])
def test_scope_is_category_independent(topic):
    from deerflow.agents.research.scope import assess_scope

    assert assess_scope(complete_scope(topic=topic, objective="为首次购买者比较易用性与总体费用")).ready_for_confirmation


def test_specified_candidates_and_discovery_have_distinct_boundaries():
    from deerflow.agents.research.scope import assess_scope

    specified = complete_scope(allow_discovery=False, named_candidates=["课程 A", "课程 B"], target_candidate_count=2)
    seeded = complete_scope(named_candidates=["课程 A"], target_candidate_count=3)
    missing_names = complete_scope(allow_discovery=False)

    assert assess_scope(specified).ready_for_confirmation
    assert not specified.allow_discovery
    assert assess_scope(seeded).ready_for_confirmation
    assert any(issue.field == "named_candidates" for issue in assess_scope(missing_names).issues)


@pytest.mark.parametrize(
    "change",
    [
        {"allow_discovery": False, "named_candidates": ["课程 A"], "target_candidate_count": 2},
        {"named_candidates": ["课程 A", "课程 B"], "target_candidate_count": 1},
        {"named_candidates": ["课程 A", " 课程 A "]},
        {"named_candidates": ["课程 A"], "excluded_candidates": ["课程 A"]},
        {"named_candidates": [""]},
    ],
)
def test_conflicting_candidate_boundaries_are_invalid(change):
    with pytest.raises(ValidationError):
        complete_scope(**change)


def pending_session(**scope_changes):
    from deerflow.agents.research.scope import ResearchScopeSession, prepare_confirmation

    return prepare_confirmation(ResearchScopeSession(scope=complete_scope(**scope_changes)))


def reply(session, action="confirm", **changes):
    request = session.pending_confirmation or session.confirmation
    values = {"research_id": request.research_id, "scope_version": request.scope_version, "request_id": request.request_id, "action": action}
    values.update(changes)
    return values


def test_complete_scope_requires_an_explicit_matching_confirmation():
    from deerflow.agents.research.scope import ResearchScopeSession, ScopeRuleError, prepare_confirmation, require_confirmed_scope, respond_to_confirmation

    draft = ResearchScopeSession(scope=complete_scope())
    pending = prepare_confirmation(draft)

    for session in (draft, pending):
        with pytest.raises(ScopeRuleError) as error:
            require_confirmed_scope(session)
        assert error.value.code == "scope_unconfirmed"

    confirmed = respond_to_confirmation(pending, reply(pending))

    assert require_confirmed_scope(confirmed) == draft.scope
    assert confirmed.pending_confirmation is None
    assert confirmed.confirmation.request_id == pending.pending_confirmation.request_id
    assert respond_to_confirmation(confirmed, reply(confirmed)) == confirmed
    assert prepare_confirmation(pending) == pending


def test_incomplete_scope_cannot_generate_a_confirmation_request():
    from deerflow.agents.research.scope import ResearchScope, ResearchScopeSession, ScopeRuleError, prepare_confirmation, require_confirmed_scope

    session = ResearchScopeSession(scope=ResearchScope(topic="扫地机器人"))

    for operation in (prepare_confirmation, require_confirmed_scope):
        with pytest.raises(ScopeRuleError) as error:
            operation(session)
        assert error.value.code == "scope_incomplete"
        assert any(issue.field == "objective" for issue in error.value.issues)


@pytest.mark.parametrize("change", [{"research_id": "another-study"}, {"scope_version": 2}, {"request_id": "old-request"}])
def test_confirmation_rejects_wrong_identity_version_or_request(change):
    from deerflow.agents.research.scope import ScopeRuleError, respond_to_confirmation

    pending = pending_session()
    with pytest.raises(ScopeRuleError) as error:
        respond_to_confirmation(pending, reply(pending, **change))
    assert error.value.code in {"confirmation_mismatch", "version_conflict"}
    assert pending.confirmation is None


@pytest.mark.parametrize("change", [{"action": "edit"}, {"action": "已补充预算"}, {"scope": {}}, {"request_id": None}, {"scope_version": True}])
def test_answering_or_editing_is_not_a_confirmation(change):
    from deerflow.agents.research.scope import respond_to_confirmation

    pending = pending_session()
    with pytest.raises(ValidationError):
        respond_to_confirmation(pending, reply(pending, **change))


def test_rejection_requires_a_new_request_and_old_answers_do_not_apply():
    from deerflow.agents.research.scope import ScopeRuleError, prepare_confirmation, respond_to_confirmation

    pending = pending_session()
    old_reply = reply(pending)
    rejected = respond_to_confirmation(pending, reply(pending, action="reject"))

    assert rejected.pending_confirmation is None
    assert rejected.confirmation is None
    renewed = prepare_confirmation(rejected)
    assert renewed.pending_confirmation.request_id != old_reply["request_id"]
    with pytest.raises(ScopeRuleError):
        respond_to_confirmation(renewed, old_reply)


def test_summary_includes_the_entire_snapshot_and_visible_proposals():
    pending = pending_session(
        named_candidates=["课程 A"],
        excluded_candidates=["课程 B"],
        product_scope="当前公开销售的基础课程版本",
        hard_constraints=["必须提供字幕"],
        preferences=["偏好短视频"],
        research_focus=["练习设计"],
        must_check=["是否提供作业反馈"],
        source_restrictions=["只看公开课程说明和独立评测"],
    )
    request = pending.pending_confirmation
    summary = request.summary

    assert request.scope == pending.scope
    for expected in ("课程 A", "课程 B", "基础课程版本", "必须提供字幕", "偏好短视频", "练习设计", "作业反馈", "独立评测", "120", "6", "markdown", "csv", "2026-10-19", "CNY", "默认建议", "候选数量是目标", "确认前不联网"):
        assert expected in summary


@pytest.mark.parametrize(
    "change",
    [
        {"topic": "咖啡机"},
        {"objective": "比较进阶课程的项目训练"},
        {"named_candidates": ["课程 C"]},
        {"excluded_candidates": ["课程 D"]},
        {"allow_discovery": False, "named_candidates": ["课程 A", "课程 B", "课程 C"]},
        {"target_candidate_count": 4},
        {"purchase_budget": {"mode": "bounded", "maximum": 500}},
        {"region": "日本"},
        {"currency": "JPY"},
        {"as_of_date": date(2026, 10, 18)},
        {"price_basis": "整个家庭购买套餐的总费用"},
        {"product_scope": "仅当前基础版本"},
        {"hard_constraints": ["必须有中文字幕"]},
        {"preferences": ["偏好直播"]},
        {"research_focus": ["练习反馈"]},
        {"must_check": ["退费条件"]},
        {"source_restrictions": ["只接受公开的官方说明"]},
        {"report_language": "英文"},
        {"runtime_limits": {"max_duration_seconds": 100, "max_tool_calls": 4}},
        {"assumptions": ["建议先比较入门课程"]},
        {"unresolved_questions": [{"code": "ambiguous_requirement", "field": "objective", "message": "是否需要证书？"}]},
    ],
)
def test_every_substantive_scope_change_invalidates_confirmation(change):
    from deerflow.agents.research.scope import ScopeRuleError, require_confirmed_scope, respond_to_confirmation, revise_scope

    pending = pending_session()
    confirmed = respond_to_confirmation(pending, reply(pending))
    revised = revise_scope(confirmed, complete_scope(**change), expected_version=1)

    assert revised.scope_version == 2
    assert revised.confirmation is None
    assert revised.pending_confirmation is None
    assert confirmed.confirmation is not None
    with pytest.raises(ScopeRuleError):
        require_confirmed_scope(revised)
    with pytest.raises(ScopeRuleError):
        respond_to_confirmation(revised, reply(confirmed))


def test_no_change_or_outer_whitespace_does_not_invalidate_confirmation():
    from deerflow.agents.research.scope import respond_to_confirmation, revise_scope

    pending = pending_session(hard_constraints=["必须提供字幕"])
    confirmed = respond_to_confirmation(pending, reply(pending))
    unchanged = complete_scope(topic=" 在线课程 ", hard_constraints=[" 必须提供字幕 "])

    assert revise_scope(confirmed, unchanged, expected_version=1) == confirmed


def test_returning_to_old_values_does_not_restore_old_confirmation():
    from deerflow.agents.research.scope import respond_to_confirmation, revise_scope

    pending = pending_session()
    confirmed = respond_to_confirmation(pending, reply(pending))
    revised = revise_scope(confirmed, complete_scope(region="日本"), expected_version=1)
    restored = revise_scope(revised, confirmed.scope, expected_version=2)

    assert restored.scope_version == 3
    assert restored.confirmation is None


def test_revision_clears_a_pending_request_and_rejects_stale_writes():
    from deerflow.agents.research.scope import ScopeRuleError, prepare_confirmation, respond_to_confirmation, revise_scope

    pending = pending_session()
    revised = revise_scope(pending, complete_scope(target_candidate_count=4), expected_version=1)
    renewed = prepare_confirmation(revised)

    assert revised.pending_confirmation is None
    assert renewed.pending_confirmation.request_id != pending.pending_confirmation.request_id
    with pytest.raises(ScopeRuleError) as error:
        revise_scope(renewed, complete_scope(), expected_version=1)
    assert error.value.code == "version_conflict"
    with pytest.raises(ScopeRuleError):
        respond_to_confirmation(renewed, reply(pending))


def test_invalid_replacement_does_not_modify_the_original_session():
    from deerflow.agents.research.scope import revise_scope

    pending = pending_session()
    before = pending.model_dump_json()
    with pytest.raises(ValidationError):
        revise_scope(pending, {"target_candidate_count": -1}, expected_version=1)
    assert pending.model_dump_json() == before


def test_nested_scope_and_confirmation_snapshots_are_immutable():
    pending = pending_session(hard_constraints=["必须提供字幕"])
    with pytest.raises(ValidationError):
        pending.scope.region = "日本"
    with pytest.raises(ValidationError):
        pending.scope.purchase_budget.maximum = Decimal("999")
    with pytest.raises(TypeError):
        pending.scope.hard_constraints[0] = "已放宽"
    with pytest.raises(ValidationError):
        pending.pending_confirmation.scope_version = 100


def test_trusted_serialization_restores_confirmation_and_rejects_mismatched_snapshots():
    from deerflow.agents.research.scope import ResearchScopeSession, require_confirmed_scope, respond_to_confirmation

    pending = pending_session()
    confirmed = respond_to_confirmation(pending, reply(pending))
    restored = ResearchScopeSession.model_validate_json(confirmed.model_dump_json())
    assert require_confirmed_scope(restored) == confirmed.scope

    tampered = confirmed.model_dump(mode="json")
    tampered["scope"]["region"] = "日本"
    with pytest.raises(ValidationError):
        ResearchScopeSession.model_validate(tampered)
    unsafe_copy = confirmed.model_copy(update={"scope": complete_scope(region="日本")})
    with pytest.raises(ValidationError):
        require_confirmed_scope(unsafe_copy)


@pytest.mark.parametrize("value", ["优先入门课程", None, {"proposal": "入门课程"}])
def test_default_helper_does_not_coerce_malformed_assumptions(value):
    with pytest.raises(ValidationError):
        complete_scope(assumptions=value)


def test_explicitly_named_objects_do_not_require_a_redundant_category():
    from deerflow.agents.research.scope import assess_scope

    scope = complete_scope(topic=None, allow_discovery=False, named_candidates=["课程 A", "课程 B"], target_candidate_count=2)
    assert assess_scope(scope).ready_for_confirmation


@pytest.mark.parametrize("value", [0, True, 1.5])
def test_as_of_date_rejects_numeric_timestamps(value):
    with pytest.raises(ValidationError):
        complete_scope(as_of_date=value)


def test_missing_confirmation_identity_is_invalid_and_unsolicited_answers_are_rejected():
    from deerflow.agents.research.scope import ResearchScopeSession, ScopeRuleError, respond_to_confirmation

    pending = pending_session()
    for field in ("research_id", "scope_version", "request_id", "action"):
        incomplete = reply(pending)
        del incomplete[field]
        with pytest.raises(ValidationError):
            respond_to_confirmation(pending, incomplete)
    with pytest.raises(ScopeRuleError):
        respond_to_confirmation(ResearchScopeSession(scope=pending.scope), reply(pending))


def test_pending_confirmation_can_be_restored_and_conflicting_receipts_are_rejected():
    from deerflow.agents.research.scope import ResearchScopeSession, respond_to_confirmation

    pending = pending_session()
    restored = ResearchScopeSession.model_validate_json(pending.model_dump_json())
    confirmed = respond_to_confirmation(restored, reply(restored))
    conflicting = confirmed.model_dump()
    conflicting["pending_confirmation"] = pending.pending_confirmation
    with pytest.raises(ValidationError):
        ResearchScopeSession.model_validate(conflicting)


def test_full_offline_workflow_from_vague_input_to_reconfirmation():
    from deerflow.agents.research.scope import ResearchScope, ResearchScopeSession, ScopeRuleError, prepare_confirmation, require_confirmed_scope, respond_to_confirmation, revise_scope

    vague = ResearchScopeSession(scope=ResearchScope(topic="在线课程"))
    with pytest.raises(ScopeRuleError, match="尚未完整"):
        prepare_confirmation(vague)
    filled = revise_scope(vague, complete_scope(), expected_version=1)
    pending = prepare_confirmation(filled)
    assert "默认建议" in pending.pending_confirmation.summary
    confirmed = respond_to_confirmation(pending, reply(pending))
    assert require_confirmed_scope(confirmed).topic == "在线课程"
    revised = revise_scope(confirmed, complete_scope(preferences=["偏好直播"]), expected_version=2)
    with pytest.raises(ScopeRuleError) as error:
        require_confirmed_scope(revised)
    assert error.value.code == "scope_unconfirmed"
    renewed = prepare_confirmation(revised)
    reconfirmed = respond_to_confirmation(renewed, reply(renewed))
    assert require_confirmed_scope(reconfirmed).preferences == ("偏好直播",)


@pytest.mark.parametrize("confirmed", [False, True])
def test_new_user_text_invalidates_confirmation_even_without_a_scope_change(confirmed):
    from deerflow.agents.research.scope import invalidate_confirmation, prepare_confirmation, respond_to_confirmation

    pending = pending_session()
    session = respond_to_confirmation(pending, reply(pending)) if confirmed else pending
    invalidated = invalidate_confirmation(session)

    assert invalidated.scope == session.scope
    assert invalidated.scope_version == session.scope_version
    assert invalidated.research_id == session.research_id
    assert invalidated.confirmation is None
    assert invalidated.pending_confirmation is None
    renewed = prepare_confirmation(invalidated)
    assert renewed.pending_confirmation.request_id != pending.pending_confirmation.request_id
    assert invalidate_confirmation(invalidated) == invalidated
