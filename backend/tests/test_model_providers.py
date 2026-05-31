import os

import httpx
import pytest

from app.providers.deepseek import DeepSeekProvider
from app.providers.base import ProviderError
from app.providers.mock import MockProvider
from app.providers.qwen import QwenProvider
from app.providers.router import get_model_provider
from app.schemas.model_providers import ModelRequest, ModelResponse


def test_model_request_exposes_provider_independent_generation_contract() -> None:
    request = ModelRequest(
        messages=[{"role": "user", "content": "Generate a profile summary."}],
        response_schema={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
        thinking_mode="on",
        reasoning_effort="high",
        tool_policy={"allowed_tools": ["artifact_write"]},
        response_format={"type": "json_object"},
        provider_options={"temperature": 0.2},
    )

    assert request.messages == [{"role": "user", "content": "Generate a profile summary."}]
    assert request.response_schema["required"] == ["summary"]
    assert request.thinking_mode == "on"
    assert request.reasoning_effort == "high"
    assert request.tool_policy == {"allowed_tools": ["artifact_write"]}
    assert request.response_format == {"type": "json_object"}
    assert request.provider_options == {"temperature": 0.2}


@pytest.mark.parametrize("thinking_mode", ["off", "auto", "on"])
def test_model_request_accepts_supported_thinking_modes(thinking_mode: str) -> None:
    assert ModelRequest(messages=[], thinking_mode=thinking_mode).thinking_mode == thinking_mode


@pytest.mark.parametrize("reasoning_effort", ["low", "medium", "high", "max"])
def test_model_request_accepts_supported_reasoning_efforts(reasoning_effort: str) -> None:
    assert ModelRequest(messages=[], reasoning_effort=reasoning_effort).reasoning_effort == reasoning_effort


def test_model_response_exposes_generation_result_contract() -> None:
    response = ModelResponse(
        content={"summary": "Candidate has strong backend experience."},
        reasoning_content="Reasoned from the resume evidence.",
        usage={"input_tokens": 20, "output_tokens": 10},
        raw={"id": "response-1"},
        model="test-model",
        finish_reason="stop",
    )

    assert response.content == {"summary": "Candidate has strong backend experience."}
    assert response.reasoning_content == "Reasoned from the resume evidence."
    assert response.usage == {"input_tokens": 20, "output_tokens": 10}
    assert response.raw == {"id": "response-1"}
    assert response.model == "test-model"
    assert response.finish_reason == "stop"


def test_model_response_requires_model_and_uses_dict_defaults() -> None:
    response = ModelResponse(content="ok", model="test-model", finish_reason="stop")

    assert response.usage == {}
    assert response.raw == {}


def test_mock_provider_returns_schema_safe_non_empty_content_without_reasoning() -> None:
    provider = MockProvider()
    request = ModelRequest(
        messages=[{"role": "user", "content": "Create a match result."}],
        response_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "score": {"type": "integer"},
                "is_fit": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "score", "is_fit", "tags"],
        },
    )

    response = provider.generate(request)

    assert isinstance(response, ModelResponse)
    assert response.reasoning_content is None
    assert response.model == "mock"
    assert response.finish_reason == "stop"
    assert response.content == {
        "summary": "mock-summary",
        "score": 1,
        "is_fit": True,
        "tags": ["mock-tags"],
    }


def test_qwen_payload_maps_thinking_mode_inside_adapter() -> None:
    request = ModelRequest(
        messages=[{"role": "user", "content": "hello"}],
        thinking_mode="on",
        reasoning_effort="high",
        provider_options={"temperature": 0.1},
    )

    payload = QwenProvider(api_key="test-key", model="qwen-test").build_payload(request)

    assert payload["model"] == "qwen-test"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.1
    assert payload["enable_thinking"] is True
    assert "thinking_mode" not in payload
    assert "reasoning_effort" not in payload


def test_qwen_provider_reads_model_and_base_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_MODEL", "qwen3.6-plus")
    monkeypatch.setenv("QWEN_BASE_URL", "https://qwen.example.test/v1/chat/completions")

    provider = QwenProvider(api_key="test-key")

    assert provider.model == "qwen3.6-plus"
    assert provider.api_url == "https://qwen.example.test/v1/chat/completions"


