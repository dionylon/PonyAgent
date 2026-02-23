# PonyAgent — Claude 开发规范

## 包管理

- 后端一律使用 `uv` 管理依赖，**禁止使用 pip**
- 添加依赖：`uv add <package>`
- 运行命令：`uv run <command>`
- 启动后端：`uv run uvicorn main:app --reload`
- 依赖声明在 `backend/pyproject.toml`，锁文件为 `backend/uv.lock`

## API 写法

- **查阅 LangChain/LangGraph/Deep Agents API 时，必须使用 `mcp__langchain-doc__SearchDocsByLangChain` 工具获取最新文档**，不得依赖训练数据中的旧版写法
- LangChain v1 中 `create_react_agent` 已废弃，使用 `create_agent`（来自 `langchain.agents`）
- LangGraph v1 中 `langgraph.prebuilt.create_react_agent` 已废弃，使用 `langchain.agents.create_agent`
- 多提供商 LLM 统一通过 `init_chat_model()` 初始化，不直接实例化各厂商 class

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SSE |
| 包管理 | uv |
| Agent 框架 | LangChain v1 + LangGraph v1 + Deep Agents |
| 前端 | Vue 3 + Vite |
| LLM | 多提供商，`init_chat_model()` 统一接口 |

## 项目结构约定

- `backend/agent/core.py` 是每个章节的**主要改动点**，路由层和前端原则上不动
- 每个 Phase 的代码在上一 Phase 基础上叠加，不重写
- 工具注册放 `backend/agent/tools.py`，记忆管理放 `backend/agent/memory.py`

## 章节进度

当前项目遵循 `ROADMAP.md` 中定义的三阶段 11 章计划：

- **Phase 1（Ch.1–6）**：LangGraph 底层，手动构建
- **Phase 2（Ch.7–9）**：LangChain `create_agent` 中层抽象
- **Phase 3（Ch.10–11）**：Deep Agents 全能 harness

详见 `docs/plans/2026-02-23-ponyagent-design.md`
