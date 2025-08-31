import pytest

from app.agents.content.agent import ContentAgent
from app.schemas.agent_content import Source
from tests.unit.fixtures.llm import make_fake_llm


@pytest.mark.asyncio
async def test_content_agent_happy(monkeypatch):
    # 1) Web aramasını/gather'ı izole et
    sources = [
        Source(title="Python Sorting Howto", url="https://docs.python.org/3/howto/sorting.html"),
        Source(title="Quicksort Wikipedia", url="https://en.wikipedia.org/wiki/Quicksort"),
    ]

    async def _fake_gather(self, query: str, min_sources: int = 2, limit: int = 5):
        return sources

    monkeypatch.setattr(ContentAgent, "_gather_sources", _fake_gather)

    # 2) LLM'i, parser'ın beklediği JSON şemasını döndürecek şekilde stub'la
    payload = {
        "answer": "Kısa açıklama",
        "sources": [{"title": s.title, "url": str(s.url)} for s in sources],
    }
    agent = ContentAgent()
    agent.llm = make_fake_llm(payload)

    # 3) Çalıştır ve doğrula
    out = await agent.run("Quicksort nedir? 2 kaynakla anlat", job_id="jC1", request_id="rC1")
    assert out.answer.startswith("Kısa")
    assert [str(s.url) for s in out.sources] == [str(s.url) for s in sources]


@pytest.mark.asyncio
async def test_content_agent_insufficient_sources(monkeypatch):
    # _gather_sources sadece 1 kaynak döndürsün → ContentAgent en az 2 beklediği için hata vermeli
    async def _fake_gather_one(self, query: str, min_sources: int = 2, limit: int = 5):
        return [Source(title="OnlyOne", url="https://example.com/one")]

    monkeypatch.setattr(ContentAgent, "_gather_sources", _fake_gather_one)

    agent = ContentAgent()
    # LLM hiç kullanılmasa bile zincir kurulurken tip sorun olmasın diye basit stub
    agent.llm = make_fake_llm({"answer": "x", "sources": []})

    with pytest.raises(ValueError) as ei:
        await agent.run("Kaynaklı yazı", job_id="jC2", request_id="rC2")

    # Hata mesajı makul bir şey söylüyor mu?
    assert "insufficient" in str(ei.value).lower() or "yetersiz" in str(ei.value).lower()
