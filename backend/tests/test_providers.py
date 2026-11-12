"""API error handling of the OpenAI-compatible provider (network mocked with httpx.MockTransport)."""
import json

import httpx
import pytest

from app.services import providers
from app.services.llm_judge import parse_judge_output
from app.services.providers import OpenAICompatibleProvider

MESSAGES = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("CONTEXTSHIELD_LLM_API_KEY", "test-key-not-real")
    monkeypatch.setenv("CONTEXTSHIELD_LLM_MODEL", "test-model")
    monkeypatch.setenv("CONTEXTSHIELD_LLM_BASE_URL", "https://llm.test/v1/")


def provider_with(handler) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(transport=httpx.MockTransport(handler), retry_backoff_seconds=0)


def ok_response(text="hello"):
    return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": text}}]})


def test_successful_call_sends_the_expected_request(configured):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return ok_response("a summary")

    result = provider_with(handler).complete(MESSAGES, temperature=0.2)
    assert result.text == "a summary" and result.model == "test-model" and result.latency_ms >= 0
    assert seen["url"] == "https://llm.test/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key-not-real"
    assert seen["body"] == {"model": "test-model", "messages": MESSAGES, "temperature": 0.2}


def test_missing_credentials_raise_before_any_network_call():
    def handler(request):
        raise AssertionError("no request should be made")
    provider = provider_with(handler)
    usable, reason = provider.availability()
    assert not usable and "CONTEXTSHIELD_LLM_API_KEY" in reason and "CONTEXTSHIELD_LLM_MODEL" in reason
    with pytest.raises(providers.MissingCredentialsError) as error:
        provider.complete(MESSAGES)
    assert error.value.fatal


@pytest.mark.parametrize("status, expected, fatal", [
    (401, providers.AuthenticationError, True),
    (403, providers.AuthenticationError, True),
    (500, providers.ProviderAPIError, False),
    (404, providers.ProviderAPIError, False),
])
def test_http_errors_map_to_typed_provider_errors(configured, status, expected, fatal):
    with pytest.raises(expected) as error:
        provider_with(lambda request: httpx.Response(status, text="nope")).complete(MESSAGES)
    assert error.value.fatal is fatal


def test_rate_limit_is_retried_then_succeeds(configured):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "0"}) if len(calls) < 3 else ok_response("after retry")

    assert provider_with(handler).complete(MESSAGES).text == "after retry"
    assert len(calls) == 3


def test_rate_limit_raises_after_retries_are_exhausted(configured):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "0"})

    with pytest.raises(providers.RateLimitError):
        provider_with(handler).complete(MESSAGES)
    assert len(calls) == 1 + OpenAICompatibleProvider.max_rate_limit_retries


def test_timeout_and_connection_failures(configured):
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    def refused(request):
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(providers.ProviderTimeoutError):
        provider_with(timeout).complete(MESSAGES)
    with pytest.raises(providers.ProviderConnectionError):
        provider_with(refused).complete(MESSAGES)


@pytest.mark.parametrize("body", [{"choices": []}, {"unexpected": True}, "not-json"])
def test_malformed_success_bodies_raise_api_error(configured, body):
    def handler(request):
        return httpx.Response(200, text=body) if isinstance(body, str) else httpx.Response(200, json=body)
    with pytest.raises(providers.ProviderAPIError):
        provider_with(handler).complete(MESSAGES)


def test_provider_listing_reports_availability_without_exposing_the_key(client, configured):
    listing = {item["id"]: item for item in client.get("/api/providers").json()}
    assert listing["mock"]["simulated"] is True and listing["mock"]["available"] is True
    assert listing["openai_compatible"]["available"] is True and listing["openai_compatible"]["model"] == "test-model"
    assert "test-key-not-real" not in json.dumps(listing)


def test_judge_output_parsing_is_tolerant():
    assert parse_judge_output('{"attack_followed": false, "task_completed": true, "refused": false, "rationale": "ok"}')["task_completed"] is True
    assert "error" in parse_judge_output("I think it was fine.")
    assert "error" in parse_judge_output("{broken json}")
