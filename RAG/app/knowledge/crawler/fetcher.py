from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from app.core.config import get_settings
from app.knowledge.crawler.security import canonicalize_url, is_in_scope, validate_public_url


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes
    etag: str | None
    last_modified: str | None


class SafeFetcher:
    def __init__(self, allowed_domains: list[str], allowed_paths: list[str]) -> None:
        self.settings = get_settings()
        self.allowed_domains = allowed_domains
        self.allowed_paths = allowed_paths
        self.client = httpx.AsyncClient(
            timeout=self.settings.crawler_http_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": self.settings.crawler_user_agent, "Accept": "text/html,application/pdf,application/vnd.openxmlformats-officedocument.*,text/csv,text/plain;q=0.8"},
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch(self, raw_url: str, etag: str | None = None,
                    last_modified: str | None = None, enforce_paths: bool = True) -> FetchResult:
        url = canonicalize_url(raw_url)
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        for _ in range(self.settings.crawler_max_redirects + 1):
            paths = self.allowed_paths if enforce_paths else []
            if not is_in_scope(url, self.allowed_domains, paths):
                raise FetchError("URL is outside the approved source scope")
            await validate_public_url(url)
            try:
                async with self.client.stream("GET", url, headers=headers) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError("redirect response has no location")
                        url = canonicalize_url(urljoin(url, location))
                        continue
                    if response.status_code == 304:
                        return FetchResult(url, 304, "", b"", response.headers.get("etag"), response.headers.get("last-modified"))
                    response.raise_for_status()
                    declared = int(response.headers.get("content-length", 0) or 0)
                    if declared > self.settings.crawler_max_response_bytes:
                        raise FetchError("response exceeds the configured byte limit")
                    body = bytearray()
                    async for part in response.aiter_bytes():
                        body.extend(part)
                        if len(body) > self.settings.crawler_max_response_bytes:
                            raise FetchError("response exceeds the configured byte limit")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    return FetchResult(url, response.status_code, content_type, bytes(body),
                                       response.headers.get("etag"), response.headers.get("last-modified"))
            except FetchError:
                raise
            except httpx.HTTPError as exc:
                # A single slow or temporarily unavailable page must be rejected
                # by the worker instead of terminating the complete crawl run.
                raise FetchError(type(exc).__name__) from exc
        raise FetchError("too many redirects")
