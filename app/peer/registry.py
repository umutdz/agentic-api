from typing import Dict


class AgentRegistry:
    """
    A simple service registry for agent objects.
    Lazy import + singleton behavior: each agent is created once.
    """

    _cache: Dict[str, object] = {}

    @classmethod
    def get(cls, name: str):
        """
        Return a singleton instance of the requested agent.

        Why lazy import?
        - Prevent circular import issues (agents are imported only when first needed).
        - Reduce startup time (heavy modules are loaded on demand).

        Caching:
        - The first call creates the instance and stores it in `_cache`.
        - Subsequent calls return the same instance (shared resources).

        Thread-safety:
        - Good enough for typical FastAPI workloads; if you expect very high concurrency on the first call,
        wrap the creation branch with a lock.
        """
        if name in cls._cache:
            return cls._cache[name]

        if name == "content":
            from app.agents.content.agent import ContentAgent

            instance = ContentAgent()
        elif name == "code":
            from app.agents.code.agent import CodeAgent

            instance = CodeAgent()
        else:
            raise ValueError(f"unknown agent: {name}")

        cls._cache[name] = instance
        return instance
