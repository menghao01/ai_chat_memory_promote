import unittest

from scripts.providers.contracts import ConversationRequest
from scripts.providers.registry import get_provider


class TestNativeTransportNormalization(unittest.TestCase):
    def test_timeout_exception_is_normalized(self):
        def timeout_transport(_request: ConversationRequest):
            raise TimeoutError("request timed out")

        for provider_name in ("openai", "anthropic", "gemini"):
            provider = get_provider(provider_name, transport=timeout_transport)
            response = provider.chat(
                ConversationRequest(
                    provider=provider_name,
                    messages=[{"role": "user", "content": "ping"}],
                )
            )
            self.assertIsNotNone(response.error)
            self.assertEqual("timeout", response.error.type)
            self.assertTrue(response.error.retryable)

    def test_success_payload_contract_remains_stable(self):
        def ok_transport(_request: ConversationRequest):
            return {
                "output_text": "ok",
                "finish_reason": "stop",
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            }

        provider = get_provider("openai", transport=ok_transport)
        response = provider.chat(
            ConversationRequest(
                provider="openai",
                messages=[{"role": "user", "content": "hello"}],
            )
        )
        self.assertIsNone(response.error)
        self.assertEqual("ok", response.output_text)
        self.assertEqual("stop", response.finish_reason)


if __name__ == "__main__":
    unittest.main()
