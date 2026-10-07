import os
import unittest
from unittest.mock import patch

from app.services.llm_analyzer import LLMAnalyzer


class LLMAnalyzerConfigTest(unittest.TestCase):
    def test_openai_model_is_default(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=True):
            with patch("app.services.llm_analyzer.AsyncOpenAI") as client:
                analyzer = LLMAnalyzer()

        self.assertEqual(analyzer.model, "gpt-4.1-mini")
        self.assertTrue(analyzer.json_mode)
        self.assertNotIn("base_url", client.call_args.kwargs)

    def test_placeholder_key_is_rejected(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "your-api-key-here"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "LLM_API_KEY"):
                LLMAnalyzer()

    def test_deepseek_model_and_base_url_can_be_configured(self):
        settings = {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://api.deepseek.com",
            "LLM_MODEL": "deepseek-flash",
        }
        with patch.dict(os.environ, settings, clear=True):
            with patch("app.services.llm_analyzer.AsyncOpenAI") as client:
                analyzer = LLMAnalyzer()

        self.assertEqual(analyzer.model, "deepseek-flash")
        self.assertEqual(client.call_args.kwargs["base_url"], "https://api.deepseek.com")


if __name__ == "__main__":
    unittest.main()
