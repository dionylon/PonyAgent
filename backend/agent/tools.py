import math
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，支持四则运算和 math 函数，如 '2 + 2'、'sqrt(16)'。"""
    safe_globals = {"__builtins__": {}, **vars(math)}
    return str(eval(expression, safe_globals))


async def get_all_tools() -> list:
    """获取所有工具：calculator + MCP filesystem 工具。"""
    client = MultiServerMCPClient(
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            }
        }
    )
    mcp_tools = await client.get_tools()
    return [calculator] + mcp_tools
