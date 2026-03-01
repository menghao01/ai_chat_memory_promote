import os
import tempfile
import unittest
from unittest.mock import patch

from scripts.chat_entry import chat_with_fallback
from scripts.providers.contracts import ConversationRequest, ConversationResponse, ProviderError
from scripts.providers.settings import load_provider_settings, resolve_provider_chain


class TestProviderFallback(unittest.TestCase):
    def test_resolve_provider_chain(self):
        chain = resolve_provider_chain(primary="openai", fallback="local_default")
        self.assertEqual(["openai", "local_default"], chain)

    def test_chat_fallback_to_local_default_when_primary_raises(self):
        def openai_transport(_request: ConversationRequest):
            raise RuntimeError("gateway timeout")

        def local_transport(_request: ConversationRequest):
            return {"output_text": "local-ok", "finish_reason": "stop"}

        request = ConversationRequest(
            provider="openai",
            fallback_provider="local_default",
            messages=[{"role": "user", "content": "hello"}],
        )
        response = chat_with_fallback(
            request,
            provider_kwargs_map={
                "openai": {"transport": openai_transport},
                "local_default": {"transport": local_transport},
            },
        )
        self.assertEqual("local_default", response.provider)
        self.assertEqual("local-ok", response.output_text)
        self.assertIn("fallback_trace", response.raw)
        self.assertEqual("openai", response.raw["fallback_trace"][0]["provider"])

    def test_non_retryable_policy_error_does_not_fallback(self):
        request = ConversationRequest(
            provider="openai",
            fallback_provider="local_default",
            messages=[{"role": "user", "content": "hello"}],
        )

        first_error = ConversationResponse(
            provider="openai",
            model="gpt-4.1-mini",
            output_text="",
            latency_ms=1,
            finish_reason="error",
            error=ProviderError(
                type="invalid_request",
                message="policy rejected",
                provider="openai",
                retryable=False,
            ),
        )

        with patch("scripts.chat_entry._chat_once", return_value=first_error) as mocked_once:
            response = chat_with_fallback(request)

        self.assertIsNotNone(response.error)
        self.assertEqual("invalid_request", response.error.type)
        self.assertEqual(1, mocked_once.call_count)

    def test_unsupported_provider_only_falls_back_when_allowed(self):
        blocked_request = ConversationRequest(
            provider="unknown_gateway",
            fallback_provider="local_default",
            messages=[{"role": "user", "content": "hello"}],
        )
        blocked_response = chat_with_fallback(
            blocked_request,
            provider_kwargs_map={"local_default": {"transport": lambda _r: {"output_text": "local-ok"}}},
        )
        self.assertIsNotNone(blocked_response.error)
        self.assertEqual("unsupported_provider", blocked_response.error.type)

        allowed_request = ConversationRequest(
            provider="unknown_gateway",
            fallback_provider="local_default",
            messages=[{"role": "user", "content": "hello"}],
            metadata={"allow_unsupported_fallback": True},
        )
        allowed_response = chat_with_fallback(
            allowed_request,
            provider_kwargs_map={"local_default": {"transport": lambda _r: {"output_text": "local-ok"}}},
        )
        self.assertIsNone(allowed_response.error)
        self.assertEqual("local_default", allowed_response.provider)
        self.assertEqual("local-ok", allowed_response.output_text)

    def test_load_provider_settings_env_overrides_yaml(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
            handle.write(
                "provider:\n"
                "  primary: openai\n"
                "  fallback: local_default\n"
                "  model: gpt-from-yaml\n"
                "  timeout_ms: 45000\n"
                "  base_url: https://yaml.example/v1\n"
            )
            config_path = handle.name

        try:
            env = {
                "AI_CHAT_PROVIDER": "gemini",
                "AI_CHAT_MODEL": "gemini-2.0-flash",
                "AI_CHAT_TIMEOUT_MS": "70000",
            }
            settings = load_provider_settings(config_path=config_path, env=env)
        finally:
            os.remove(config_path)

        self.assertEqual("gemini", settings.provider)
        self.assertEqual("local_default", settings.fallback_provider)
        self.assertEqual("gemini-2.0-flash", settings.model)
        self.assertEqual(70000, settings.timeout_ms)
        self.assertEqual("https://yaml.example/v1", settings.base_url)


if __name__ == "__main__":
    unittest.main()
