from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from app.services.llm import LLMClient

ProgressCB = Callable[[float], Any]


class BaseAgent(ABC):
    """Base class for agents.
    - Holds an LLM client created via LLMClient.get_llm()
    - Provides a safe progress() helper to avoid repeating None checks.
    """

    def __init__(self, *, model_name: Optional[str] = None, temperature: float = 0.2, timeout_s: int = 30):
        self.llm = LLMClient.get_llm(model_name=model_name, temperature=temperature, timeout_s=timeout_s)

    @staticmethod
    def _progress(cb: Optional[ProgressCB], value: float) -> None:
        if cb is not None:
            try:
                cb(float(value))
            except Exception:
                # progress is best-effort; never break the agent
                pass

    @abstractmethod
    async def run(self, task: str, *, job_id: str, request_id: str, progress_cb: Optional[ProgressCB] = None):
        """Execute the agent-specific workflow and return a Pydantic model output."""
        ...
