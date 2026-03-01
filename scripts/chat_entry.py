import argparse
from dataclasses import replace
from typing import Any, Dict, Mapping, Optional

from scripts.providers.contracts import ConversationRequest, ConversationResponse, ProviderError
from scripts.providers.registry import get_provider
from scripts.providers.settings import (
    build_request_from_settings,
    load_provider_settings,
    resolve_provider_chain,
)


FALLBACK_ERROR_ALLOWLIST = {"provider_unavailable", "transport_error"}


def _make_error_response(
    provider: str,
    model: str,
    error_type: str,
    message: str,
    retryable: bool,
    raw: Optional[Dict[str, Any]] = None,
) -> ConversationResponse:
    return ConversationResponse(
        provider=provider,
        model=model,
        output_text="",
        latency_ms=0,
        finish_reason="error",
        error=ProviderError(
            type=error_type,
            message=message,
            provider=provider,
            retryable=retryable,
            raw=raw or {},
        ),
        raw=raw or {},
    )


def _should_fallback(error: ProviderError, request: ConversationRequest) -> bool:
    if error.retryable:
        return True
    if error.type == "unsupported_provider":
        return bool(request.metadata.get("allow_unsupported_fallback"))
    return error.type in FALLBACK_ERROR_ALLOWLIST


def _chat_once(
    request: ConversationRequest,
    provider_kwargs_map: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> ConversationResponse:
    provider_name = request.provider
    provider_kwargs = dict((provider_kwargs_map or {}).get(provider_name, {}))
    model = request.model or "unknown"

    try:
        provider = get_provider(provider_name, **provider_kwargs)
    except ValueError as exc:
        return _make_error_response(
            provider=provider_name,
            model=model,
            error_type="unsupported_provider",
            message=str(exc),
            retryable=False,
        )

    try:
        return provider.chat(request)
    except Exception as exc:  # pragma: no cover - defensive layer for adapters
        return _make_error_response(
            provider=provider_name,
            model=model,
            error_type="transport_error",
            message=f"Provider call failed: {exc}",
            retryable=True,
            raw={"exception": repr(exc)},
        )


def chat_with_fallback(
    request: ConversationRequest,
    provider_kwargs_map: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> ConversationResponse:
    chain = resolve_provider_chain(request.provider, request.fallback_provider)
    fallback_trace = []
    last_response = None

    for idx, provider_name in enumerate(chain):
        current_request = replace(request, provider=provider_name, fallback_provider=None)
        response = _chat_once(current_request, provider_kwargs_map=provider_kwargs_map)
        if not response.error:
            response.raw = dict(response.raw)
            if fallback_trace:
                response.raw["fallback_trace"] = fallback_trace
            return response

        last_response = response
        fallback_trace.append(
            {
                "provider": provider_name,
                "error_type": response.error.type,
                "retryable": response.error.retryable,
                "message": response.error.message,
            }
        )

        has_next = idx < len(chain) - 1
        if has_next and _should_fallback(response.error, current_request):
            continue

        response.raw = dict(response.raw)
        response.raw["fallback_trace"] = fallback_trace
        return response

    if last_response:
        last_response.raw = dict(last_response.raw)
        last_response.raw["fallback_trace"] = fallback_trace
        return last_response

    return _make_error_response(
        provider=request.provider,
        model=request.model or "unknown",
        error_type="provider_unavailable",
        message="No provider resolved from request settings.",
        retryable=False,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat entry with provider config and fallback chain.")
    parser.add_argument("--config", default="config/provider.yaml", help="Provider config yaml path")
    parser.add_argument("--message", required=True, help="Single user message")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    settings = load_provider_settings(config_path=args.config)
    request = build_request_from_settings(
        messages=[{"role": "user", "content": args.message}],
        settings=settings,
    )
    response = chat_with_fallback(request)
    if response.error:
        print(f"[{response.provider}] error={response.error.type} message={response.error.message}")
        return 1
    print(response.output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
