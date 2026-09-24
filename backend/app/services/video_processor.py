import os
import subprocess
import json
from typing import List, Dict


class VideoProcessor:
    """视频处理：获取时长、抽关键帧"""

    def __init__(self, video_path: str):
        self.video_path = video_path

    def get_duration(self) -> float:
        """获取视频时长（秒）"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", self.video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])

    def extract_keyframes(self, interval: float = 2.0) -> List[Dict]:
        """
        按固定间隔抽帧，返回帧列表
        MVP版本：按间隔抽帧，生产可改用场景检测抽关键帧
        """
        duration = self.get_duration()
        frames = []

        # 临时目录存帧
        frame_dir = os.path.join(os.path.dirname(self.video_path), "frames")
        os.makedirs(frame_dir, exist_ok=True)

        timestamps = []
        t = 0.0
        while t < duration:
            timestamps.append(t)
            t += interval

        for i, ts in enumerate(timestamps):
            frame_path = os.path.join(frame_dir, f"frame_{i:04d}.jpg")
            cmd = [
                "ffmpeg", "-y", "-ss", str(ts),
                "-i", self.video_path,
                "-vframes", "1", "-q:v", "2",
                frame_path
            ]
            subprocess.run(cmd, capture_output=True)
            frames.append({
                "timestamp": ts,
                "image_path": frame_path,
            })

        return frames
