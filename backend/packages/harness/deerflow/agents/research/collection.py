"""Bounded public-page observations, saved by the existing research tool chain."""

from datetime import UTC, datetime
from uuid import uuid4

from deerflow.agents.research.data import DataRuleError, Source, SourceCapture
from deerflow.community.jina_ai.jina_client import JinaClient
from deerflow.community.jina_ai.tools import _coerce_bool, _coerce_proxy, _coerce_timeout
from deerflow.config import get_app_config
from deerflow.utils.file_io import run_file_io
from deerflow.utils.readability import ReadabilityExtractor

MAX_CAPTURE_TEXT_BYTES = 128 * 1024
MAX_SOURCE_BYTES = 8192


async def collect_sources(*, url: str, product_id: str, configuration_ids: tuple[str, ...] = (), product_wide: bool = False, kind: str = "other") -> tuple[Source, ...]:
    """Return server-authored observations, including explicit failures.

    The caller owns confirmation, authorization, URL admission and persistence.
    A Reader response is not proof of seller identity, freshness or claim support.
    """
    config = (await run_file_io(get_app_config)).get_tool_config("web_fetch")
    extras = config.model_extra if config else {}
    response = await JinaClient().crawl_bounded(url, timeout=max(1, min(60, _coerce_timeout(extras.get("timeout"), 10))), proxy=_coerce_proxy(extras.get("proxy")), trust_env=_coerce_bool(extras.get("trust_env"), True))
    collected = datetime.now(UTC)
    group = "cap-" + uuid4().hex
    title, text, failure = "Untitled (captured response)", "", response.error
    if failure is None:
        try:
            article = await run_file_io(ReadabilityExtractor().extract_article, response.content, url=url)
            title = str(article.title)[:200]
            if article.html_content in {None, "No content could be extracted from this page", "No content available"}:
                failure = "extraction_empty"
            else:
                text = await run_file_io(article.to_markdown)
                if not text.strip():
                    failure = "extraction_empty"
        except (ValueError, OSError, RuntimeError):
            failure = "extraction_failed"
    raw = text.encode("utf-8")
    truncated = len(raw) > MAX_CAPTURE_TEXT_BYTES
    if truncated:
        text = raw[:MAX_CAPTURE_TEXT_BYTES].decode("utf-8", errors="ignore")
    common = dict(url=url, title=title, kind=kind, collected_at=collected, product_id=product_id, configuration_ids=configuration_ids, product_wide=product_wide, failure_reason=failure)
    sources, start = [], 0
    while start < len(text) or not sources:
        end = min(len(text), start + 1800)
        while True:
            capture = SourceCapture(group_id=group, segment_index=len(sources), start_char=start, end_char=end, total_chars=len(text), truncation_reason="text_limit" if truncated else "segmented" if start or end < len(text) else None)
            source = Source(id=f"{group}-{len(sources)}", text=text[start:end] or None, status="failed" if failure else "truncated" if capture.truncation_reason else "available", capture=capture, **common)
            if len(source.model_dump_json().encode("utf-8")) <= MAX_SOURCE_BYTES:
                break
            if end == start:
                raise DataRuleError("source_metadata_too_large", "sources", "来源元数据超过单条容量")
            end = start + (end - start) // 2
        sources.append(source)
        if end == len(text):
            return tuple(sources)
        if end == start:
            raise DataRuleError("source_metadata_too_large", "sources", "来源元数据未留出正文空间")
        start = end
