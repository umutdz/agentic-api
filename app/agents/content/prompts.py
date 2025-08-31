from langchain_core.prompts import PromptTemplate

CONTENT_PROMPT = PromptTemplate.from_template(
    """You are a precise researcher. Use ONLY the provided sources to answer.
Cite at least two sources in the output list; do not invent URLs.

Return JSON strictly matching this schema:
{schema}

User Task:
{task}

Sources (title — url):
{sources_block}
"""
)
