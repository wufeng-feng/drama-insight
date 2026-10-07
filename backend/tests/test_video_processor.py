import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.services.video_processor import VideoProcessor


class VideoProcessorTest(unittest.TestCase):
    def test_timestamps_cover_start_and_end(self):
        timestamps = VideoProcessor.build_timestamps(120, max_frames=20)

        self.assertEqual(len(timestamps), 20)
        self.assertEqual(timestamps[0], 0.0)
        self.assertAlmostEqual(timestamps[-1], 119.9, places=1)

    def test_short_video_uses_two_second_density(self):
        timestamps = VideoProcessor.build_timestamps(5, max_frames=20)

        self.assertEqual(len(timestamps), 3)
        self.assertEqual(timestamps[0], 0.0)
        self.assertAlmostEqual(timestamps[-1], 4.9, places=1)

    def test_invalid_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            VideoProcessor.build_timestamps(0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_extracts_jpeg_from_limited_range_video(self):
        with tempfile.TemporaryDirectory() as directory:
            video_path = Path(directory) / "limited-range.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "testsrc2=size=320x180:rate=24", "-t", "3", "-c:v", "mpeg4",
                    "-pix_fmt", "yuv420p", str(video_path),
                ],
                check=True,
                capture_output=True,
            )

            processor = VideoProcessor(str(video_path))
            try:
                frames = processor.extract_keyframes()
                self.assertEqual(len(frames), 2)
                for frame in frames:
                    self.assertTrue(Path(frame["image_path"]).read_bytes().startswith(b"\xff\xd8"))
            finally:
                processor.cleanup()


if __name__ == "__main__":
    unittest.main()
