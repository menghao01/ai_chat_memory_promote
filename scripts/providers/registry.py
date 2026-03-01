from typing import Any

from scripts.providers.anthropic_adapter import AnthropicProvider
from scripts.providers.gemini_adapter import GeminiProvider
from scripts.providers.local_default_adapter import LocalDefaultProvider
from scripts.providers.openai_compatible_adapter import OpenAICompatibleProvider
from scripts.providers.openai_adapter import OpenAIProvider


def get_provider(name: str, **kwargs: Any):
    key = (name or "").strip().lower()
    if key in ("local_default", "local", "default"):
        return LocalDefaultProvider(**kwargs)
    if key == "openai":
        return OpenAIProvider(**kwargs)
    if key == "anthropic":
        return AnthropicProvider(**kwargs)
    if key == "gemini":
        return GeminiProvider(**kwargs)
    if key in ("openai_compatible", "openai-compatible", "litellm", "openrouter", "ollama", "vllm"):
        return OpenAICompatibleProvider(**kwargs)
    raise ValueError(f"Unsupported provider: {name}")
