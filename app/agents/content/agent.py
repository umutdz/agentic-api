from typing import List

from langchain_core.output_parsers import PydanticOutputParser

from app.agents.base import BaseAgent
from app.agents.content.prompts import CONTENT_PROMPT
from app.core.config import config
from app.schemas.agent_content import ContentOutput, Source
from app.services.search_factory import make_search_provider
from app.services.web import WebClient


class ContentAgent(BaseAgent):
    """Produce a sourced answer (≥2 sources), using only provided links."""

    def __init__(self, web: WebClient = None):
        super().__init__(model_name=config.LLM_MODEL_CONTENT, temperature=0.35, timeout_s=60)
        provider = make_search_provider()
        whitelist = [d.strip() for d in (config.WEB_WHITELIST or "").split(",") if d.strip()]
        self.web = WebClient(
            search_provider=provider,
            whitelist=whitelist,
            timeout_s=config.WEB_TIMEOUT_S,
            user_agent=config.WEB_USER_AGENT,
        )

    async def _gather_sources(self, query: str, min_sources: int = 2, limit: int = 5) -> List[Source]:
        hits = await self.web.search(query, limit=limit)  # [{title, url}]
        sources: List[Source] = []
        for h in hits:
            # Optionally fetch page to validate title/url (and stay within whitelist)
            page = await self.web.fetch(h["url"])  # {title, url, snippet?}
            sources.append(Source(title=page["title"], url=page["url"]))
            if len(sources) >= min_sources:
                break
        return sources

    async def run(self, task: str, *, job_id: str, request_id: str, progress_cb=None) -> ContentOutput:
        # 1) gather sources (≥2)
        self._progress(progress_cb, 0.20)
        srcs = await self._gather_sources(task, min_sources=2, limit=5)
        if len(srcs) < 2:
            raise ValueError("insufficient_sources")

        sources_block = "\n".join(f"- {s.title} — {s.url}" for s in srcs)

        # 2) LC chain: prompt | llm | parser
        parser = PydanticOutputParser(pydantic_object=ContentOutput)
        prompt = CONTENT_PROMPT.partial(schema=parser.get_format_instructions())
        chain = prompt | self.llm | parser

        self._progress(progress_cb, 0.80)
        output: ContentOutput = await chain.ainvoke({"task": task, "sources_block": sources_block})

        # 3) Optional guardrail: ensure output.sources ⊆ gathered sources
        allowed = {str(s.url): s for s in srcs}
        filtered = [s for s in output.sources if str(s.url) in allowed]
        if len(filtered) < 2:
            # enforce the contract strictly
            raise ValueError("model_output_sources_not_in_whitelist")
        output.sources = filtered

        self._progress(progress_cb, 0.90)
        return output
