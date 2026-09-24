import io
import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_reports_dependency_state(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["status"], {"ok", "degraded"})
        self.assertEqual(set(body["dependencies"]), {"ffmpeg", "ffprobe"})

    def test_unknown_task_returns_404(self):
        response = self.client.get("/api/analyze/not-a-real-task")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "任务不存在")

    def test_unsupported_file_is_rejected(self):
        response = self.client.post(
            "/api/analyze",
            files={"file": ("script.txt", io.BytesIO(b"not a video"), "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("不支持的格式", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
