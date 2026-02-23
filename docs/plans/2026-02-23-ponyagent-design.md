# PonyAgent — 设计文档

**日期：** 2026-02-23
**目标：** 从零到生产级，系统学习现代 agent 工作流程与机制

---

## 概述

PonyAgent 是一个渐进式学习项目，通过分章节逐步实现一个通用对话 agent，涵盖从底层 LLM 调用到全能 Deep Agents 框架的完整技术栈。项目采用 C/S 架构，后端 FastAPI + SSE，前端 Vue 3。

---

## 技术选型

| 层次 | 技术 |
|------|------|
| 后端语言 | Python，uv 管理依赖 |
| 后端框架 | FastAPI + SSE（流式推送） |
| Agent 框架 | LangChain v1 + LangGraph v1 + Deep Agents |
| 前端框架 | Vue 3 + Vite |
| LLM 提供商 | 多提供商（OpenAI、Anthropic 等，`init_chat_model()` 统一接口） |

---

## 项目结构

```
ponyagent/
├── backend/
│   ├── pyproject.toml        # uv 项目配置
│   ├── uv.lock
│   ├── main.py               # FastAPI 入口
│   ├── routers/
│   │   └── chat.py           # /chat SSE 端点
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py           # Agent 核心（每章主要改动点）
│   │   ├── memory.py         # 记忆管理
│   │   └── tools.py          # 工具注册
│   └── providers/
│       └── llm.py            # 多提供商 LLM 工厂
│
├── frontend/                 # Vue 3 (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatWindow.vue
│   │   ├── api/
│   │   │   └── chat.ts       # SSE 客户端封装
│   │   └── App.vue
│   └── package.json
│
├── ROADMAP.md
└── docs/
    └── plans/
        └── 2026-02-23-ponyagent-design.md
```

**演进原则：** 每章改动集中在 `agent/` 目录，前端和路由层基本不动。

---

## 章节规划

### Phase 1 — LangGraph 底层，手动构建（Ch.1–6）

**Ch.1 — ChatModels + Messages**
- 目标：接通 LLM，跑通基础多轮对话
- 核心概念：ChatModel、HumanMessage、AIMessage、多提供商统一接口
- 关键 API：`init_chat_model()`, `HumanMessage`, `AIMessage`
- 验收：前端发送消息，后端同步返回 AI 回复

**Ch.2 — Streaming**
- 目标：实现 token 级流式输出
- 核心概念：异步流、SSE 协议、前端 EventSource
- 关键 API：`astream()`, `EventSourceResponse`
- 验收：前端逐字渲染 AI 回复

**Ch.3 — LangGraph Graph API**
- 目标：手动用图结构重构对话流程
- 核心概念：State、Node、Edge、图编译与执行
- 关键 API：`StateGraph`, `MessagesState`, `add_node`, `add_edge`, `InMemorySaver`
- 验收：对话逻辑完全跑在 StateGraph 上，行为与 Ch.2 一致

**Ch.4 — Tools + Tool Calling**
- 目标：为 agent 添加工具调用能力，手写 ReAct 循环
- 核心概念：工具定义、bind_tools、工具执行节点、条件边
- 关键 API：`@tool`, `bind_tools`, 条件边 `add_conditional_edges`
- 验收：agent 能调用计算器/搜索等通用工具并返回结果

**Ch.5 — 短期记忆 Persistence**
- 目标：实现多 session 对话历史持久化
- 核心概念：Checkpointer、thread_id、session 隔离
- 关键 API：`InMemorySaver` → `SqliteSaver`, `thread_id` config
- 验收：刷新页面后历史对话可恢复；不同用户 session 互不干扰

**Ch.6 — Context Engineering**
- 目标：管理 token 上限，防止上下文溢出
- 核心概念：消息裁剪、摘要压缩、token 计数
- 关键 API：`trim_messages`, `SummarizationMiddleware`
- 验收：超长对话自动压缩，不丢失关键信息

---

### Phase 2 — LangChain `create_agent`，中层抽象（Ch.7–9）

**Ch.7 — `create_agent` + Middleware**
- 目标：用 LangChain 高层 API 替换 Phase 1 手写 agent，对比差异
- 核心概念：create_agent、middleware 系统、内置能力
- 关键 API：`create_agent`, `langchain.agents`
- 验收：与 Phase 1 功能等价，代码量显著减少

**Ch.8 — Human-in-the-loop**
- 目标：实现工具执行前的人工审批流程
- 核心概念：interrupt、Command、图状态暂停与恢复
- 关键 API：`interrupt()`, `Command(resume=...)`, `HumanInTheLoopMiddleware`
- 验收：敏感工具调用前前端弹出审批 UI，支持 approve / edit / reject

**Ch.9 — 长期记忆 Long-term Memory**
- 目标：实现跨 session、跨 thread 的用户偏好与知识持久化
- 核心概念：Store vs Checkpointer、namespace/key 组织、语义搜索
- 关键 API：`InMemoryStore`, `store.put/get/search`, `ToolRuntime`
- 验收：新 session 可检索上一 session 存储的用户信息

---

### Phase 3 — Deep Agents，全能 harness（Ch.10–11）

**Ch.10 — `create_deep_agent`**
- 目标：切换到 Deep Agents SDK，体验 batteries-included 的全能 agent
- 核心概念：任务规划工具、虚拟文件系统、子 agent 委派、CompositeBackend
- 关键 API：`create_deep_agent`, `deepagents`, `CompositeBackend`
- 验收：agent 能自主拆解复杂任务、读写文件、派生子 agent

**Ch.11 — Skills**
- 目标：通过 Skills 机制为 agent 注入可复用的领域知识
- 核心概念：Agent Skills 规范、skills 目录、AGENTS.md、/remember 机制
- 关键 API：skills frontmatter、skill 文件加载
- 验收：agent 能自动加载并运用自定义 skill，跨 session 学习用户偏好

---

## 数据流

```
用户输入
  └─→ Vue 3 ChatWindow
        └─→ POST /chat (带 thread_id, message)
              └─→ FastAPI routers/chat.py
                    └─→ agent/core.py (LangGraph 图)
                          ├─→ LLM (多提供商)
                          ├─→ Tools (工具节点)
                          └─→ Memory (Checkpointer / Store)
              └─→ SSE stream (token by token)
        └─→ 逐字渲染
```

---

## 关键设计决策

1. **SSE 而非 WebSocket**：对话场景单向流式已足够，实现更简单，便于学习
2. **uv 管理后端**：现代 Python 工程规范，`pyproject.toml` + `uv.lock`
3. **`agent/core.py` 作为唯一改动焦点**：每章学习内容聚焦，前端和路由不变
4. **低层 → 高层递进**：Phase 1 手写图 → Phase 2 create_agent → Phase 3 Deep Agents，每阶段都能对比上一阶段理解抽象收益
5. **多提供商统一接口**：通过 `init_chat_model()` 隔离提供商细节，章节间可自由切换模型
