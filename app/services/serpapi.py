from typing import Dict, List, Optional

import httpx

from app.services.interfaces import ISearchProvider

SearchHit = Dict[str, str]


class SerpAPIProvider(ISearchProvider):
    """
    SerpAPI adapter.
    Supported engines: google, bing, duckduckgo, ... (SerpAPI documentation)
    Free plan ~ 250 search/month (See SerpAPI website).
    """

    def __init__(self, *, api_key: str, engine: str = "duckduckgo", timeout_s: int = 10, user_agent: Optional[str] = None):
        if not api_key:
            raise ValueError("SERPAPI_API_KEY is required")
        self.api_key = api_key
        self.engine = engine
        self.timeout_s = int(timeout_s)
        self.user_agent = user_agent or "AgenticAPI/ContentAgent"

    async def search(self, query: str, *, limit: int = 5) -> List[SearchHit]:
        params = {
            "engine": self.engine,  # "google" | "bing" | "duckduckgo" ...
            "q": query,
            "api_key": self.api_key,
            "num": max(1, min(10, int(limit))),
        }
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout_s, headers=headers) as client:
            r = await client.get("https://serpapi.com/search.json", params=params)
            r.raise_for_status()
            data = r.json()

        organic = data.get("organic_results") or []
        hits: List[Dict[str, str]] = []
        for it in organic:
            title = it.get("title") or it.get("name") or ""
            url = it.get("link") or it.get("url") or ""
            if title and url:
                hits.append({"title": title[:240], "url": url})
            if len(hits) >= limit:
                break
        return hits
