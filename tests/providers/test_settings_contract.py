import unittest

from scripts.providers.settings import DEFAULT_TIMEOUT_MS, load_provider_settings


class TestSettingsContract(unittest.TestCase):
    def test_invalid_timeout_uses_default(self):
        settings = load_provider_settings(
            config_path=None,
            env={
                "AI_CHAT_PROVIDER": "openai",
                "AI_CHAT_TIMEOUT_MS": "-1",
            },
        )
        self.assertEqual(DEFAULT_TIMEOUT_MS, settings.timeout_ms)

    def test_provider_alias_is_normalized(self):
        settings = load_provider_settings(
            config_path=None,
            env={
                "AI_CHAT_PROVIDER": "OpenAI-Compatible",
            },
        )
        self.assertEqual("openai_compatible", settings.provider)

    def test_empty_provider_falls_back_to_local_default(self):
        settings = load_provider_settings(
            config_path=None,
            env={
                "AI_CHAT_PROVIDER": "   ",
            },
        )
        self.assertEqual("local_default", settings.provider)


if __name__ == "__main__":
    unittest.main()
