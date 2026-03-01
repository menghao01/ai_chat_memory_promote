import time
from typing import Any, Callable, Dict, Optional

from scripts.providers.base import BaseProvider
from scripts.providers.contracts import (
    ConversationRequest,
    ConversationResponse,
    ProviderError,
)
from scripts.providers.transport import execute_transport


Transport = Callable[[ConversationRequest], Dict[str, Any]]


class OpenAIProvider(BaseProvider):
    def __init__(self, default_model: str = "gpt-4.1-mini", transport: Optional[Transport] = None):
        self.default_model = default_model
        self.transport = transport

    def chat(self, request: ConversationRequest) -> ConversationResponse:
        started = time.perf_counter()
        model = request.model or self.default_model

        if not self.transport:
            latency = int((time.perf_counter() - started) * 1000)
            return ConversationResponse(
                provider="openai",
                model=model,
                output_text="",
                latency_ms=latency,
                finish_reason="not_implemented",
                error=ProviderError(
                    type="provider_unavailable",
                    message="No transport configured for OpenAI provider.",
                    provider="openai",
                    retryable=False,
                ),
            )

        payload, transport_error = execute_transport("openai", request, self.transport)
        latency = int((time.perf_counter() - started) * 1000)
        if transport_error:
            return ConversationResponse(
                provider="openai",
                model=model,
                output_text="",
                latency_ms=latency,
                finish_reason="error",
                error=transport_error,
            )
        return ConversationResponse(
            provider="openai",
            model=model,
            output_text=str(payload.get("output_text", "")),
            latency_ms=latency,
            finish_reason=payload.get("finish_reason"),
            usage=payload.get("usage", {}),
            raw=payload,
        )
