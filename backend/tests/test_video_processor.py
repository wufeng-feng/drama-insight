import unittest

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


if __name__ == "__main__":
    unittest.main()
