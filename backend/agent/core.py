# Ch.3: LangGraph Graph API - 用 StateGraph 重构对话流程（Ch.2 直接调用 LLM.astream）
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from providers.llm import get_llm

_llm = get_llm()
_checkpointer = InMemorySaver()


def chat_node(state: MessagesState):
    response = _llm.invoke(state["messages"])
    return {"messages": [response]}


_graph = (
    StateGraph(MessagesState)
    .add_node("chat", chat_node)
    .add_edge(START, "chat")
    .add_edge("chat", END)
    .compile(checkpointer=_checkpointer)
)


async def stream_agent(message: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=message)]}
    async for chunk, _metadata in _graph.astream(input_state, config=config, stream_mode="messages"):
        if chunk.content:
            yield chunk.content
