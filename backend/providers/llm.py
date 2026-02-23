from langchain.chat_models import init_chat_model

from config import settings


def get_llm():
    kwargs = {}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    return init_chat_model(settings.model, model_provider="openai", **kwargs)
