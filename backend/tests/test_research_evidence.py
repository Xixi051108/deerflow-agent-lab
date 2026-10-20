"""Evidence rules at the validated research-write and assessment boundaries."""

import pytest
from support.research_discovery_samples import planning_batch

from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch


def original_result():
    return apply_batch(ResearchResult(research_id="study", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(planning_batch()))


def captured_source():
    source = planning_batch()["sources"][0]
    source.update(id="captured", text="极光 A1 8GB/256GB 全新公开售价 3299 CNY，合成自营，无会员条件。", kind="retailer", product_wide=False, configuration_ids=["c1"])
    source["capture"] = dict(group_id="capture-1", segment_index=0, start_char=0, end_char=len(source["text"]), total_chars=len(source["text"]))
    return source


def test_model_cannot_mint_a_server_capture_by_copying_its_shape():
    from deerflow.agents.research.evidence import validate_evidence_write

    before = original_result()
    batch = ResearchBatch.model_validate({"sources": [captured_source()]})
    merged = apply_batch(before, batch)
    with pytest.raises(ValueError, match="服务端采集") as error:
        validate_evidence_write(before, merged, batch)
    assert error.value.code == "capture_read_only"
    assert before.revision == 1


def price_batch(basis="public_offer", **price_changes):
    return ResearchBatch.model_validate(
        {
            "claims": [
                {
                    "id": "offer",
                    "kind": "fact",
                    "product_id": "p1",
                    "configuration_id": "c1",
                    "dimension_id": "price",
                    "value": "3299",
                    "unit": "CNY",
                    "price": {"amount": "3299", "region": "中国大陆", "currency": "CNY", "channel": "合成商城", "seller": "合成自营", "basis": basis, "conditions": "无会员要求", "observed_at": "2026-10-20T10:00:00+08:00", **price_changes},
                }
            ],
            "citations": [{"id": "offer-cite", "claim_id": "offer", "source_id": "captured", "quote": "公开售价 3299 CNY", "locator": "销售段"}],
        }
    )


@pytest.mark.parametrize(
    "basis,status", [("public_offer", "captured_offer_observation"), ("member", "conditional_price"), ("subsidized", "conditional_price"), ("launch", "historical_or_list_price"), ("list", "historical_or_list_price"), ("used", "used_price")]
)
def test_price_assessment_keeps_basis_and_requires_semantic_review(basis, status):
    from support.research_discovery_samples import discovery_scope

    from deerflow.agents.research.evidence import assess_claim_evidence, validate_evidence_write

    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [captured_source()]}))
    batch = price_batch(basis)
    result = apply_batch(before, batch)
    validate_evidence_write(before, result, batch)
    assessment = assess_claim_evidence(discovery_scope(), result, "offer")
    assert assessment["status"] == status
    assert assessment["semantic_review_required"] is True
    assert assessment["capture_groups"] == ["capture-1"]
    assert "verified" not in assessment


@pytest.mark.parametrize("changes,reason", [({"region": "其他地区"}, "market_mismatch"), ({"observed_at": "2026-10-19T10:00:00+08:00"}, "observation_time_mismatch")])
def test_inapplicable_price_is_not_promoted_to_current_offer(changes, reason):
    from support.research_discovery_samples import discovery_scope

    from deerflow.agents.research.evidence import assess_claim_evidence

    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [captured_source()]}))
    result = apply_batch(before, price_batch(**changes))
    assessment = assess_claim_evidence(discovery_scope(), result, "offer")
    assert assessment["status"] == "unverified_price"
    assert assessment["reason"] == reason


def test_new_known_price_cannot_use_model_submitted_page_text():
    from deerflow.agents.research.evidence import validate_evidence_write

    source = captured_source()
    source.pop("capture")
    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [source]}))
    batch = price_batch()
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == "price_requires_capture"


@pytest.mark.parametrize("change", [{"capture": None}, {"text": "X" * len(captured_source()["text"])}, {"configuration_ids": [], "product_wide": True}, {"kind": "official"}])
def test_existing_capture_cannot_be_replaced_or_downgraded(change):
    from deerflow.agents.research.evidence import validate_evidence_write

    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [captured_source()]}))
    batch = ResearchBatch.model_validate({"sources": [{**captured_source(), **change}]})
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == "capture_read_only"


