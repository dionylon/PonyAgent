import logging
from contextlib import asynccontextmanager

import logging_config
logging_config.setup()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from agent.tools import init_tools  # noqa: E402
from config import settings  # noqa: E402
from routers.chat import router  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tools()
    yield


app = FastAPI(title="PonyAgent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

logger.info("PonyAgent backend started")
