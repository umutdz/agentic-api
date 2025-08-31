import re

from langchain_core.output_parsers import PydanticOutputParser

from app.agents.base import BaseAgent
from app.agents.code.prompts import CODE_PROMPT
from app.core.config import config
from app.schemas.agent_code import CodeOutput


class CodeAgent(BaseAgent):
    """Generate structured code output (language, code, explanation)."""

    _CTRL_CHARS_RE = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")

    def __init__(self):
        # Code models benefit from low temperature
        super().__init__(model_name=config.LLM_MODEL_CODE, temperature=0.2, timeout_s=45)

    def _sanitize_text(self, s: str) -> str:
        # remove ASCII control chars to keep JSON/Mongo/jq happy
        return self._CTRL_CHARS_RE.sub("", s or "")

    def _strip_md_code_fence(self, s: str) -> str:
        if not s:
            return s
        m = re.match(r"^```[a-zA-Z0-9_-]*\n(.*)\n```$", s.strip(), flags=re.DOTALL)
        return m.group(1) if m else s

    async def run(self, task: str, *, job_id: str, request_id: str, progress_cb=None) -> CodeOutput:
        self._progress(progress_cb, 0.30)

        parser = PydanticOutputParser(pydantic_object=CodeOutput)
        prompt = CODE_PROMPT.partial(schema=parser.get_format_instructions())
        chain = prompt | self.llm | parser

        self._progress(progress_cb, 0.70)
        output: CodeOutput = await chain.ainvoke({"task": self._sanitize_text(self._strip_md_code_fence(task))})

        # ---- post-process / guardrails ----
        output.code = self._strip_md_code_fence(self._sanitize_text(output.code))
        output.explanation = self._sanitize_text(output.explanation)
        output.language = self._sanitize_text(output.language)

        if not output.code or len(output.code.strip()) < 5:
            raise ValueError("empty_or_invalid_code")

        self._progress(progress_cb, 0.90)
        return output
