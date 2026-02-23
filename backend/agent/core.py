# Ch.5: 短期记忆持久化 - SqliteSaver（见 agent/memory.py）
import asyncio
from typing import AsyncGenerator

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from providers.llm import get_llm

from agent.memory import get_checkpointer
from agent.tools import get_cached_tools

_llm = get_llm()
_graph = None
_lock = asyncio.Lock()


async def _get_graph():
    global _graph
    if _graph is None:
        async with _lock:
            if _graph is None:
                checkpointer = await get_checkpointer()
                tools = get_cached_tools()
                llm_with_tools = _llm.bind_tools(tools)

                def chat_node(state: MessagesState):
                    return {"messages": [llm_with_tools.invoke(state["messages"])]}

                _graph = (
                    StateGraph(MessagesState)
                    .add_node("chat", chat_node)
                    .add_node("tools", ToolNode(tools))
                    .add_edge(START, "chat")
                    .add_conditional_edges("chat", tools_condition)
                    .add_edge("tools", "chat")
                    .compile(checkpointer=checkpointer)
                )
    return _graph


async def stream_agent(message: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    graph = await _get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=message)]}
    async for chunk, _metadata in graph.astream(input_state, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content
