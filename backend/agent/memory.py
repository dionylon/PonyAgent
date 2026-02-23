import sqlite3

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite


async def get_checkpoiner():
    checkpointer = AsyncSqliteSaver(aiosqlite.connect("db/checkpoints.db", check_same_thread=False))
    return checkpointer