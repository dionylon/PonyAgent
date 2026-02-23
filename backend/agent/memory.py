import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def get_checkpointer():
    return AsyncSqliteSaver(aiosqlite.connect("db/checkpoints.db"))
