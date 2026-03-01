import unittest

from scripts.providers.contracts import ConversationRequest
from scripts.providers.registry import get_provider


def _mock_transport(_request: ConversationRequest):
    return {
        "output_text": "mock-ok",
        "finish_reason": "stop",
        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
    }


class TestNativeAdapters(unittest.TestCase):
    def test_registry_returns_native_adapters(self):
        for name in ("openai", "anthropic", "gemini"):
            provider = get_provider(name, transport=_mock_transport)
            self.assertIsNotNone(provider)

    def test_native_adapter_chat_contract(self):
        provider = get_provider("openai", transport=_mock_transport)
        req = ConversationRequest(
            provider="openai",
            model="gpt-test",
            messages=[{"role": "user", "content": "hi"}],
        )
        resp = provider.chat(req)
        self.assertEqual("openai", resp.provider)
        self.assertEqual("mock-ok", resp.output_text)
        self.assertEqual("stop", resp.finish_reason)


if __name__ == "__main__":
    unittest.main()
