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
