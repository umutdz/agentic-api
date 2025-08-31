from functools import lru_cache

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.core.config import config


class LLMClient:
    """
    Merkezi LLM factory.
    - Currently only OpenAI is supported.
    - Each different (provider, model, api_key, base_url, temperature, timeout_s, max_retries)
        combination creates a separate cache entry.
    """

    @classmethod
    def get_llm(
        cls,
        *,
        model_name: str,
        temperature: float = 0.2,
        timeout_s: int = 30,
    ) -> Runnable:
        provider = config.LLM_PROVIDER.lower()

        if provider == "openai":
            return _get_openai_chat_llm_cached(
                provider="openai",
                model=model_name,
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL,
                temperature=temperature,
                timeout_s=timeout_s or config.LLM_TIMEOUT_S,
                max_retries=config.LLM_MAX_RETRIES,
            )

        raise ValueError(f"Unknown LLM provider: {provider}")


@lru_cache(maxsize=128)
def _get_openai_chat_llm_cached(
    *,
    provider: str,
    model: str,
    api_key: str,
    base_url: str,
    temperature: float,
    timeout_s: int,
    max_retries: int,
) -> ChatOpenAI:
    """
    Return a cached ChatOpenAI client.

    Cache key = (provider, model, api_key, base_url,
                rounded temperature, timeout_s, max_retries)
    """

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is empty; please set it.")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=round(temperature, 3),
        timeout=int(timeout_s),
        max_retries=int(max_retries),
    )
