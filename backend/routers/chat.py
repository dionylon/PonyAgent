import json
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from agent.core import invoke_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@router.post("/api/chat")
async def chat(req: ChatRequest):
    async def event_gen():
        content = await invoke_agent(req.message)
        yield {"data": json.dumps({"type": "text", "content": content})}
        yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_gen())
