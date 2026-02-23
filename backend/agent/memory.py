import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config import settings


async def get_checkpointer():
    return AsyncSqliteSaver(aiosqlite.connect(settings.checkpoint_db_path))
