from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.schemas.model_providers import ModelRequest, ModelResponse


class ModelProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError


class ChatCompletionProvider(ModelProvider):
    api_url: str
    provider_name: str

    def __init__(self, api_key: str, model: str, timeout: float = 60.0) -> None:
        if not api_key:
            raise ValueError(f"{self.provider_name} api_key is required")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def build_payload(self, request: ModelRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": request.messages,
        }
        payload.update(dict(request.provider_options))

        if request.response_format is not None:
            payload["response_format"] = request.response_format
        elif request.response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "careeragent_response", "schema": request.response_schema},
            }

        return payload

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = self.build_payload(request)
        response = httpx.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()
        return self._response_from_chat_completion(raw)

    def _response_from_chat_completion(self, raw: dict[str, Any]) -> ModelResponse:
        choice = (raw.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        return ModelResponse(
            content=message.get("content") or "",
            reasoning_content=message.get("reasoning_content"),
            usage=raw.get("usage") or {},
            raw=raw,
            model=raw.get("model", self.model),
            finish_reason=choice.get("finish_reason") or "stop",
        )
