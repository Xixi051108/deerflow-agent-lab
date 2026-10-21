"""Bounded public-page observations, saved by the existing research tool chain."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from deerflow.agents.research.data import DataRuleError, Source, SourceCapture
from deerflow.community.jina_ai.jina_client import JinaClient
from deerflow.community.jina_ai.tools import _coerce_bool, _coerce_proxy, _coerce_timeout
from deerflow.config import get_app_config
from deerflow.utils.file_io import run_file_io
from deerflow.utils.readability import Article, _resolve_html_urls

MAX_CAPTURE_TEXT_BYTES = 128 * 1024
MAX_SOURCE_BYTES = 8192


def _capture_document(html: str, url: str) -> tuple[str, str]:
    # Research pages include purchase sidebars, specification tables and comments;
    # selecting only an article can discard the configuration and offer itself.
    document = BeautifulSoup(_resolve_html_urls(html, url), "html5lib")
    title = document.title.get_text(" ", strip=True) if document.title else "Untitled"
    for element in document.select("script, style, noscript, template, [hidden], [aria-hidden='true']"):
        element.decompose()
    body = document.body or document
    if not any(character.isalnum() for character in body.get_text()):
        return title, ""
    return title, Article(title, str(body)).to_markdown()


async def _browser_document(url: str, thread_id: str | None) -> tuple[str, str, str | None]:
    from deerflow.community.browser_automation import get_browser_session_manager

    if not thread_id:
        return "Untitled", "", "browser_not_open"
    if (await run_file_io(get_app_config)).get_tool_config("browser_navigate") is None:
        return "Untitled", "", "browser_not_enabled"
    session = get_browser_session_manager().existing_session(thread_id)
    if session is None:
        return "Untitled", "", "browser_not_open"
    try:
        page = await asyncio.wait_for(session.capture_page(), 10)
        if HttpUrl(page["url"]) != HttpUrl(url):
            return "Untitled", "", "browser_url_mismatch"
        text = page["text"]
        return str(page["title"]), text, None if text.strip() else "extraction_empty"
    except TimeoutError:
        return "Untitled", "", "request_timeout"
    except (RuntimeError, ValueError):
        return "Untitled", "", "browser_capture_failed"


async def collect_sources(*, url: str, product_id: str, configuration_ids: tuple[str, ...] = (), product_wide: bool = False, kind: str = "other", method: str = "reader", thread_id: str | None = None) -> tuple[Source, ...]:
    """Return server-authored observations, including explicit failures.

    The caller owns confirmation, authorization, URL admission and persistence.
    A Reader response is not proof of seller identity, freshness or claim support.
    """
    group = "cap-" + uuid4().hex
    if method == "browser":
        title, text, failure = await _browser_document(url, thread_id)
    elif method == "reader":
        config = (await run_file_io(get_app_config)).get_tool_config("web_fetch")
        extras = config.model_extra if config else {}
        response = await JinaClient().crawl_bounded(url, timeout=max(1, min(60, _coerce_timeout(extras.get("timeout"), 10))), proxy=_coerce_proxy(extras.get("proxy")), trust_env=_coerce_bool(extras.get("trust_env"), True))
        title, text, failure = "Untitled (captured response)", "", response.error
        if failure is None:
            try:
                title, text = await run_file_io(_capture_document, response.content, url)
                if not text.strip():
                    failure = "extraction_empty"
            except (ValueError, OSError, RuntimeError):
                failure = "extraction_failed"
    else:
        raise DataRuleError("invalid_capture_method", "method", "采集方式不合法")
    title = title[:200]
    collected = datetime.now(UTC)
    raw = text.encode("utf-8")
    truncated = len(raw) > MAX_CAPTURE_TEXT_BYTES
    if truncated:
        text = raw[:MAX_CAPTURE_TEXT_BYTES].decode("utf-8", errors="ignore")
    common = dict(url=url, title=title, kind=kind, collected_at=collected, product_id=product_id, configuration_ids=configuration_ids, product_wide=product_wide, failure_reason=failure)
    sources, start = [], 0
    while start < len(text) or not sources:
        end = min(len(text), start + 1800)
        while True:
            capture = SourceCapture(
                group_id=group,
                method="browser_dom" if method == "browser" else "jina_reader",
                segment_index=len(sources),
                start_char=start,
                end_char=end,
                total_chars=len(text),
                truncation_reason="text_limit" if truncated else "segmented" if start or end < len(text) else None,
            )
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
