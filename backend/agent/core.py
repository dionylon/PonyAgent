# Ch.2: 流式输出 - 用 astream() 逐 token 推送（Ch.1 用 ainvoke 单次返回）
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from providers.llm import get_llm

_llm = get_llm()


async def stream_agent(message: str) -> AsyncGenerator[str, None]:
    async for chunk in _llm.astream([HumanMessage(content=message)]):
        if chunk.content:
            yield chunk.content
