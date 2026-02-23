# MCP Startup Loading Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 MCP 工具加载从首次请求懒加载改为服务启动时预加载，消除首次请求延迟。

**Architecture:** 在 `tools.py` 增加模块级缓存（`_cached_tools`）和两个新函数（`init_tools()` / `get_cached_tools()`），用 FastAPI lifespan 在 startup 时调用 `init_tools()`，`core.py` 改为同步调用 `get_cached_tools()`。路由层和前端不动。

**Tech Stack:** Python 3.12, FastAPI lifespan (`asynccontextmanager`), pytest-asyncio, httpx (test only)

---

### Task 1: 添加 dev 依赖

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: 添加 pytest-asyncio 和 httpx**

```bash
cd backend && uv add --dev pytest-asyncio httpx
```

Expected：`pyproject.toml` 的 `[dependency-groups] dev` 新增两个依赖，`uv.lock` 更新。

**Step 2: 配置 pytest asyncio 模式**

在 `backend/pyproject.toml` 末尾追加：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Step 3: 验证现有测试仍通过**

```bash
cd backend && uv run pytest tests/ -v
```

Expected：全部绿色通过。

**Step 4: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(backend/ch4): add pytest-asyncio and httpx for async tests"
```

---

### Task 2: 为 tools.py 新 API 写失败测试

**Files:**
- Modify: `backend/tests/test_tools.py`

**Step 1: 在 `test_tools.py` 末尾追加以下测试**

```python
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
```

**Step 2: 运行测试，确认它们失败**

```bash
cd backend && uv run pytest tests/test_tools.py::test_get_cached_tools_raises_before_init tests/test_tools.py::test_init_tools_mcp_failure_fallback tests/test_tools.py::test_init_tools_success -v
```

Expected：三个测试全部 FAIL，报 `AttributeError: module 'agent.tools' has no attribute '_cached_tools'` 或类似错误。

---

### Task 3: 实现 tools.py 新 API

**Files:**
- Modify: `backend/agent/tools.py`

**Step 1: 将 `tools.py` 替换为以下内容**

```python
import asyncio
import logging
import math

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

