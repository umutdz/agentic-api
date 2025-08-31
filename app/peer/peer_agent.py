from app.peer.rules import _score


class PeerAgent:
    @staticmethod
    def decide(task: str) -> dict:
        code, content, breakdown = _score(task)
        if code >= 2 and code > content:
            return {"agent": "code", "reason": f"rules: code_signals={breakdown}"}
        if content >= 1 and content >= code:
            return {"agent": "content", "reason": f"rules: content_signals={breakdown}"}
        return {"agent": "content", "reason": f"fallback_content: signals={breakdown}"}
