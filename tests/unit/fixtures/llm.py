import json

from langchain_core.runnables import RunnableLambda


def make_fake_llm(payload: dict):
    """LangChain Runnable gibi davranan basit LLM stub.
    prompt output -> JSON string
    """

    def _fn(_input):
        # prompt | llm | parser chain llm should return a string
        return json.dumps(payload)

    return RunnableLambda(_fn)
