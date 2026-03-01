import unittest

from scripts.providers.contracts import ConversationRequest
from scripts.providers.registry import get_provider


class TestOpenAICompatibleProvider(unittest.TestCase):
    def test_registry_supports_openai_compatible_and_aliases(self):
        main = get_provider("openai_compatible")
        alias = get_provider("openrouter")
        self.assertEqual(main.__class__.__name__, alias.__class__.__name__)

    def test_chat_uses_transport_contract(self):
        def transport(_request: ConversationRequest):
            return {
                "output_text": "compatible-ok",
                "finish_reason": "stop",
                "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            }

        provider = get_provider("openai_compatible", transport=transport)
        req = ConversationRequest(
            provider="openai_compatible",
            model="qwen2.5",
            messages=[{"role": "user", "content": "hello"}],
        )
        resp = provider.chat(req)
        self.assertEqual("openai_compatible", resp.provider)
        self.assertEqual("compatible-ok", resp.output_text)
        self.assertEqual("stop", resp.finish_reason)

    def test_default_base_url_applies_when_request_has_none(self):
        captured = {}

        def transport(req: ConversationRequest):
            captured["base_url"] = req.endpoint.base_url
            return {"output_text": "ok"}

        provider = get_provider(
            "openai_compatible",
            base_url="http://127.0.0.1:11434/v1",
            transport=transport,
        )
        req = ConversationRequest(
            provider="openai_compatible",
            messages=[{"role": "user", "content": "ping"}],
        )
        provider.chat(req)
        self.assertEqual("http://127.0.0.1:11434/v1", captured["base_url"])

    def test_no_transport_returns_structured_error(self):
        provider = get_provider("openai_compatible")
        req = ConversationRequest(
            provider="openai_compatible",
            messages=[{"role": "user", "content": "hello"}],
        )
        resp = provider.chat(req)
        self.assertIsNotNone(resp.error)
        self.assertEqual("provider_unavailable", resp.error.type)


if __name__ == "__main__":
    unittest.main()
