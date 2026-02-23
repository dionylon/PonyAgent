# Ch.6: 上下文压缩 - trim_messages（在 Ch.5 基础上叠加）
import asyncio
from typing import AsyncGenerator

from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from providers.llm import get_llm

from agent.memory import get_checkpointer
from agent.tools import get_cached_tools

# 保留最近 8000 token，防止超出模型上下文窗口
_MAX_TOKENS = 8000

_llm = get_llm()
_graph = None
_lock = asyncio.Lock()


def _make_chat_node(llm_with_tools):
    def chat_node(state: MessagesState):
        trimmed = trim_messages(
            state["messages"],
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=_MAX_TOKENS,
            start_on="human",
            end_on=("human", "tool"),
            allow_partial=False,
        )
        return {"messages": [llm_with_tools.invoke(trimmed)]}

    return chat_node


def _build_graph(llm_with_tools, tools, checkpointer):
    chat_node = _make_chat_node(llm_with_tools)
    return (
        StateGraph(MessagesState)
        .add_node("chat", chat_node)
        .add_node("tools", ToolNode(tools))
        .add_edge(START, "chat")
        .add_conditional_edges("chat", tools_condition)
        .add_edge("tools", "chat")
        .compile(checkpointer=checkpointer)
    )


async def _get_graph():
    global _graph
    if _graph is None:
        async with _lock:
            if _graph is None:
                checkpointer = await get_checkpointer()
                tools = get_cached_tools()
                llm_with_tools = _llm.bind_tools(tools)
                _graph = _build_graph(llm_with_tools, tools, checkpointer)
    return _graph


async def stream_agent(message: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    graph = await _get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=message)]}
    async for chunk, _metadata in graph.astream(input_state, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content
