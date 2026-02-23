# MCP 工具启动时加载设计

**日期**：2026-02-23
**章节**：Ch.4

## 背景

现有实现在 `core.py` 的 `_get_graph()` 中懒加载 MCP 工具（第一次请求时调用 `get_all_tools()`，含最多 10s 的 MCP 初始化等待），导致首次请求延迟明显。

## 目标

将 MCP 工具加载提前到服务 startup 阶段，消除首次请求延迟。图的构建仍保持懒加载。

## 方案

**方案 A（采用）：FastAPI lifespan + 模块级缓存**

### 改动范围

只改动三个文件，路由层和前端不动：

| 文件 | 改动 |
|------|------|
| `backend/agent/tools.py` | 新增 `_cached_tools`、`init_tools()`、`get_cached_tools()` |
| `backend/main.py` | 改用 `asynccontextmanager` lifespan，startup 调用 `init_tools()` |
| `backend/agent/core.py` | `_get_graph()` 改调 `get_cached_tools()`（同步，无 await） |

### 数据流

```
uvicorn 启动
  → lifespan startup
      → tools.init_tools()
          → 尝试 MultiServerMCPClient.get_tools()（10s timeout）
          → 成功：_cached_tools = [calculator] + mcp_tools
          → 失败：_cached_tools = [calculator]（warning log）
  → 服务就绪，接受请求

首次请求到达
  → stream_agent()
      → _get_graph()（lazy，仅首次）
          → get_cached_tools()  ← 直接返回缓存，无 IO
          → 构建并缓存 _graph
  → 后续请求直接用缓存的 _graph
```

### 错误处理

- `init_tools()` 内部 try/except，失败时 `logger.warning` 并写 `[calculator]`，不向外抛出，服务正常启动
- `get_cached_tools()` 若在 `init_tools()` 未调用时被调用，抛出 `RuntimeError`（防御性保护）

### 接口定义

```python
# tools.py 新增
async def init_tools() -> None: ...      # 供 lifespan 调用
def get_cached_tools() -> list: ...      # 供 core.py 调用（同步）
```

## 不采用的方案

- **方案 B（AppState 注入）**：需修改路由层，违反 CLAUDE.md 约定
- **方案 C（asyncio.Event 惰性等待）**：复杂度高，ch4 阶段无此必要