@pytest.mark.parametrize("value,source_unit,target_unit,expected", [("190", "g", "kg", "0.190"), ("1.35", "kg", "g", "1350"), ("1024", "MiB", "GiB", "1"), ("1", "GB", "MB", "1000")])
def test_explicit_decimal_unit_conversion(value, source_unit, target_unit, expected):
    from decimal import Decimal

    from deerflow.agents.research.evidence import convert_measurement

    assert convert_measurement(Decimal(value), source_unit, target_unit) == Decimal(expected)


@pytest.mark.parametrize("source_unit,target_unit", [("mAh", "Wh"), ("GB", "GiB"), ("hours gaming", "hours idle")])
def test_incomparable_units_require_a_separate_basis(source_unit, target_unit):
    from decimal import Decimal

    from deerflow.agents.research.evidence import convert_measurement

    with pytest.raises(ValueError) as error:
        convert_measurement(Decimal("10"), source_unit, target_unit)
    assert error.value.code == "incomparable_unit"


def test_divergent_same_condition_facts_need_explicit_conflict_and_cannot_overwrite():
    from support.research_samples import sample_batch

    from deerflow.agents.research.evidence import validate_evidence_write

    before = apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(sample_batch()))
    source = {**sample_batch()["sources"][0], "id": "second-source", "text": "同配置重量 200 g"}
    claim = {**sample_batch()["claims"][0], "id": "second-weight", "value": "200"}
    batch = ResearchBatch.model_validate({"sources": [source], "claims": [claim], "citations": [{"id": "second-cite", "source_id": "second-source", "claim_id": "second-weight", "quote": "重量 200 g", "locator": "测量段"}]})
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == "conflict_required"
    resolved = ResearchBatch.model_validate({**batch.model_dump(), "conflicts": [{"id": "weight-conflict", "claim_ids": ["weight-fact", "second-weight"], "description": "同配置及标称条件下说法不同，暂不选择单一数值"}]})
    validate_evidence_write(before, apply_batch(before, resolved), resolved)
    overwrite = ResearchBatch.model_validate({"claims": [{**claim, "id": "weight-fact", "value": "190", "conditions": "改变原条件"}]})
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, overwrite), overwrite)
    assert error.value.code == "observation_read_only"


@pytest.mark.parametrize("value,code", [("0.190", None), ("0.200", "conversion_mismatch")])
def test_normalized_fact_keeps_and_checks_its_original_unit(value, code):
    from deerflow.agents.research.evidence import validate_evidence_write

    source = captured_source()
    source["text"] = "极光 A1 整机重量 190 g。"
    source["capture"].update(end_char=len(source["text"]), total_chars=len(source["text"]))
    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [source], "dimensions": [{"id": "mass", "name": "重量", "unit": "kg", "basis": "整机重量"}]}))
    batch = ResearchBatch.model_validate(
        {
            "claims": [{"id": "mass-fact", "kind": "fact", "product_id": "p1", "configuration_id": "c1", "dimension_id": "mass", "value": value, "unit": "kg", "original_value": "190", "original_unit": "g"}],
            "citations": [{"id": "mass-cite", "source_id": "captured", "claim_id": "mass-fact", "quote": "重量 190 g", "locator": "规格段"}],
        }
    )
    if code:
        with pytest.raises(ValueError) as error:
            validate_evidence_write(before, apply_batch(before, batch), batch)
        assert error.value.code == code
    else:
        validate_evidence_write(before, apply_batch(before, batch), batch)


def test_citation_only_update_cannot_rebind_a_saved_price_to_unbound_text():
    from deerflow.agents.research.evidence import validate_evidence_write

    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [captured_source()]}))
    before = apply_batch(before, price_batch())
    source = {**captured_source(), "id": "unbound", "capture": None}
    batch = ResearchBatch.model_validate({"sources": [source], "citations": [{"id": "offer-cite", "claim_id": "offer", "source_id": "unbound", "quote": "公开售价 3299 CNY", "locator": "sales"}]})
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == "citation_read_only"


