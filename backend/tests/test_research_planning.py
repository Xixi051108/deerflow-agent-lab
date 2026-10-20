"""Public research planning rules; synthetic records are not verified products."""

from datetime import date

import pytest


def scope(**changes):
    from deerflow.agents.research.scope import ResearchScope

    return ResearchScope.with_defaults(
        {
            "topic": "手机",
            "objective": "摄影和续航",
            "allow_discovery": True,
            "target_candidate_count": 2,
            "purchase_budget": {"mode": "unlimited"},
            "price_basis": "单台全新公开售价",
            "runtime_limits": {"max_duration_seconds": 120, "max_tool_calls": 12},
            **changes,
        },
        as_of_date=date(2026, 10, 20),
    )


def empty():
    from deerflow.agents.research.data import ResearchResult

    return ResearchResult(research_id="study", scope_version=1, user_id="default", thread_id="research-thread", agent_name="researcher")


def test_merged_candidates_cannot_exceed_the_confirmed_count():
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    original = apply_batch(empty(), ResearchBatch(products=[{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]))
    batch = ResearchBatch(products=[{"id": "c", "name": "C", "reason": "待核实"}])
    merged = apply_batch(original, batch)
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(), merged, batch)
    assert error.value.code == "candidate_limit_exceeded"
    assert original.revision == 1 and len(original.products) == 2


@pytest.mark.parametrize(
    "changes,name,code",
    [
        ({"allow_discovery": False, "named_candidates": ["A"], "target_candidate_count": 1}, "B", "candidate_outside_scope"),
        ({"excluded_candidates": ["A"]}, " a ", "candidate_excluded"),
    ],
)
def test_exact_named_and_excluded_boundaries(changes, name, code):
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch(products=[{"id": "p", "name": name, "reason": "待核实"}])
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(**changes), apply_batch(empty(), batch), batch)
    assert error.value.code == code


@pytest.mark.parametrize("category", ["phone", "laptop"])
def test_traceable_cross_category_plan_can_be_saved_and_restored(category):
    from support.research_discovery_samples import discovery_scope, planning_batch

    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch.model_validate(planning_batch(category))
    result = apply_batch(empty(), batch)
    validate_research_plan(discovery_scope(category), result, batch)
    restored = ResearchResult.model_validate_json(result.model_dump_json())
    assert restored.products[0].discovery_source_ids == ("s1",)
    assert restored.dimensions[0].description


def test_named_alias_can_be_kept_without_inventing_a_source():
    from deerflow.agents.research.data import ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch(products=[{"id": "a", "name": "A 正式名称", "scope_name": "A", "reason": "用户指定，身份与价格待核实"}])
    validate_research_plan(scope(allow_discovery=False, named_candidates=["A"], target_candidate_count=1), apply_batch(empty(), batch), batch)


def test_discovery_requires_a_source_instead_of_a_model_memory():
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch(products=[{"id": "p", "name": "新候选", "reason": "模型记忆，不足以作为发现依据"}])
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(), apply_batch(empty(), batch), batch)
    assert error.value.code == "missing_discovery_source"


@pytest.mark.parametrize(
    "section,field,value,code",
    [
        ("products", "reason", None, "missing_selection_reason"),
        ("products", "reason", "  ", "missing_selection_reason"),
        ("products", "name", "  ", "invalid_candidate"),
        ("dimensions", "description", None, "missing_dimension_rationale"),
        ("dimensions", "description", "  ", "missing_dimension_rationale"),
        ("dimensions", "basis", "  ", "invalid_dimension"),
    ],
)
def test_new_planning_records_explain_their_purpose(section, field, value, code):
    from support.research_discovery_samples import planning_batch

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    data = planning_batch()
    data[section][0][field] = value
    batch = ResearchBatch.model_validate(data)
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(), apply_batch(empty(), batch), batch)
    assert error.value.code == code


def test_one_named_object_cannot_be_counted_as_two_candidates():
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch(products=[{"id": "a", "name": "A", "reason": "用户指定"}, {"id": "b", "name": "A 正式名", "scope_name": "A", "reason": "同一对象别名"}])
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(named_candidates=["A"]), apply_batch(empty(), batch), batch)
    assert error.value.code == "duplicate_candidate"


@pytest.mark.parametrize("change,code", [("absent", "dangling_reference"), ("foreign", "discovery_source_mismatch"), ("duplicate", "duplicate_reference")])
def test_discovery_source_relationships_are_checked_on_the_merged_graph(change, code):
    from pydantic import ValidationError
    from support.research_discovery_samples import planning_batch

    from deerflow.agents.research.data import ResearchBatch, apply_batch

    data = planning_batch()
    if change == "absent":
        data["products"][0]["discovery_source_ids"] = ["absent"]
    elif change == "foreign":
        data["products"].append({"id": "other", "name": "另一产品"})
        data["sources"][0]["product_id"] = "other"
    else:
        data["products"][0]["discovery_source_ids"] = ["s1", "s1"]
    original = empty()
    with pytest.raises(ValidationError) as error:
        apply_batch(original, ResearchBatch.model_validate(data))
    assert error.value.errors()[0]["ctx"]["error"].code == code
    assert original.revision == 0


