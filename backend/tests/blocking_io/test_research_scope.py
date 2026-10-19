"""Scope transitions must remain usable on the agent event loop without I/O."""

from datetime import date

import pytest

from deerflow.agents.research.scope import ResearchScope, ResearchScopeSession, prepare_confirmation, require_confirmed_scope, respond_to_confirmation, revise_scope


@pytest.mark.asyncio
async def test_scope_confirmation_does_not_block_the_event_loop():
    scope = ResearchScope.with_defaults(
        {
            "topic": "咖啡机",
            "objective": "比较清洁便利性与总体费用",
            "allow_discovery": True,
            "target_candidate_count": 2,
            "purchase_budget": {"mode": "unlimited"},
            "price_basis": "单台含税价格，配件另列",
            "runtime_limits": {"max_duration_seconds": 60, "max_tool_calls": 2},
        },
        as_of_date=date(2026, 10, 19),
    )
    pending = prepare_confirmation(ResearchScopeSession(scope=scope))
    request = pending.pending_confirmation
    confirmed = respond_to_confirmation(pending, {"research_id": request.research_id, "scope_version": request.scope_version, "request_id": request.request_id, "action": "confirm"})

    assert require_confirmed_scope(confirmed).topic == "咖啡机"
    assert "确认前不联网" in request.summary
    restored = ResearchScopeSession.model_validate_json(confirmed.model_dump_json())
    assert revise_scope(restored, scope, expected_version=1) == confirmed