def test_unit_error_identifies_the_fact_and_expected_dimension_unit():
    from support.research_samples import sample_batch

    batch = sample_batch()
    batch["claims"][0]["unit"] = "kg"
    with pytest.raises(ValueError) as error:
        apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(batch))
    cause = error.value.errors()[0]["ctx"]["error"]
    assert cause.code == "unit_mismatch"
    assert cause.field == "claims.weight-fact.unit"
    assert "g" in str(cause)


def test_structural_price_checks_do_not_certify_the_meaning_of_a_quote():
    from support.research_discovery_samples import discovery_scope

    from deerflow.agents.research.evidence import assess_claim_evidence, validate_evidence_write

    source = captured_source()
    source["text"] = "极光 A1 8GB/256GB 公开售价并非3299 CNY，正确金额另查。"
    source["capture"].update(end_char=len(source["text"]), total_chars=len(source["text"]))
    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [source]}))
    raw = price_batch().model_dump(mode="json")
    raw["citations"][0]["quote"] = "公开售价并非3299 CNY"
    batch = ResearchBatch.model_validate(raw)
    result = apply_batch(before, batch)
    # The amount occurs, but negation makes the assertion semantically WRONG.
    # A structural pass must stay explicitly reviewable, never become verified.
    validate_evidence_write(before, result, batch)
    assessment = assess_claim_evidence(discovery_scope(), result, "offer")
    assert assessment["semantic_review_required"] is True
    assert "verified" not in assessment


@pytest.mark.parametrize("changes,code", [({"observed_at": "2026-10-19T10:00:00+08:00"}, "observation_time_mismatch"), ({"amount": "3298"}, "price_amount_unsupported")])
def test_new_price_rejects_time_and_amount_not_supported_by_capture(changes, code):
    from deerflow.agents.research.evidence import validate_evidence_write

    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [captured_source()]}))
    raw = price_batch(**changes).model_dump(mode="json") if "amount" not in changes else price_batch().model_dump(mode="json")
    if "amount" in changes:
        raw["claims"][0]["price"]["amount"] = raw["claims"][0]["value"] = changes["amount"]
    batch = ResearchBatch.model_validate(raw)
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == code


def test_unknown_price_needs_reason_but_does_not_invent_a_zero_amount():
    from support.research_discovery_samples import discovery_scope

    from deerflow.agents.research.evidence import assess_claim_evidence, validate_evidence_write

    before = original_result()
    batch = ResearchBatch(claims=[{"id": "unknown-price", "kind": "fact", "product_id": "p1", "configuration_id": "c1", "dimension_id": "price", "unit": "CNY", "value": None, "missing_reason": "公开销售页面未提供对应配置报价"}])
    result = apply_batch(before, batch)
    validate_evidence_write(before, result, batch)
    assert assess_claim_evidence(discovery_scope(), result, "unknown-price")["status"] == "unknown"
    assert result.claims[0].value is None and result.claims[0].price is None


def test_captured_numeric_fact_cannot_silently_normalize_an_unsupported_unit():
    from deerflow.agents.research.evidence import validate_evidence_write

    source = captured_source()
    source["text"] = "极光 A1 存储容量1TB。"
    source["capture"].update(end_char=len(source["text"]), total_chars=len(source["text"]))
    before = apply_batch(original_result(), ResearchBatch.model_validate({"sources": [source], "dimensions": [{"id": "storage", "name": "存储容量", "unit": "GB", "basis": "声明容量"}]}))
    batch = ResearchBatch(
        claims=[{"id": "storage-fact", "kind": "fact", "product_id": "p1", "configuration_id": "c1", "dimension_id": "storage", "value": "1000", "unit": "GB"}],
        citations=[{"id": "storage-cite", "claim_id": "storage-fact", "source_id": "captured", "quote": "容量1TB", "locator": "规格"}],
    )
    with pytest.raises(ValueError) as error:
        validate_evidence_write(before, apply_batch(before, batch), batch)
    assert error.value.code == "measurement_amount_unsupported"
