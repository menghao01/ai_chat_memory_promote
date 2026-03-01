import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import yaml

from scripts.providers.contracts import AuthConfig, ConversationRequest, EndpointConfig


DEFAULT_PROVIDER = "local_default"
DEFAULT_TIMEOUT_MS = 60000
MIN_TIMEOUT_MS = 1000
MAX_TIMEOUT_MS = 300000


@dataclass(frozen=True)
class ProviderSettings:
    provider: str = DEFAULT_PROVIDER
    fallback_provider: Optional[str] = None
    model: Optional[str] = None
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None


def normalize_provider_name(name: Optional[str]) -> str:
    value = (name or "").strip().lower().replace("-", "_")
    return value


def resolve_provider_chain(
    primary: Optional[str],
    fallback: Optional[str] = None,
    default_provider: str = DEFAULT_PROVIDER,
) -> List[str]:
    resolved_primary = normalize_provider_name(primary) or normalize_provider_name(default_provider)
    resolved_fallback = normalize_provider_name(fallback)

    chain = [resolved_primary]
    if resolved_fallback and resolved_fallback != resolved_primary:
        chain.append(resolved_fallback)
    return chain


def _coalesce_str(*values: Optional[Any]) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _coalesce_int(*values: Optional[Any], default: int) -> int:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        try:
            return int(text)
        except ValueError:
            continue
    return default


def _normalize_timeout_ms(timeout_ms: int) -> int:
    if timeout_ms < MIN_TIMEOUT_MS:
        return DEFAULT_TIMEOUT_MS
    if timeout_ms > MAX_TIMEOUT_MS:
        return MAX_TIMEOUT_MS
    return timeout_ms


def _read_yaml_file(config_path: Optional[str]) -> Dict[str, Any]:
    if not config_path:
        return {}

    path = Path(config_path)
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Provider config must be a mapping: {config_path}")
    return loaded


def load_provider_settings(
    config_path: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> ProviderSettings:
    effective_env = env or os.environ
    config = _read_yaml_file(config_path)
    provider_section = config.get("provider", {})
    if not isinstance(provider_section, dict):
        provider_section = {}

    provider = normalize_provider_name(
        _coalesce_str(
            effective_env.get("AI_CHAT_PROVIDER"),
            config.get("provider"),
            provider_section.get("primary"),
            provider_section.get("name"),
            DEFAULT_PROVIDER,
        )
    )

    fallback_provider = normalize_provider_name(
        _coalesce_str(
            effective_env.get("AI_CHAT_FALLBACK_PROVIDER"),
            config.get("fallback_provider"),
            provider_section.get("fallback"),
        )
    )
    if fallback_provider == "":
        fallback_provider = None

    model = _coalesce_str(
        effective_env.get("AI_CHAT_MODEL"),
        config.get("model"),
        provider_section.get("model"),
    )

    timeout_ms = _coalesce_int(
        effective_env.get("AI_CHAT_TIMEOUT_MS"),
        config.get("timeout_ms"),
        provider_section.get("timeout_ms"),
        default=DEFAULT_TIMEOUT_MS,
    )
    timeout_ms = _normalize_timeout_ms(timeout_ms)

    base_url = _coalesce_str(
        effective_env.get("AI_CHAT_BASE_URL"),
        config.get("base_url"),
        provider_section.get("base_url"),
    )

    api_key_env = _coalesce_str(
        effective_env.get("AI_CHAT_API_KEY_ENV"),
        config.get("api_key_env"),
        provider_section.get("api_key_env"),
    )

    return ProviderSettings(
        provider=provider or DEFAULT_PROVIDER,
        fallback_provider=fallback_provider,
        model=model,
        timeout_ms=timeout_ms,
        base_url=base_url,
        api_key_env=api_key_env,
    )


def build_request_from_settings(
    messages: List[Dict[str, Any]],
    settings: ProviderSettings,
) -> ConversationRequest:
    return ConversationRequest(
        provider=settings.provider,
        model=settings.model,
        messages=messages,
        timeout_ms=settings.timeout_ms,
        auth=AuthConfig(api_key_env=settings.api_key_env),
        endpoint=EndpointConfig(base_url=settings.base_url),
        fallback_provider=settings.fallback_provider,
    )
