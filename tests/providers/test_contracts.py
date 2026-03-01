import unittest

from scripts.providers.contracts import (
    ConversationRequest,
    ConversationResponse,
    ProviderError,
)


class TestProviderContracts(unittest.TestCase):
    def test_conversation_response_has_required_fields(self):
        resp = ConversationResponse(
            provider="local_default",
            model="local-model",
            output_text="ok",
            latency_ms=12,
        )
        self.assertEqual("local_default", resp.provider)
        self.assertEqual("ok", resp.output_text)

    def test_provider_error_retryable_flag(self):
        err = ProviderError(
            type="timeout",
            message="timeout",
            provider="openai",
            status_code=504,
            retryable=True,
        )
        self.assertTrue(err.retryable)

    def test_conversation_request_default_timeout(self):
        req = ConversationRequest(
            provider="local_default",
            messages=[{"role": "user", "content": "hello"}],
        )
        self.assertEqual(60000, req.timeout_ms)


if __name__ == "__main__":
    unittest.main()
