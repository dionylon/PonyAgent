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
                "command": "uvx",
                "args": ["mcp-server-time"],
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
