import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    model = os.getenv("MODEL", "anthropic:claude-sonnet-4-5-20250929")
    return init_chat_model(model)
