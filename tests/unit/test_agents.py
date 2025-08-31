# tests/unit/test_agents.py
import pytest

from app.agents.code.agent import CodeAgent
from tests.unit.fixtures.llm import make_fake_llm


@pytest.mark.asyncio
async def test_code_agent_happy():
    agent = CodeAgent()

    fake_payload = {
        "language": "Python",
        "code": "def f():\n    return 42",
        "explanation": "simple",
    }
    agent.llm = make_fake_llm(fake_payload)

    out = await agent.run("Basit bir Python fonksiyonu yaz", job_id="j1", request_id="r1")

    assert out.language == "Python"
    assert "return 42" in out.code
    assert out.explanation == "simple"
