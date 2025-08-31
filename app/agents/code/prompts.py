from langchain_core.prompts import PromptTemplate

CODE_PROMPT = PromptTemplate.from_template(
    """You generate minimal, side-effect-free code snippets.

Return JSON strictly matching this schema:
{schema}

Constraints:
- Single programming language (fill `language`).
- Keep `explanation` short and optional.
- Do not include comments that simulate execution results.

Task:
{task}
"""
)
