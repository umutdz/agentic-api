from typing import Dict, List, Protocol

SearchHit = Dict[str, str]


# Search provider interface
class ISearchProvider(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> List[SearchHit]: ...
