import time
from typing import Any, Callable, Dict, Optional

from scripts.providers.base import BaseProvider
from scripts.providers.contracts import ConversationRequest, ConversationResponse


Transport = Callable[[ConversationRequest], Dict[str, Any]]


class LocalDefaultProvider(BaseProvider):
    """
    Adapter for host-managed local default model runtime.
    """

    def __init__(self, default_model: str = "local_default", transport: Optional[Transport] = None):
        self.default_model = default_model
        self.transport = transport

    def chat(self, request: ConversationRequest) -> ConversationResponse:
        started = time.perf_counter()
        model = request.model or self.default_model

        if self.transport:
            payload = self.transport(request)
            latency = int((time.perf_counter() - started) * 1000)
            return ConversationResponse(
                provider="local_default",
                model=model,
                output_text=str(payload.get("output_text", "")),
                latency_ms=latency,
                finish_reason=payload.get("finish_reason"),
                usage=payload.get("usage", {}),
                raw=payload,
            )

        latency = int((time.perf_counter() - started) * 1000)
        return ConversationResponse(
            provider="local_default",
            model=model,
            output_text="",
            latency_ms=latency,
            finish_reason="delegated",
            raw={"delegated_to_host_runtime": True},
        )
