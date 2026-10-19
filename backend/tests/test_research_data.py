"""Research data contract tested with synthetic observations through public APIs."""

import copy
from decimal import Decimal

import pytest
from support.research_samples import sample_batch


@pytest.mark.parametrize("category, expected", [("phone", Decimal("190")), ("laptop", Decimal("1.4"))])
def test_cross_category_data_round_trip(category, expected):
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    original = ResearchResult(research_id="study", scope_version=1, user_id="user", thread_id="thread", agent_name="researcher")
    result = apply_batch(original, ResearchBatch.model_validate(sample_batch(category)))
    restored = ResearchResult.model_validate_json(result.model_dump_json())
    assert restored == result
    assert restored.revision == 1
    assert restored.claims[0].value == expected
    assert isinstance(restored.claims[0].value, Decimal)
    assert restored.claims[1].value is None
    assert original.revision == 0 and original.products == ()


@pytest.mark.parametrize(
    "section,index,field,value",
    [
        ("claims", 0, "configuration_id", "absent"),
        ("claims", 0, "dimension_id", "absent"),
        ("claims", 0, "unit", "kg"),
        ("claims", 0, "value", True),
        ("claims", 0, "value", float("nan")),
        ("claims", 0, "value", "Infinity"),
        ("claims", 0, "value", ""),
        ("claims", 0, "verified", True),
        ("claims", 1, "missing_reason", None),
        ("sources", 0, "collected_at", "2026-10-19T08:00:00"),
        ("sources", 0, "collected_at", True),
        ("sources", 0, "url", "file:///private"),
        ("sources", 0, "configuration_ids", ["other"]),
        ("sources", 0, "product_id", "missing"),
        ("sources", 0, "status", "failed"),
        ("citations", 0, "quote", "来源里没有这个句子"),
        ("citations", 0, "quote", "x" * 4001),
        ("citations", 0, "claim_id", "absent"),
        ("products", 0, "id", "../escape"),
    ],
)
def test_invalid_batch_never_changes_original(section, index, field, value):
    from pydantic import ValidationError

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, ResearchResult, apply_batch

    original = ResearchResult(research_id="study", scope_version=1, user_id="user", thread_id="thread", agent_name="researcher")
    batch = sample_batch()
    batch[section][index][field] = value
    with pytest.raises((ValidationError, DataRuleError)):
        apply_batch(original, ResearchBatch.model_validate(batch))
    assert original.revision == 0 and original.claims == ()


def test_duplicate_ids_and_missing_citations_are_rejected():
    from pydantic import ValidationError

    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    values = sample_batch()
    values["products"].append(copy.deepcopy(values["products"][0]))
    with pytest.raises(ValidationError, match="重复"):
        ResearchBatch.model_validate(values)
    values = sample_batch()
    values["citations"] = []
    with pytest.raises(ValidationError, match="引用来源"):
        apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(values))


def test_zero_is_known_and_old_launch_price_keeps_its_basis():
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    batch = sample_batch()
    batch["dimensions"][1]["kind"] = "price"
    price = batch["claims"][1]
    price.pop("missing_reason")
    price["value"] = "0"
    price["price"] = {"amount": "0", "region": "中国大陆", "currency": "CNY", "channel": "合成官网", "seller": "合成商家", "basis": "launch", "conditions": "仅合成历史资料", "observed_at": "2026-10-19T08:00:00+08:00"}
    batch["sources"][0]["text"] += " 历史首发价 0 CNY。"
    batch["citations"].append({"id": "price-citation", "claim_id": "unknown-price", "source_id": "source", "quote": "历史首发价 0 CNY", "locator": "历史价格段"})
    original = ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a")
    result = apply_batch(original, ResearchBatch.model_validate(batch))
    assert result.claims[1].value == Decimal("0")
    assert result.claims[1].price.basis == "launch"
    assert result.claims[1].missing_reason is None
    del batch["claims"][1]["price"]
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="价格"):
        apply_batch(original, ResearchBatch.model_validate(batch))


def test_conflicting_observations_and_inference_keep_separate_evidence():
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    batch = sample_batch()
    batch["sources"].append({**batch["sources"][0], "id": "second-source", "kind": "review", "text": "合成评测：重量 200 g，可能含保护壳。"})
    batch["claims"].extend(
        [
            {**batch["claims"][0], "id": "second-weight", "value": "200", "conditions": "可能含保护壳"},
            {"id": "inference", "kind": "inference", "product_id": "product", "configuration_id": "base", "dimension_id": "weight", "value": "测量条件不同，暂不能统一重量", "unit": "g", "basis_claim_ids": ["weight-fact", "second-weight"]},
        ]
    )
    batch["citations"].append({"id": "second-citation", "claim_id": "second-weight", "source_id": "second-source", "quote": "重量 200 g", "locator": "评测段"})
    batch["conflicts"] = [{"id": "weight-conflict", "claim_ids": ["weight-fact", "second-weight"], "description": "合成不同条件数据，保留两种说法"}]
    result = apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(batch))
    assert result.claims[0].value == Decimal("190")
    assert result.claims[2].value == Decimal("200")
    assert result.conflicts[0].claim_ids == ("weight-fact", "second-weight")
    assert result.claims[3].basis_claim_ids == ("weight-fact", "second-weight")


def test_upsert_revalidates_existing_citations_without_partial_changes():
    from pydantic import ValidationError

    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    original = apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(sample_batch()))
    with pytest.raises(ValidationError, match="摘录"):
        apply_batch(original, ResearchBatch(sources=[{**original.sources[0].model_dump(), "text": "不能破坏既有引用"}]))
    assert original.revision == 1
    assert original.sources[0].text == "合成官方资料：256GB 配置重量 190 g。"
    same = apply_batch(original, ResearchBatch.model_validate(sample_batch()))
    assert len(same.products) == 1 and len(same.claims) == 2


@pytest.mark.parametrize("kind", ["fact", "opinion"])
def test_product_wide_sources_apply_only_when_explicit(kind):
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch

    batch = sample_batch()
    batch["sources"][0].update(configuration_ids=[], product_wide=True)
    batch["claims"][0].update(configuration_id=None, kind=kind)
    result = apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(batch))
    assert result.claims[0].configuration_id is None


def test_failed_source_with_reason_cannot_support_an_existing_citation():
    from pydantic import ValidationError

    from deerflow.agents.research.data import DataRuleError, ResearchBatch, ResearchResult, Source, apply_batch

    original = apply_batch(ResearchResult(research_id="s", scope_version=1, user_id="u", thread_id="t", agent_name="a"), ResearchBatch.model_validate(sample_batch()))
    before = original.model_dump_json()
    failed_source = Source.model_validate({**original.sources[0].model_dump(), "status": "failed", "failure_reason": "合成采集失败：请求超时"})
    assert failed_source.failure_reason is not None
    assert original.citations[0].quote in failed_source.text
    changes = {key for key, value in original.sources[0].model_dump().items() if value != failed_source.model_dump()[key]}
    assert changes == {"status", "failure_reason"}
    batch = ResearchBatch(sources=[failed_source])
    with pytest.raises(ValidationError) as caught:
        apply_batch(original, batch)
    cause = caught.value.errors()[0]["ctx"]["error"]
    assert isinstance(cause, DataRuleError)
    assert cause.code == "unsupported_quote"
    assert cause.field == "citations"
    assert original.model_dump_json() == before
