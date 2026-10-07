import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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


class LLMAnalyzerResponseTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _response(payload):
        message = SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    @staticmethod
    def _payload():
        return {
            "overall_summary": "画面中出现悬念",
            "viewing_advice": {"verdict": "optional", "reason": "可选择观看"},
            "scenes": [],
            "memes": [
                {
                    "type": "suspense",
                    "start_time": 0.0,
                    "end_time": 1.0,
                    "description": "人物发现一封陌生信件",
                    "confidence": 0.75,
                }
            ],
        }

    @staticmethod
    def _analyzer(responses):
        create = AsyncMock(side_effect=responses)
        analyzer = object.__new__(LLMAnalyzer)
        analyzer.client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        analyzer.model = "deepseek-flash"
        analyzer.json_mode = True
        return analyzer, create

    async def _analyze(self, analyzer):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "frame.jpg"
            image_path.write_bytes(b"test frame")
            return await analyzer.analyze(
                video_duration=3.0,
                frames=[{"timestamp": 0.0, "image_path": str(image_path)}],
            )

    async def test_missing_meme_description_is_retried(self):
        valid = self._payload()
        missing = self._payload()
        del missing["memes"][0]["description"]
        analyzer, create = self._analyzer([self._response(missing), self._response(valid)])

        result = await self._analyze(analyzer)

        self.assertEqual(result.memes[0].description, "人物发现一封陌生信件")
        self.assertEqual(create.await_count, 2)
        retry = create.await_args_list[1].kwargs
        self.assertIn("memes.0.description", retry["messages"][-1]["content"])
        self.assertEqual(retry["response_format"], {"type": "json_object"})

    async def test_valid_response_does_not_retry(self):
        analyzer, create = self._analyzer([self._response(self._payload())])

        result = await self._analyze(analyzer)

        self.assertEqual(len(result.memes), 1)
        self.assertEqual(create.await_count, 1)

    async def test_repeated_missing_description_has_friendly_error(self):
        missing = self._payload()
        del missing["memes"][0]["description"]
        analyzer, create = self._analyzer([self._response(missing), self._response(missing)])

        with self.assertRaisesRegex(RuntimeError, "自动重试后仍失败"):
            await self._analyze(analyzer)

        self.assertEqual(create.await_count, 2)


if __name__ == "__main__":
    unittest.main()
