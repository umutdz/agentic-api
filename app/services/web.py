import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import config
from app.services.interfaces import ISearchProvider

SearchHit = Dict[str, str]
Page = Dict[str, str]


class WebClient:
    """
    Minimal async web client for ContentAgent.
    - search(query): Delegate to ISearchProvider (RuntimeError if no provider).
    - fetch(url): Get request and extract title and snippet.
    - optional whitelist: WEB_WHITELIST = "wikipedia.org, mdn.mozilla.org"
    """

    def __init__(
        self,
        *,
        search_provider: Optional[ISearchProvider] = None,
        whitelist: Optional[List[str]] = None,
        timeout_s: int = 10,
        user_agent: Optional[str] = None,
    ) -> None:
        self._provider = search_provider
        self._whitelist = [d.strip().lower() for d in (whitelist or []) if d.strip()]
        self._timeout_s = int(timeout_s)
        self._ua = user_agent or config.WEB_USER_AGENT

    async def search(self, query: str, *, limit: int = 5) -> List[SearchHit]:
        if not self._provider:
            # In production, deliberate decision: if no search provider, fail-fast,
            # in test, inject FakeSearchProvider.
            raise RuntimeError("No search provider configured. Set WEB_SEARCH_PROVIDER or inject one.")
        hits = await self._provider.search(query, limit=limit)
        return hits[: max(1, int(limit))]

    async def fetch(self, url: str) -> Page:
        if not self._is_allowed(url):
            raise ValueError(f"url_not_whitelisted: {url}")

        headers = {"User-Agent": self._ua, "Accept": "text/html,application/xhtml+xml"}
        async with httpx.AsyncClient(timeout=self._timeout_s, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text or ""

        title = self._extract_title(html) or self._host_as_title(url)
        snippet = self._extract_meta_description(html) or self._first_p_tag(html) or ""
        return {"title": title, "url": url, "snippet": snippet}

    # ---- helpers ----
    def _is_allowed(self, url: str) -> bool:
        if not self._whitelist:
            return True
        host = (urlparse(url).hostname or "").lower()
        return any(host == d or host.endswith("." + d) for d in self._whitelist)

    @staticmethod
    def _extract_title(html: str) -> Optional[str]:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        return re.sub(r"\s+", " ", m.group(1)).strip()[:240]

    @staticmethod
    def _extract_meta_description(html: str) -> Optional[str]:
        m = re.search(
            r'<meta\s+(?:name=["\']description["\']|property=["\']og:description["\'])\s+content=["\'](.*?)["\']',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return None
        return re.sub(r"\s+", " ", m.group(1)).strip()[:300]

    @staticmethod
    def _first_p_tag(html: str) -> Optional[str]:
        m = re.search(r"<p[^>]*>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        txt = re.sub(r"<[^>]+>", " ", m.group(1))
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:300] if txt else None

    @staticmethod
    def _host_as_title(url: str) -> str:
        return urlparse(url).hostname or "web"
