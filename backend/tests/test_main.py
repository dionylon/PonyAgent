from unittest.mock import patch

import agent.tools as tools_module
from agent.tools import calculator


async def test_lifespan_calls_init_tools():
    """服务启动时 lifespan 应调用 init_tools() 并完成工具缓存。"""
    import main as main_module
    from main import app, lifespan

    original = tools_module._cached_tools
    tools_module._cached_tools = None

    async def fake_init():
        tools_module._cached_tools = [calculator]

    try:
        with patch.object(main_module, "init_tools", side_effect=fake_init) as mock_init:
            async with lifespan(app):
                pass

        mock_init.assert_called_once()
        assert tools_module.get_cached_tools() == [calculator]
    finally:
        tools_module._cached_tools = original
