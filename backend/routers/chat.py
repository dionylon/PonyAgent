import json
import logging
import traceback

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from agent.core import invoke_agent

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
            content = await invoke_agent(req.message)
            logger.debug("llm response length=%d", len(content))
            yield {"data": json.dumps({"type": "text", "content": content})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception:
            logger.error("invoke_agent failed:\n%s", traceback.format_exc())
            yield {"data": json.dumps({"type": "error", "message": "服务出错，请稍后重试"})}

    return EventSourceResponse(event_gen())
