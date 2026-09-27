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


if __name__ == "__main__":
    unittest.main()