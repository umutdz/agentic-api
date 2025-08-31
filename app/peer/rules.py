import re
from typing import Dict, Tuple

# Language tokens / abbreviations
LANG_TOKENS = r"(python|javascript|typescript|js|ts|java|go|golang|rust|c\+\+|c#|ruby|php)"

# Simple signals
CODE_PATTERNS = [
    r"\bkod( yaz|la)?\b",
    r"\bcode\b",
    r"\bimplement(et|ation)?\b",
    r"\b(function|class|method|api|endpoint)\b",
    r"\btest(ler|)\b|\bunit test\b|\bpytest\b|\bassert\b",
    r"```",
    r"\bimport\s+\w+",
    # language tokens alone +1 (weak signal)
    rf"\b{LANG_TOKENS}\b",
]

CONTENT_PATTERNS = [
    r"\bblog\b",
    r"\bmakale\b",
    r"\byazı\b",
    r"\biçerik\b",
    r"\bnedir\b",
    r"\baçıkla\b",
    r"\bözet(le|)\b",
    r"\brehber\b",
    r"\bkarşılaştır\b",
    r"\bkaynak(ça)?\b",
    r"\breferans(lar)?\b",
    r"\blink ver\b",
    r"\bar(a|â)ştır(ma)?\b",
    r"\bincele\b",
]

# Strong signals
HARD_CODE = [
    r"\bkod yaz\b",
    r"\bunit test\b",
    r"\bpytest\b",
    r"\bfonksiyon yaz\b",
    r"```",
    r"\bfunction\b",
    r"\bclass\b",
]

HARD_CONTENT = [r"\bblog yaz\b", r"\bmakale yaz\b", r"\bkaynak(ça)? ver\b"]

# Language name and "example/code/snippet/function" together +2
CO_OCCUR = re.compile(
    rf"(\b{LANG_TOKENS}\b.*\b(örnek|orneği|ornegi|örneği|kod|kodu|snippet|demo|fonksiyon|function)\b)"
    rf"|(\b(örnek|orneği|ornegi|örneği|kod|kodu|snippet|demo|fonksiyon|function)\b.*\b{LANG_TOKENS}\b)",
    flags=re.IGNORECASE,
)


def _score(text: str) -> Tuple[int, int, Dict]:
    t = text.lower()

    def count(ps):
        return sum(1 for p in ps if re.search(p, t, flags=re.IGNORECASE))

    code = count(CODE_PATTERNS)
    content = count(CONTENT_PATTERNS)

    if any(re.search(p, t, flags=re.IGNORECASE) for p in HARD_CODE):
        code += 2
    if any(re.search(p, t, flags=re.IGNORECASE) for p in HARD_CONTENT):
        content += 2
    if CO_OCCUR.search(t):
        code += 2  # "js + example", "python + code" etc.

    return code, content, {"code": code, "content": content}