def test_deepseek_payload_maps_reasoning_options_inside_adapter_and_pops_provider_option() -> None:
    request = ModelRequest(
        messages=[{"role": "user", "content": "hello"}],
        thinking_mode="auto",
        reasoning_effort="medium",
        provider_options={"temperature": 0.1, "deepseek_effort": "max"},
    )

    payload = DeepSeekProvider(api_key="test-key", model="deepseek-test").build_payload(request)

    assert payload["model"] == "deepseek-test"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.1
    assert payload["reasoning_effort"] == "max"
    assert payload["thinking"] == {"type": "enabled"}
    assert "enable_reasoning" not in payload
    assert "deepseek_effort" not in payload
    assert "thinking_mode" not in payload


def test_deepseek_payload_disables_thinking_with_off_mode() -> None:
    request = ModelRequest(
        messages=[{"role": "user", "content": "hello"}],
        thinking_mode="off",
        reasoning_effort="medium",
    )

    payload = DeepSeekProvider(api_key="test-key", model="deepseek-test").build_payload(request)

    assert payload["thinking"] == {"type": "disabled"}
    assert "enable_reasoning" not in payload
    assert "reasoning_effort" not in payload


def test_deepseek_provider_reads_model_and_base_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://deepseek.example.test/chat/completions")

    provider = DeepSeekProvider(api_key="test-key")

    assert provider.model == "deepseek-v4-flash"
    assert provider.api_url == "https://deepseek.example.test/chat/completions"


def test_chat_completion_provider_maps_http_errors_to_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_request(*args, **kwargs):
        raise httpx.TimeoutException("upstream timeout")

    monkeypatch.setattr(httpx, "post", fail_request)
    provider = QwenProvider(api_key="test-key", model="qwen-test")

    with pytest.raises(ProviderError, match="qwen"):
        provider.generate(ModelRequest(messages=[{"role": "user", "content": "hello"}]))


def test_chat_completion_provider_maps_malformed_success_response_to_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def malformed_response(*args, **kwargs):
        return httpx.Response(
            200,
            json={"id": "missing-choices"},
            request=httpx.Request("POST", "https://provider.example.test/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", malformed_response)
    provider = QwenProvider(api_key="test-key", model="qwen-test")

    with pytest.raises(ProviderError, match="malformed"):
        provider.generate(ModelRequest(messages=[{"role": "user", "content": "hello"}]))


@pytest.mark.parametrize(
    "raw_response",
    [
        [],
        {"choices": [{}]},
        {"choices": [{"message": []}]},
    ],
)
def test_chat_completion_provider_rejects_invalid_success_response_shapes(
    raw_response,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def malformed_response(*args, **kwargs):
        return httpx.Response(
            200,
            json=raw_response,
            request=httpx.Request("POST", "https://provider.example.test/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", malformed_response)
    provider = QwenProvider(api_key="test-key", model="qwen-test")

    with pytest.raises(ProviderError, match="malformed"):
        provider.generate(ModelRequest(messages=[{"role": "user", "content": "hello"}]))


def test_router_returns_configured_provider() -> None:
    assert isinstance(get_model_provider("mock"), MockProvider)
    assert isinstance(get_model_provider("qwen", api_key="test-key"), QwenProvider)
    assert isinstance(get_model_provider("deepseek", api_key="test-key"), DeepSeekProvider)


@pytest.mark.skipif(not os.getenv("QWEN_API_KEY"), reason="QWEN_API_KEY is not set")
def test_qwen_provider_smoke_generate_when_api_key_is_configured() -> None:
    provider = QwenProvider(api_key=os.environ["QWEN_API_KEY"])
    response = provider.generate(ModelRequest(messages=[{"role": "user", "content": "Reply with ok."}]))

    assert response.content


@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="DEEPSEEK_API_KEY is not set")
def test_deepseek_provider_smoke_generate_when_api_key_is_configured() -> None:
    provider = DeepSeekProvider(api_key=os.environ["DEEPSEEK_API_KEY"])
    response = provider.generate(ModelRequest(messages=[{"role": "user", "content": "Reply with ok."}]))

    assert response.content
