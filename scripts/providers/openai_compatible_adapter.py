import time
from dataclasses import replace
from typing import Any, Callable, Dict, Optional

from scripts.providers.base import BaseProvider
from scripts.providers.contracts import (
    ConversationRequest,
    ConversationResponse,
    EndpointConfig,
    ProviderError,
)
from scripts.providers.transport import execute_transport


Transport = Callable[[ConversationRequest], Dict[str, Any]]


class OpenAICompatibleProvider(BaseProvider):
    """
    Adapter for OpenAI-compatible gateways (LiteLLM/OpenRouter/Ollama/vLLM).
    """

    def __init__(
        self,
        default_model: str = "gpt-4.1-mini",
        base_url: Optional[str] = None,
        transport: Optional[Transport] = None,
    ):
        self.default_model = default_model
        self.base_url = base_url
        self.transport = transport

    def _resolve_request(self, request: ConversationRequest) -> ConversationRequest:
        effective_request = request
        if request.provider != "openai_compatible":
            effective_request = replace(effective_request, provider="openai_compatible")
        if effective_request.endpoint.base_url or not self.base_url:
            return effective_request
        return replace(effective_request, endpoint=EndpointConfig(base_url=self.base_url))

    def chat(self, request: ConversationRequest) -> ConversationResponse:
        started = time.perf_counter()
        model = request.model or self.default_model
        effective_request = self._resolve_request(request)

        if not self.transport:
            latency = int((time.perf_counter() - started) * 1000)
            return ConversationResponse(
                provider="openai_compatible",
                model=model,
                output_text="",
                latency_ms=latency,
                finish_reason="not_implemented",
                error=ProviderError(
                    type="provider_unavailable",
                    message="No transport configured for OpenAI-compatible provider.",
                    provider="openai_compatible",
                    retryable=False,
                    raw={"base_url": effective_request.endpoint.base_url},
                ),
            )

        payload, transport_error = execute_transport("openai_compatible", effective_request, self.transport)
        latency = int((time.perf_counter() - started) * 1000)
        if transport_error:
            return ConversationResponse(
                provider="openai_compatible",
                model=model,
                output_text="",
                latency_ms=latency,
                finish_reason="error",
                error=transport_error,
            )
        return ConversationResponse(
            provider="openai_compatible",
            model=model,
            output_text=str(payload.get("output_text", "")),
            latency_ms=latency,
            finish_reason=payload.get("finish_reason"),
            usage=payload.get("usage", {}),
            raw=payload,
        )
