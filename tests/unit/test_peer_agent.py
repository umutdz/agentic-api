from app.peer.peer_agent import PeerAgent


def test_peer_agent_routing_rules_happy():
    cases = [
        ("Blog yaz: Quicksort nedir? 2 kaynaktan referans ver.", "content"),
        ("Python kodu yaz: quicksort ve 3 test", "code"),
        ("Makale yaz: LLM nedir? Kaynakça ekle.", "content"),
        ("JS ile quicksort örneği", "code"),
    ]
    for task, expected in cases:
        d = PeerAgent.decide(task)
        assert d.get("agent") == expected, f"{task} -> {d}"
        # reason field should be filled:
        assert isinstance(d.get("reason"), str) and d["reason"]


def test_peer_agent_routing_rules_sad():
    cases = [
        ("Quicksort nedir? Kısa özet ve kaynak ver.", "content"),
        ("JS ile quicksort örneği ve açıklaması", "code"),
    ]
    for task, expected in cases:
        d = PeerAgent.decide(task)
        assert d.get("agent") == expected, f"{task} -> {d}"
        assert isinstance(d.get("reason"), str) and d["reason"]
