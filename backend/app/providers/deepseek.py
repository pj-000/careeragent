import os
from typing import Any

from app.providers.base import ChatCompletionProvider
from app.schemas.model_providers import ModelRequest


class DeepSeekProvider(ChatCompletionProvider):
    provider_name = "deepseek"
    api_url = "https://api.deepseek.com/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
        base_url: str | None = None,
    ) -> None:
        self.api_url = base_url or os.getenv("DEEPSEEK_BASE_URL") or self.api_url
        super().__init__(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            timeout=timeout,
        )

    def build_payload(self, request: ModelRequest) -> dict[str, Any]:
        payload = super().build_payload(request)
        provider_options = dict(request.provider_options)
        deepseek_effort = provider_options.pop("deepseek_effort", None)
        provider_options.pop("enable_reasoning", None)
        provider_options.pop("thinking", None)
        provider_options.pop("reasoning_effort", None)

        for key in request.provider_options:
            payload.pop(key, None)
        payload.update(provider_options)

        if request.thinking_mode == "off":
            payload["thinking"] = {"type": "disabled"}
        else:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = _normalize_deepseek_effort(
                str(deepseek_effort or request.reasoning_effort)
            )

        return payload


def _normalize_deepseek_effort(effort: str) -> str:
    if effort in {"high", "max"}:
        return effort
    return "high"
