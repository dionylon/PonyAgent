import logging

import logging_config
logging_config.setup()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from routers.chat import router  # noqa: E402

logger = logging.getLogger(__name__)

# --- FastAPI ---
app = FastAPI(title="PonyAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

logger.info("PonyAgent backend started")
