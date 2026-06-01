from typing import Any

from app.providers.base import ModelProvider
from app.schemas.model_providers import ModelRequest, ModelResponse


class MockProvider(ModelProvider):
    provider_name = "mock"

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content=self._content_for_schema(request.response_schema),
            reasoning_content=None,
            usage={"input_tokens": 0, "output_tokens": 0},
            raw={"provider": self.provider_name},
            model=self.provider_name,
            finish_reason="stop",
        )

    def _content_for_schema(self, schema: dict[str, Any] | None, field_name: str | None = None) -> Any:
        if not schema:
            return "mock-content"

        schema_type = schema.get("type")
        if schema_type == "object":
            properties = schema.get("properties") or {}
            required = schema.get("required") or list(properties)
            return {
                name: self._content_for_schema(properties.get(name, {"type": "string"}), name)
                for name in required
            }
        if schema_type == "array":
            return [self._content_for_schema(schema.get("items") or {"type": "string"}, field_name)]
        if schema_type == "integer":
            return 1
        if schema_type == "number":
            return 1.0
        if schema_type == "boolean":
            return True

        title = schema.get("title")
        if isinstance(title, str) and title:
            return f"mock-{title}"
        if field_name:
            return f"mock-{field_name}"
        return "mock-summary"