_cached_tools: list | None = None


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，支持四则运算和 math 函数，如 '2 + 2'、'sqrt(16)'。"""
    if "__" in expression:
        raise ValueError("表达式不允许包含 dunder 属性访问")
    safe_globals = {"__builtins__": {}, **vars(math)}
    return str(eval(expression, safe_globals))


async def init_tools() -> None:
    """服务启动时调用：加载 MCP 工具并缓存。MCP 不可用时回退到仅 calculator。"""
    global _cached_tools
    client = MultiServerMCPClient(
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            }
        }
    )
    try:
        mcp_tools = await asyncio.wait_for(client.get_tools(), timeout=10)
        logger.info("MCP filesystem 工具加载成功：%d 个工具", len(mcp_tools))
        _cached_tools = [calculator] + mcp_tools
    except Exception as e:
        logger.warning("MCP 工具加载失败（%s），回退到仅 calculator", e)
        _cached_tools = [calculator]


def get_cached_tools() -> list:
    """返回已缓存的工具列表。必须先调用 init_tools()。"""
    if _cached_tools is None:
        raise RuntimeError("init_tools() 尚未调用，请在服务启动时（lifespan）调用")
    return _cached_tools
```

**Step 2: 运行 Task 2 的三个测试，确认全部通过**

```bash
cd backend && uv run pytest tests/test_tools.py::test_get_cached_tools_raises_before_init tests/test_tools.py::test_init_tools_mcp_failure_fallback tests/test_tools.py::test_init_tools_success -v
```

Expected：三个测试 PASS。

**Step 3: 运行全部测试，确认无回归**

```bash
cd backend && uv run pytest tests/ -v
```

Expected：全部通过（`test_graph_has_correct_nodes` 已直接构建图，不依赖 `get_all_tools`，不受影响）。

**Step 4: Commit**

```bash
git add backend/agent/tools.py backend/tests/test_tools.py
git commit -m "feat(backend/ch4): add init_tools/get_cached_tools, remove get_all_tools"
```

---

### Task 4: 为 main.py lifespan 写失败测试

**Files:**
- Create: `backend/tests/test_main.py`

**Step 1: 创建 `backend/tests/test_main.py`**

```python
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

import agent.tools as tools_module
from agent.tools import calculator


async def test_lifespan_calls_init_tools():
    """服务启动时 lifespan 应调用 init_tools() 并完成工具缓存。"""
    original = tools_module._cached_tools
    tools_module._cached_tools = None

    async def fake_init():
        tools_module._cached_tools = [calculator]

    try:
        with patch.object(tools_module, "init_tools", side_effect=fake_init) as mock_init:
            from main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as _:
                pass

        mock_init.assert_called_once()
        assert tools_module.get_cached_tools() == [calculator]
    finally:
        tools_module._cached_tools = original
```

**Step 2: 运行测试，确认失败**

```bash
cd backend && uv run pytest tests/test_main.py::test_lifespan_calls_init_tools -v
```

Expected：FAIL，报 `AssertionError: Expected 'init_tools' to have been called once` 或 lifespan 未调用 `init_tools`。

---

### Task 5: 更新 main.py 使用 lifespan

**Files:**
- Modify: `backend/main.py`

**Step 1: 将 `main.py` 替换为以下内容**

```python
import logging
from contextlib import asynccontextmanager

import logging_config
logging_config.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.tools import init_tools
from routers.chat import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tools()
    yield


app = FastAPI(title="PonyAgent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

logger.info("PonyAgent backend started")
```

**Step 2: 运行 Task 4 的测试，确认通过**

```bash
cd backend && uv run pytest tests/test_main.py::test_lifespan_calls_init_tools -v
```

Expected：PASS。

**Step 3: Commit**

```bash
git add backend/main.py backend/tests/test_main.py
git commit -m "feat(backend/ch4): move MCP init to FastAPI lifespan startup"
```

---

### Task 6: 更新 core.py 使用 get_cached_tools

**Files:**
- Modify: `backend/agent/core.py`

**Step 1: 将 `core.py` 替换为以下内容**

```python
# Ch.4: Tools + Tool Calling - ReAct 图（MCP 工具在服务启动时预加载）
import asyncio
from typing import AsyncGenerator

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from providers.llm import get_llm

from agent.tools import get_cached_tools

_llm = get_llm()
_checkpointer = InMemorySaver()
_graph = None
_lock = asyncio.Lock()


async def _get_graph():
    global _graph
    if _graph is None:
        async with _lock:
            if _graph is None:
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
                    .compile(checkpointer=_checkpointer)
                )
    return _graph


async def stream_agent(message: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    graph = await _get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=message)]}
    async for chunk, _metadata in graph.astream(input_state, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content
```

**Step 2: 运行全部测试**

```bash
cd backend && uv run pytest tests/ -v
```

Expected：全部通过。

**Step 3: Commit**

```bash
git add backend/agent/core.py
git commit -m "refactor(backend/ch4): use get_cached_tools() instead of await get_all_tools()"
```

---

### Task 7: 冒烟测试（手动验证）

**Step 1: 启动服务，观察 startup 日志**

```bash
cd backend && uv run uvicorn main:app --reload
```

Expected 日志（启动时，首次请求之前）：
```
INFO ... MCP filesystem 工具加载成功：N 个工具
```
或（MCP 不可用时）：
```
WARNING ... MCP 工具加载失败（...），回退到仅 calculator
```

**Step 2: 发送首次请求，确认无明显延迟**

```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "2加2等于几", "thread_id": "test"}'
```

Expected：立即开始流式返回，不再有首次请求的 10s 等待。
