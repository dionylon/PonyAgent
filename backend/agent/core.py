# Ch.1: 直接调用 LLM，无图结构（Ch.3 引入 StateGraph）
from langchain_core.messages import HumanMessage
from providers.llm import get_llm

_llm = get_llm()


async def invoke_agent(message: str) -> str:
    response = await _llm.ainvoke([HumanMessage(content=message)])
    return response.content
