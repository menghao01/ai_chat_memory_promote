import unittest

from scripts.providers.contracts import ConversationRequest, EndpointConfig
from scripts.providers.registry import get_provider


class TestTransportCompatible(unittest.TestCase):
    def test_base_url_precedence_request_over_provider_default(self):
        captured = {}

        def transport(req: ConversationRequest):
            captured["base_url"] = req.endpoint.base_url
            return {"output_text": "ok"}

        provider = get_provider(
            "openai_compatible",
            base_url="https://provider-default.example/v1",
            transport=transport,
        )
        request = ConversationRequest(
            provider="openai_compatible",
            endpoint=EndpointConfig(base_url="https://request-override.example/v1"),
            messages=[{"role": "user", "content": "hello"}],
        )
        provider.chat(request)
        self.assertEqual("https://request-override.example/v1", captured["base_url"])

    def test_alias_route_uses_canonical_provider_contract(self):
        captured = {}

        def transport(req: ConversationRequest):
            captured["provider"] = req.provider
            return {"output_text": "alias-ok", "finish_reason": "stop"}

        provider = get_provider("openrouter", transport=transport)
        request = ConversationRequest(
            provider="openrouter",
            messages=[{"role": "user", "content": "hello"}],
        )
        response = provider.chat(request)
        self.assertEqual("openai_compatible", response.provider)
        self.assertEqual("openai_compatible", captured["provider"])

    def test_transport_timeout_is_normalized(self):
        def transport(_request: ConversationRequest):
            raise TimeoutError("compatible timeout")

        provider = get_provider("openai_compatible", transport=transport)
        request = ConversationRequest(
            provider="openai_compatible",
            messages=[{"role": "user", "content": "hello"}],
        )
        response = provider.chat(request)
        self.assertIsNotNone(response.error)
        self.assertEqual("timeout", response.error.type)
        self.assertTrue(response.error.retryable)


if __name__ == "__main__":
    unittest.main()
