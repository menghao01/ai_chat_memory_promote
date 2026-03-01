from typing import Any, Callable, Dict, Optional, Tuple

from scripts.providers.contracts import ConversationRequest, ProviderError


Transport = Callable[[ConversationRequest], Dict[str, Any]]


def _status_code_from_exception(exc: Exception) -> Optional[int]:
    value = getattr(exc, "status_code", None)
    if isinstance(value, int):
        return value
    return None


def normalize_transport_exception(provider: str, exc: Exception) -> ProviderError:
    if isinstance(exc, TimeoutError):
        return ProviderError(
            type="timeout",
            message=str(exc) or "Provider request timed out.",
            provider=provider,
            status_code=_status_code_from_exception(exc),
            retryable=True,
            raw={"exception": repr(exc)},
        )

    return ProviderError(
        type="transport_error",
        message=str(exc) or "Provider transport failed.",
        provider=provider,
        status_code=_status_code_from_exception(exc),
        retryable=True,
        raw={"exception": repr(exc)},
    )


def execute_transport(
    provider: str,
    request: ConversationRequest,
    transport: Transport,
) -> Tuple[Optional[Dict[str, Any]], Optional[ProviderError]]:
    try:
        payload = transport(request)
    except Exception as exc:
        return None, normalize_transport_exception(provider, exc)
    return payload, None
