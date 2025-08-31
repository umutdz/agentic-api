from typing import Optional

from app.core.config import config
from app.services.interfaces import ISearchProvider
from app.services.serpapi import SerpAPIProvider


def make_search_provider() -> Optional[ISearchProvider]:
    name = (config.WEB_SEARCH_PROVIDER or "").lower()
    if name == "serpapi" and getattr(config, "SERPAPI_API_KEY", ""):
        engine = getattr(config, "SERPAPI_ENGINE", "duckduckgo")
        return SerpAPIProvider(
            api_key=config.SERPAPI_API_KEY,
            engine=engine,
            timeout_s=config.WEB_TIMEOUT_S,
            user_agent=config.WEB_USER_AGENT,
        )
    # later: if name == "bing": ...
    # later: if name == "ddg":  ...
    return None
