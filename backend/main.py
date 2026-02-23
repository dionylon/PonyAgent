import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router

# --- 日志配置 ---
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# 把 uvicorn/httpx 等库的日志也汇入同一配置
for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx", "openai"):
    logging.getLogger(name).handlers = []
    logging.getLogger(name).propagate = True

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
