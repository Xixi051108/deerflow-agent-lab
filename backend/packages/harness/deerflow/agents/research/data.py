"""Offline, category-neutral research records. Structural validity is not verification."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl, model_validator

from deerflow.agents.research.scope import Money, PositiveInt, Text

MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024
MAX_PROJECTION_BYTES = 16 * 1024
MAX_READ_BYTES = 16 * 1024
MAX_QUOTE_CHARS = 4000
Id = Annotated[str, Field(strict=True, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
Revision = Annotated[int, Field(strict=True, ge=0)]
Section = Literal["products", "configurations", "dimensions", "sources", "claims", "citations", "gaps", "conflicts"]
SECTIONS = ("products", "configurations", "dimensions", "sources", "claims", "citations", "gaps", "conflicts")


class DataRuleError(ValueError):
    def __init__(self, code: str, field: str, message: str):
        super().__init__(message)
        self.code, self.field, self.message = code, field, message


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


def _scalar(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("值必须是有限数值、非空文字或 null，不能是布尔值")
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("未知值使用 null 和 missing_reason")
        try:
            number = Decimal(value)
        except InvalidOperation:
            return value
    else:
        number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("数值必须有限")
    return number


def _timestamp(value: object) -> object:
    if not isinstance(value, (str, datetime)):
        raise ValueError("时间必须是带时区的 ISO 时间或 datetime")
    return value


Scalar = Annotated[Decimal | str | None, BeforeValidator(_scalar)]
Timestamp = Annotated[AwareDatetime, BeforeValidator(_timestamp)]


class Product(Record):
    id: Id
    name: Text
    brand: Text | None = None
    model: Text | None = None
    disposition: Literal["candidate", "excluded"] = "candidate"
    reason: Text | None = None
    scope_name: Text | None = None
    discovery_source_ids: tuple[Id, ...] = ()

    @model_validator(mode="after")
    def exclusion_reason(self) -> Self:
        if self.disposition == "excluded" and self.reason is None:
            raise ValueError("排除候选必须说明原因")
        return self


class Configuration(Record):
    id: Id
    product_id: Id
    label: Text | None = None
    attributes: dict[Text, Text | None] = Field(default_factory=dict)


class Dimension(Record):
    id: Id
    name: Text
    kind: Literal["measurement", "qualitative", "price"] = "measurement"
    description: Text | None = None
    unit: Text | None = None
    basis: Text


class SourceCapture(Record):
    """Server-authored capture position; proof of observation, not semantic truth."""

    group_id: Id
    segment_index: Revision
    start_char: Revision
    end_char: Revision
    total_chars: Revision
    truncation_reason: Text | None = None

    @model_validator(mode="after")
    def position(self) -> Self:
        if not self.start_char <= self.end_char <= self.total_chars:
            raise ValueError("采集片段位置不合法")
        return self


class Source(Record):
    id: Id
    url: HttpUrl
    title: Text
    kind: Literal["official", "review", "retailer", "user_review", "other"]
    status: Literal["available", "truncated", "failed", "unknown"]
    collected_at: Timestamp
    published_at: Timestamp | None = None
    text: str | None = None
    product_id: Id
    configuration_ids: tuple[Id, ...] = ()
    product_wide: bool = Field(default=False, strict=True)
    failure_reason: Text | None = None
    capture: SourceCapture | None = None

    @model_validator(mode="after")
    def applicability(self) -> Self:
        if self.product_wide == bool(self.configuration_ids):
            raise ValueError("来源须明确为产品级或指定配置级")
        if len(set(self.configuration_ids)) != len(self.configuration_ids):
            raise ValueError("来源配置不能重复")
        if self.status in {"failed", "unknown"} and self.failure_reason is None:
            raise ValueError("不可用来源需要原因")
        if self.capture is not None and self.capture.end_char - self.capture.start_char != len(self.text or ""):
            raise ValueError("采集片段长度与正文不一致")
        return self


class Price(Record):
    amount: Money
    region: Text
    currency: Annotated[str, Field(strict=True, pattern=r"^[A-Z]{3}$")]
    channel: Text
    seller: Text
    basis: Literal["launch", "list", "public_offer", "promotion", "member", "subsidized", "used"]
    conditions: Text
    observed_at: Timestamp


class Claim(Record):
    id: Id
    kind: Literal["fact", "opinion", "inference"]
    product_id: Id
    configuration_id: Id | None = None
    dimension_id: Id
    value: Scalar
    unit: Text | None = None
    conditions: Text | None = None
    missing_reason: Text | None = None
    basis_claim_ids: tuple[Id, ...] = ()
    price: Price | None = None
    original_value: Scalar = None
    original_unit: Text | None = None

    @model_validator(mode="after")
    def meaning(self) -> Self:
        if (self.value is None) != (self.missing_reason is not None):
            raise ValueError("仅未知值必须填写 missing_reason")
        if self.price is not None and (not isinstance(self.value, Decimal) or self.value != self.price.amount or self.unit != self.price.currency or self.configuration_id is None or self.kind != "fact"):
            raise ValueError("价格必须是对应明确配置、币种和金额的事实")
        if self.kind == "inference":
            if not self.basis_claim_ids or self.value is None:
                raise ValueError("推断必须有值和依据")
        elif self.basis_claim_ids:
            raise ValueError("只有推断使用 basis_claim_ids")
        if (self.original_value is None) != (self.original_unit is None) or (
            self.original_value is not None and (not isinstance(self.original_value, Decimal) or not isinstance(self.value, Decimal) or self.unit is None or self.price is not None)
        ):
            raise ValueError("单位换算须保留原数值和单位，且只用于明确的非价格数值")
        return self


class Citation(Record):
    id: Id
    claim_id: Id
    source_id: Id
    quote: Annotated[str, Field(strict=True, min_length=1, max_length=MAX_QUOTE_CHARS)]
    locator: Text


class Gap(Record):
    id: Id
    product_id: Id | None = None
    configuration_id: Id | None = None
    dimension_id: Id | None = None
    reason: Text
    description: Text


class Conflict(Record):
    id: Id
    claim_ids: tuple[Id, ...] = Field(min_length=2)
    description: Text


class ResearchBatch(Record):
    products: tuple[Product, ...] = ()
    configurations: tuple[Configuration, ...] = ()
    dimensions: tuple[Dimension, ...] = ()
    sources: tuple[Source, ...] = ()
    claims: tuple[Claim, ...] = ()
    citations: tuple[Citation, ...] = ()
    gaps: tuple[Gap, ...] = ()
    conflicts: tuple[Conflict, ...] = ()

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        seen = set()
        for section in SECTIONS:
            for row in getattr(self, section):
                if row.id in seen:
                    raise DataRuleError("duplicate_id", section, f"重复记录标识：{row.id}")
                seen.add(row.id)
        return self


class ResearchResult(ResearchBatch):
    schema_version: Literal[1] = 1
    research_id: Id
    scope_version: PositiveInt
    revision: Revision = 0
    user_id: Text
    thread_id: Text
    agent_name: Text

    @model_validator(mode="after")
    def references(self) -> Self:
        products = {p.id: p for p in self.products}
        configurations = {c.id: c for c in self.configurations}
        dimensions = {d.id: d for d in self.dimensions}
        sources = {s.id: s for s in self.sources}
        claims = {c.id: c for c in self.claims}

        def target(row, field):
            product_id, configuration_id = row.product_id, getattr(row, "configuration_id", None)
            if product_id is not None and product_id not in products:
                raise DataRuleError("dangling_reference", field, "产品不存在")
            if configuration_id is not None and (configuration_id not in configurations or configurations[configuration_id].product_id != product_id):
                raise DataRuleError("configuration_mismatch", field, "配置不属于对应产品")
            dimension_id = getattr(row, "dimension_id", None)
            if dimension_id is not None and dimension_id not in dimensions:
                raise DataRuleError("dangling_reference", field, "维度不存在")

        for configuration in self.configurations:
            if configuration.product_id not in products:
                raise DataRuleError("dangling_reference", "configurations", "配置对应的产品不存在")
        for source in self.sources:
            target(source, "sources")
            for config_id in source.configuration_ids:
                if config_id not in configurations or configurations[config_id].product_id != source.product_id:
                    raise DataRuleError("configuration_mismatch", "sources", "来源配置不属于对应产品")
        for product in self.products:
            if len(set(product.discovery_source_ids)) != len(product.discovery_source_ids):
                raise DataRuleError("duplicate_reference", "products", "发现来源标识不能重复")
            for source_id in product.discovery_source_ids:
                if source_id not in sources:
                    raise DataRuleError("dangling_reference", "products", "候选的发现来源不存在")
                if sources[source_id].product_id != product.id:
                    raise DataRuleError("discovery_source_mismatch", "products", "发现来源不属于对应产品")
        supported = set()
        for citation in self.citations:
            if citation.claim_id not in claims or citation.source_id not in sources:
                raise DataRuleError("dangling_reference", "citations", "引用对应的事实或来源不存在")
            claim, source = claims[citation.claim_id], sources[citation.source_id]
            if claim.value is None or claim.kind == "inference":
                raise DataRuleError("invalid_citation", "citations", "未知值或推断不能伪装成直接来源事实")
            if claim.product_id != source.product_id or (not source.product_wide and claim.configuration_id not in source.configuration_ids):
                raise DataRuleError("configuration_mismatch", "citations", "引用不适用于对应产品或配置")
            if source.status not in {"available", "truncated"} or not source.text or not citation.quote.strip() or citation.quote not in source.text:
                raise DataRuleError("unsupported_quote", "citations", "摘录不在可用来源文本中")
            supported.add(claim.id)
        for claim in self.claims:
            target(claim, "claims")
            if claim.kind == "fact" and claim.value is not None and (dimensions[claim.dimension_id].kind == "price") != (claim.price is not None):
                raise DataRuleError("invalid_price", "claims", "已知价格必须携带价格口径，其他维度不能携带价格")
            if claim.unit != dimensions[claim.dimension_id].unit:
                raise DataRuleError("unit_mismatch", f"claims.{claim.id}.unit", f"事实单位须为维度 {claim.dimension_id} 的 {dimensions[claim.dimension_id].unit!r}；不同属性请另建维度，不改其他事实的单位")
            if claim.value is not None and claim.kind != "inference" and claim.id not in supported:
                raise DataRuleError("missing_citation", "claims", "已知事实或评价必须引用来源")
            for basis_id in claim.basis_claim_ids:
                basis = claims.get(basis_id)
                if basis is None or basis.kind == "inference" or basis.value is None:
                    raise DataRuleError("invalid_inference_basis", "claims", "推断须基于已有已知事实或评价")
        for gap in self.gaps:
            target(gap, "gaps")
        for conflict in self.conflicts:
            if len(set(conflict.claim_ids)) != len(conflict.claim_ids) or any(i not in claims for i in conflict.claim_ids):
                raise DataRuleError("dangling_reference", "conflicts", "冲突必须关联不同的已有事实")
            related = [claims[i] for i in conflict.claim_ids]
            if len({(c.product_id, c.configuration_id, c.dimension_id) for c in related}) != 1:
                raise DataRuleError("configuration_mismatch", "conflicts", "冲突须对应同一产品、配置与维度")
        return self


class ResultRef(Record):
    schema_version: Literal[1] = 1
    research_id: Id
    scope_version: PositiveInt
    revision: PositiveInt
    sha256: Annotated[str, Field(strict=True, pattern=r"^[a-f0-9]{64}$")]
    counts: dict[Section, Revision]
    preview: tuple[Text, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if set(self.counts) != set(SECTIONS):
            raise ValueError("结果索引须包含所有集合的计数")
        if len(self.model_dump_json().encode("utf-8")) > MAX_PROJECTION_BYTES:
            raise ValueError("结果状态投影超过 16 KiB")
        return self


def apply_batch(result: ResearchResult, batch: ResearchBatch) -> ResearchResult:
    """Validate a whole merged result before returning an immutable replacement."""
    result = ResearchResult.model_validate(result)
    batch = ResearchBatch.model_validate(batch)
    values = result.model_dump()
    for section in SECTIONS:
        merged = {row.id: row.model_dump() for row in getattr(result, section)}
        merged.update({row.id: row.model_dump() for row in getattr(batch, section)})
        values[section] = list(merged.values())
    values["revision"] = result.revision + 1
    return ResearchResult.model_validate(values)
