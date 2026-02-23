from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router

app = FastAPI(title="PonyAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
