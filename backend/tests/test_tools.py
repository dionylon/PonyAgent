import pytest
from agent.tools import calculator


def test_calculator_basic_arithmetic():
    assert calculator.invoke({"expression": "2 + 2"}) == "4"


def test_calculator_power():
    assert calculator.invoke({"expression": "2 ** 10"}) == "1024"


def test_calculator_sqrt():
    assert calculator.invoke({"expression": "sqrt(16)"}) == "4.0"


def test_calculator_blocks_import():
    with pytest.raises(Exception):
        calculator.invoke({"expression": "__import__('os').getcwd()"})

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


def test_graph_has_correct_nodes():
    """验证 ReAct 图结构：chat 和 tools 节点都存在。"""
    import agent.core as core
    from agent.tools import calculator

    tools = [calculator]
    llm_with_tools = core._llm.bind_tools(tools)

    def chat_node(state: MessagesState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph = (
        StateGraph(MessagesState)
        .add_node("chat", chat_node)
        .add_node("tools", ToolNode(tools))
        .add_edge(START, "chat")
        .add_conditional_edges("chat", tools_condition)
        .add_edge("tools", "chat")
        .compile(checkpointer=InMemorySaver())
    )
    assert "chat" in graph.nodes
    assert "tools" in graph.nodes


def test_calculator_blocks_mro_escape():
    with pytest.raises(Exception):
        calculator.invoke({"expression": "(1).__class__.__mro__[-1].__subclasses__()"})


import pytest
from unittest.mock import AsyncMock, patch
from langchain_mcp_adapters.client import MultiServerMCPClient
import agent.tools as tools_module


@pytest.fixture()
def reset_tool_cache():
    """每个测试前后重置 _cached_tools，避免测试间互相污染。"""
    original = tools_module._cached_tools
    tools_module._cached_tools = None
    yield
    tools_module._cached_tools = original


def test_get_cached_tools_raises_before_init(reset_tool_cache):
    """未调用 init_tools() 时，get_cached_tools() 应抛出 RuntimeError。"""
    with pytest.raises(RuntimeError, match="init_tools"):
        tools_module.get_cached_tools()


async def test_init_tools_mcp_failure_fallback(reset_tool_cache):
    """MCP 加载失败时，应回退到仅含 calculator 的工具列表。"""
    with patch.object(
        MultiServerMCPClient, "get_tools",
        new_callable=AsyncMock,
        side_effect=Exception("mcp down"),
    ):
        await tools_module.init_tools()
    result = tools_module.get_cached_tools()
    assert len(result) == 1
    assert result[0].name == "calculator"


async def test_init_tools_success(reset_tool_cache):
    """MCP 加载成功时，工具列表应包含 calculator + MCP 工具。"""
    from langchain_core.tools import tool as langchain_tool

    @langchain_tool
    def fake_mcp_tool(x: str) -> str:
        """fake mcp tool"""
        return x

    with patch.object(
        MultiServerMCPClient, "get_tools",
        new_callable=AsyncMock,
        return_value=[fake_mcp_tool],
    ):
        await tools_module.init_tools()
    result = tools_module.get_cached_tools()
    assert len(result) == 2
    assert result[0].name == "calculator"
    assert result[1].name == "fake_mcp_tool"
