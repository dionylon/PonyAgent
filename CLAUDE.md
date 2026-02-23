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
- 所有可通过环境变量调整的配置项（路径、阈值、超时、来源白名单等）统一放入 `backend/config.py` 的 `Settings` 类，禁止在业务代码中直接使用 `os.getenv` 或硬编码配置值

## 代码质量检查

每次对后端文件进行大改动后，必须执行以下检查：

```bash
# Lint（在 backend/ 目录下）
uv run ruff check .

# 语法检查（单文件快速验证）
uv run python -m py_compile <file.py>
```

- `ruff` 已加入 dev 依赖，直接用 `uv run ruff check .` 扫描整个 backend
- E402（import 顺序）：若 import 顺序有意为之（如 logging 初始化必须先于其他 import），在对应行加 `# noqa: E402` 抑制
- F401（未使用 import）：直接删除，或用 `uv run ruff check --fix <file>` 自动修复
- 所有 import 应集中在文件顶部，禁止散落在函数定义之间



当前项目遵循 `ROADMAP.md` 中定义的三阶段 11 章计划：

- **Phase 1（Ch.1–6）**：LangGraph 底层，手动构建
- **Phase 2（Ch.7–9）**：LangChain `create_agent` 中层抽象
- **Phase 3（Ch.10–11）**：Deep Agents 全能 harness

详见 `docs/plans/2026-02-23-ponyagent-design.md`