@pytest.mark.parametrize("status,text", [("failed", "有正文但采集失败"), ("unknown", "未确认返回"), ("available", "  "), ("truncated", None)])
def test_unavailable_discovery_evidence_is_not_a_valid_origin(status, text):
    from support.research_discovery_samples import planning_batch

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    data = planning_batch()
    data["sources"][0].update(status=status, text=text, failure_reason="固定故障" if status in {"failed", "unknown"} else None)
    batch = ResearchBatch.model_validate(data)
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(), apply_batch(empty(), batch), batch)
    assert error.value.code == "invalid_discovery_source"


@pytest.mark.parametrize("binding", ["未知名称", "B", "  "])
def test_named_binding_cannot_reassign_a_different_explicit_name(binding):
    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    batch = ResearchBatch(products=[{"id": "p", "name": "A", "scope_name": binding, "reason": "非法重绑定"}])
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(named_candidates=["A", "B"]), apply_batch(empty(), batch), batch)
    assert error.value.code == "invalid_scope_binding"


def test_same_model_is_not_two_products_but_pro_suffix_is_preserved():
    from support.research_discovery_samples import planning_batch

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    data = planning_batch()
    data["products"][0].update(brand="Brand", model="A1")
    data["products"].append({**data["products"][0], "id": "p2", "name": "不同店铺名称", "brand": " brand ", "model": "a1", "discovery_source_ids": ["s2"]})
    data["sources"].append({**data["sources"][0], "id": "s2", "product_id": "p2"})
    batch = ResearchBatch.model_validate(data)
    with pytest.raises(DataRuleError) as error:
        validate_research_plan(scope(), apply_batch(empty(), batch), batch)
    assert error.value.code == "duplicate_candidate"
    data["products"][1]["model"] = "A1 Pro"
    batch = ResearchBatch.model_validate(data)
    validate_research_plan(scope(), apply_batch(empty(), batch), batch)


def test_excluded_objects_and_configurations_do_not_use_candidate_slots():
    from support.research_discovery_samples import planning_batch

    from deerflow.agents.research.data import ResearchBatch, apply_batch
    from deerflow.agents.research.planning import validate_research_plan

    data = planning_batch()
    data["products"].append({"id": "excluded", "name": "用户排除", "disposition": "excluded", "reason": "用户明确排除"})
    data["configurations"].append({"id": "c2", "product_id": "p1", "label": "12GB/256GB"})
    batch = ResearchBatch.model_validate(data)
    validate_research_plan(scope(target_candidate_count=1, excluded_candidates=["用户排除"]), apply_batch(empty(), batch), batch)


def test_legacy_snapshot_keeps_its_original_bytes_and_allows_unrelated_gap_writes(tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path

    from deerflow.agents.research.data import SECTIONS, ResearchBatch, ResultRef, apply_batch
    from deerflow.agents.research.planning import validate_research_plan
    from deerflow.agents.research.storage import load_result
    from deerflow.config.paths import get_paths

    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    monkeypatch.setattr("deerflow.config.paths._paths", None)
    raw = Path(__file__).with_name("support").joinpath("research_legacy_v1.json").read_bytes()
    digest = "506f60fab96c30875be1a54ab0cc29eb46477cec66cb7f12f3c595eeda860e69"
    assert hashlib.sha256(raw).hexdigest() == digest
    counts = dict(zip(SECTIONS, [1, 2, 2, 1, 2, 1, 1, 0], strict=True))
    reference = ResultRef(research_id="study", scope_version=1, revision=1, sha256=digest, counts=counts)
    path = get_paths().thread_dir("research-thread", user_id="default") / "research/study/scope-1" / f"{digest}.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    result = load_result(reference, user_id="default", thread_id="research-thread", agent_name="researcher")
    assert result.products[0].discovery_source_ids == () and result.products[0].scope_name is None
    assert result.products[0].reason is None
    batch = ResearchBatch(gaps=[{"id": "new-gap", "reason": "unverified", "description": "旧数据未重新核实"}])
    validate_research_plan(scope(), apply_batch(result, batch), batch)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("case", ["unsupported_specification", "invented_requirement"])
def test_live_quality_rubric_rejects_the_two_observed_semantic_errors(case):
    from test_research_planning_live import assert_controlled_plan_quality

    artifact = {
        "case": "phone" if case == "unsupported_specification" else "laptop-shortage",
        "scope": {"objective": "摄影或便携开发，不指定内存下限"},
        "result": {
            "products": [{"id": "p", "reason": "电池5120mAh" if case == "unsupported_specification" else "便携候选"}],
            "sources": [{"product_id": "p", "text": "电池5000mAh"}],
            "gaps": [{"description": "价格未提供" if case == "unsupported_specification" else "原始意图要求32GB内存，但只有16GB"}],
        },
    }
    with pytest.raises(AssertionError):
        assert_controlled_plan_quality(artifact)
    artifact["result"]["products"][0]["reason"] = "电池5000mAh" if case == "unsupported_specification" else "便携候选"
    artifact["result"]["gaps"][0]["description"] = "价格未提供"
    assert_controlled_plan_quality(artifact)
