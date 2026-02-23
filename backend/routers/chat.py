import json
import logging
import traceback

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from agent.core import stream_agent

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@router.post("/api/chat")
async def chat(req: ChatRequest):
    async def event_gen():
        logger.info("chat request: thread=%s message=%r", req.thread_id, req.message[:80])
        try:
            async for token in stream_agent(req.message, req.thread_id):
                yield {"data": json.dumps({"type": "text", "content": token}, ensure_ascii=False)}
            yield {"data": json.dumps({"type": "done"})}
        except Exception:
            logger.error("stream_agent failed:\n%s", traceback.format_exc())
            yield {"data": json.dumps({"type": "error", "message": "服务出错，请稍后重试"}, ensure_ascii=False)}

    return EventSourceResponse(event_gen())
