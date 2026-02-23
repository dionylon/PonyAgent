# PonyAgent Roadmap

从零到生产级，系统学习现代 agent 工作流程与机制。

**技术栈：** Python · FastAPI · SSE · Vue 3 · LangChain v1 · LangGraph v1 · Deep Agents

---

## Phase 1 — LangGraph 底层，手动构建

手动实现 agent 的每一个环节，深入理解底层机制。

| 章节 | 主题 | 核心概念 | 关键 API |
|------|------|----------|----------|
| Ch.1 | **基础 LLM 对话** | ChatModel、Messages、多提供商接入 | `init_chat_model()` |
| Ch.2 | **流式返回** | SSE 协议、异步流、前端 EventSource | `astream()` |
| Ch.3 | **LangGraph Graph API** | State、Node、Edge、图编译与执行 | `StateGraph`, `MessagesState` |
| Ch.4 | **工具调用** | 工具定义、bind_tools、手写 ReAct 循环 | `@tool`, `bind_tools` |
| Ch.5 | **短期记忆** | Checkpointer、thread_id、session 隔离 | `InMemorySaver`, `SqliteSaver` |
| Ch.6 | **上下文压缩** | 消息裁剪、摘要压缩、token 管理 | `trim_messages` |

---

## Phase 2 — LangChain `create_agent`，中层抽象

切换到 LangChain 高层 API，与 Phase 1 手写版对比，理解抽象价值。

| 章节 | 主题 | 核心概念 | 关键 API |
|------|------|----------|----------|
| Ch.7 | **`create_agent` + Middleware** | 生产级 agent 工厂、middleware 系统 | `create_agent` |
| Ch.8 | **Human-in-the-loop** | 执行中断、人工审批、状态恢复 | `interrupt()`, `Command`, `HumanInTheLoopMiddleware` |
| Ch.9 | **长期记忆** | 跨 thread Store、namespace/key、语义搜索 | `InMemoryStore`, `store.put/get/search` |

---

## Phase 3 — Deep Agents，全能 harness

使用 Deep Agents SDK，体验 batteries-included 的完整 agent 能力。

| 章节 | 主题 | 核心概念 | 关键 API |
|------|------|----------|----------|
| Ch.10 | **`create_deep_agent`** | 任务规划、虚拟文件系统、子 agent 委派 | `create_deep_agent`, `CompositeBackend` |
| Ch.11 | **Skills** | 可复用领域知识、AGENTS.md、跨 session 学习 | Agent Skills 规范 |

---

## 架构层次

```
Deep Agents (create_deep_agent)   ← Phase 3：batteries-included harness
       ↑
LangChain (create_agent)          ← Phase 2：生产级 agent 构建块
       ↑
LangGraph (StateGraph)            ← Phase 1：底层图编排运行时
```

## 项目结构

```
ponyagent/
├── backend/              # FastAPI + uv
│   ├── pyproject.toml
│   ├── main.py
│   ├── routers/chat.py   # SSE 端点
│   ├── agent/core.py     # 每章主要改动点
│   └── providers/llm.py  # 多提供商工厂
├── frontend/             # Vue 3 + Vite
│   └── src/
│       ├── components/ChatWindow.vue
│       └── api/chat.ts
└── docs/plans/           # 设计文档
```

> 详细设计见 [docs/plans/2026-02-23-ponyagent-design.md](docs/plans/2026-02-23-ponyagent-design.md)
