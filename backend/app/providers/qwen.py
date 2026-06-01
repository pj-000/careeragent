import os
from typing import Any

from app.providers.base import ChatCompletionProvider
from app.schemas.model_providers import ModelRequest


class QwenProvider(ChatCompletionProvider):
    provider_name = "qwen"
    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
        base_url: str | None = None,
    ) -> None:
        self.api_url = base_url or os.getenv("QWEN_BASE_URL") or self.api_url
        super().__init__(
            api_key=api_key or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY", ""),
            model=model or os.getenv("QWEN_MODEL", "qwen3.6-plus"),
            timeout=timeout,
        )

    def build_payload(self, request: ModelRequest) -> dict[str, Any]:
        payload = super().build_payload(request)
        if request.thinking_mode == "on":
            payload["enable_thinking"] = True
        elif request.thinking_mode == "off":
            payload["enable_thinking"] = False
        return payload
