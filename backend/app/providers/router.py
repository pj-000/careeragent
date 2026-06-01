from app.providers.base import ModelProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.mock import MockProvider
from app.providers.qwen import QwenProvider


def get_model_provider(provider: str = "mock", **kwargs: object) -> ModelProvider:
    provider_name = provider.lower()
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "qwen":
        return QwenProvider(**kwargs)
    if provider_name == "deepseek":
        return DeepSeekProvider(**kwargs)
    raise ValueError(f"Unsupported model provider: {provider}")
