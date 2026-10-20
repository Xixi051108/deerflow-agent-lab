"""Public research capture boundary, with only HTTP transport replaced."""

import httpx
import pytest


@pytest.mark.asyncio
async def test_capture_preserves_long_page_tail_and_supports_existing_pages(monkeypatch):
    from deerflow.agents.research.collection import collect_sources
    from deerflow.agents.research.data import ResearchBatch, ResearchResult, apply_batch
    from deerflow.agents.research.storage import read_page

    html = "<html><head><title>合成销售页</title></head><body><article>" + "<p>公开销售说明，配置及条件应核对。</p>" * 450 + "<p>极光 A1 8GB/256GB，公开售价 3299 CNY，卖家：合成自营，无会员要求。</p></article></body></html>"
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html)), **kwargs))
    sources = await collect_sources(url="https://example.com/sales", product_id="p1", configuration_ids=("c1",), kind="retailer")
    result = apply_batch(
        ResearchResult(research_id="study", scope_version=1, user_id="u", thread_id="t", agent_name="a"),
        ResearchBatch.model_validate({"products": [{"id": "p1", "name": "极光 A1"}], "configurations": [{"id": "c1", "product_id": "p1"}], "sources": sources}),
    )
    saved_text, offset = "", 0
    while True:
        page = read_page(result, "sources", offset=offset)
        saved_text += "".join(row["text"] or "" for row in page["records"])
        if page["next_offset"] is None:
            break
        offset = page["next_offset"]
    assert "公开售价 3299 CNY" in saved_text
    assert len(sources) > 1
    assert sources[0].capture.group_id == sources[-1].capture.group_id
    assert sources[0].capture.start_char == 0
    assert sources[-1].capture.end_char == len(saved_text)
    assert sources[0].collected_at.tzinfo is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["429", "timeout", "empty", "extraction"])
async def test_capture_failures_are_explicit_and_do_not_include_provider_error_body(monkeypatch, failure):
    from deerflow.agents.research.collection import collect_sources

    def respond(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("sensitive provider detail")
        return httpx.Response(429 if failure == "429" else 200, text="sensitive provider detail" if failure == "429" else "" if failure == "empty" else "<html><body></body></html>")

    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    sources = await collect_sources(url="https://example.com/page", product_id="p", product_wide=True)
    assert len(sources) == 1
    source = sources[0]
    assert source.status == "failed"
    assert source.failure_reason == {"429": "reader_http_429", "timeout": "request_timeout", "empty": "empty_response", "extraction": "extraction_empty"}[failure]
    assert source.text is None
    assert "sensitive" not in source.model_dump_json()
    assert source.capture.total_chars == 0


@pytest.mark.asyncio
async def test_bounded_reader_stops_streaming_before_accumulating_large_body(monkeypatch):
    from deerflow.community.jina_ai.jina_client import JinaClient

    class LargeStream(httpx.AsyncByteStream):
        chunks = 0
        closed = False

        async def __aiter__(self):
            for _ in range(100):
                self.chunks += 1
                yield b"x" * 8192

        async def aclose(self):
            self.closed = True

    stream = LargeStream()
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)), **kwargs))
    result = await JinaClient().crawl_bounded("https://example.com/page", max_bytes=16384)
    assert result.error == "response_too_large" and result.content == ""
    assert stream.chunks == 3 and stream.closed


@pytest.mark.asyncio
async def test_text_cap_and_unicode_segments_are_explicit_and_pageable(monkeypatch):
    import json

    from deerflow.agents.research.collection import collect_sources

    html = "<html><head><title>容量样本</title></head><body><article>" + '<p>中文容量与转义"说明\\，持续记录。</p>' * 4000 + "<p>不得取得的尾部4999元</p></article></body></html>"
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html)), **kwargs))
    sources = await collect_sources(url="https://example.com/page", product_id="p", product_wide=True)
    assert all(source.capture.truncation_reason == "text_limit" for source in sources)
    assert all(len(source.model_dump_json().encode("utf-8")) <= 8192 for source in sources)
    text = "".join(source.text for source in sources)
    assert len(text.encode("utf-8")) <= 128 * 1024
    assert "4999" not in text
    assert sources[-1].capture.end_char == sources[-1].capture.total_chars == len(text)
    assert len(json.dumps([s.model_dump(mode="json") for s in sources], ensure_ascii=False)) < 2 * 1024 * 1024


@pytest.mark.asyncio
async def test_reader_total_deadline_covers_a_stream_that_never_finishes(monkeypatch):
    import asyncio

    from deerflow.community.jina_ai.jina_client import JinaClient

    class NeverFinishes(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            yield b"first chunk"
            await asyncio.Event().wait()

        async def aclose(self):
            self.closed = True

    stream = NeverFinishes()
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)), **kwargs))
    # The outer deadline prevents a broken implementation hanging the test.
    result = await asyncio.wait_for(JinaClient().crawl_bounded("https://example.com/page", timeout=0.01), 1)
    assert result.error == "request_timeout" and stream.closed
