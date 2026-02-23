import asyncio
import logging
import math

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，支持四则运算和 math 函数，如 '2 + 2'、'sqrt(16)'。"""
    if "__" in expression:
        raise ValueError("表达式不允许包含 dunder 属性访问")
    safe_globals = {"__builtins__": {}, **vars(math)}
    return str(eval(expression, safe_globals))


async def get_all_tools() -> list:
    """获取所有工具：calculator + MCP filesystem 工具（MCP 不可用时回退到仅 calculator）。"""
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
        return [calculator] + mcp_tools
    except Exception as e:
        logger.warning("MCP 工具加载失败（%s），回退到仅 calculator", e)
        return [calculator]
