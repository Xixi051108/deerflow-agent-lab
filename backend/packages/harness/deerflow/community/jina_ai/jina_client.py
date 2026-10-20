import asyncio
import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_api_key_warned = False


@dataclass(frozen=True)
class CrawlResult:
    content: str = ""
    error: str | None = None
    http_status: int | None = None


class JinaClient:
    async def crawl_bounded(self, url: str, *, max_bytes: int = 512 * 1024, timeout: int = 10, proxy: str | None = None, trust_env: bool = True) -> CrawlResult:
        """Read a bounded Reader response without changing the legacy crawl ABI.

        Errors deliberately exclude provider bodies, credentials and proxy details.
        HTTP status belongs to Reader, not necessarily the original website.
        """
        headers = {"Content-Type": "application/json", "X-Return-Format": "html", "X-Timeout": str(timeout)}
        if key := os.getenv("JINA_API_KEY"):
            headers["Authorization"] = f"Bearer {key}"
        options = {"trust_env": trust_env}
        if proxy:
            options["proxy"] = proxy
        try:
            async with asyncio.timeout(timeout), httpx.AsyncClient(**options) as client:
                async with client.stream("POST", "https://r.jina.ai/", headers=headers, json={"url": url}, timeout=timeout) as response:
                    if response.status_code != 200:
                        return CrawlResult(error=f"reader_http_{response.status_code}", http_status=response.status_code)
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        if len(body) + len(chunk) > max_bytes:
                            return CrawlResult(error="response_too_large", http_status=response.status_code)
                        body.extend(chunk)
                    text = body.decode(response.encoding or "utf-8", errors="replace")
                    return CrawlResult(content=text, http_status=200) if text.strip() else CrawlResult(error="empty_response", http_status=200)
        except (httpx.TimeoutException, TimeoutError):
            return CrawlResult(error="request_timeout")
        except httpx.HTTPError:
            return CrawlResult(error="request_failed")

    async def crawl(self, url: str, return_format: str = "html", timeout: int = 10, proxy: str | None = None, trust_env: bool = True) -> str:
        global _api_key_warned
        headers = {
            "Content-Type": "application/json",
            "X-Return-Format": return_format,
            "X-Timeout": str(timeout),
        }
        if os.getenv("JINA_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('JINA_API_KEY')}"
        elif not _api_key_warned:
            _api_key_warned = True
            logger.warning("Jina API key is not set. Provide your own key to access a higher rate limit. See https://jina.ai/reader for more information.")
        data = {"url": url}
        try:
            client_kwargs: dict[str, object] = {"trust_env": trust_env}
            if proxy:
                client_kwargs["proxy"] = proxy
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post("https://r.jina.ai/", headers=headers, json=data, timeout=timeout)

            if response.status_code != 200:
                error_message = f"Jina API returned status {response.status_code}: {response.text}"
                logger.error(error_message)
                return f"Error: {error_message}"

            if not response.text or not response.text.strip():
                error_message = "Jina API returned empty response"
                logger.error(error_message)
                return f"Error: {error_message}"

            return response.text
        except Exception as e:
            error_message = f"Request to Jina API failed: {type(e).__name__}: {e}"
            logger.warning(error_message)
            return f"Error: {error_message}"
