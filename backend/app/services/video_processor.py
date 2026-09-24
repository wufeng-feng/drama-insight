import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List


class VideoProcessor:
    """获取视频时长，并在整段视频上均匀抽取画面帧。"""

    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.frame_dir = self.video_path.parent / f"{self.video_path.stem}_frames"

    @staticmethod
    def dependency_status() -> Dict[str, bool]:
        return {
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "ffprobe": shutil.which("ffprobe") is not None,
        }

    @classmethod
    def ensure_dependencies(cls) -> None:
        missing = [name for name, installed in cls.dependency_status().items() if not installed]
        if missing:
            joined = "、".join(missing)
            raise RuntimeError(f"缺少视频处理程序：{joined}。请安装 FFmpeg 并加入 PATH。")

    @staticmethod
    def build_timestamps(duration: float, max_frames: int = 20) -> List[float]:
        """在整段视频中均匀取样，并确保包含接近结尾的画面。"""
        if duration <= 0:
            raise ValueError("视频时长必须大于 0")
        if max_frames < 1:
            raise ValueError("max_frames 必须大于 0")

        frame_count = min(max_frames, max(1, math.ceil(duration / 2)))
        if frame_count == 1:
            return [0.0]

        last_timestamp = max(0.0, duration - 0.1)
        step = last_timestamp / (frame_count - 1)
        return [round(index * step, 3) for index in range(frame_count)]

    def _run(self, command: List[str], tool_name: str) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "未知错误"
            raise RuntimeError(f"{tool_name} 执行失败：{error}")
        return result

    def get_duration(self) -> float:
        """获取视频时长（秒）。"""
        self.ensure_dependencies()
        result = self._run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_entries",
                "format=duration",
                str(self.video_path),
            ],
            "ffprobe",
        )
        try:
            info = json.loads(result.stdout)
            duration = float(info["format"]["duration"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("无法读取视频时长，请确认文件未损坏") from exc

        if duration <= 0:
            raise RuntimeError("视频时长无效")
        return duration

    def extract_keyframes(self, max_frames: int = 20) -> List[Dict]:
        """均匀抽帧，返回帧文件路径及其真实时间戳。"""
        duration = self.get_duration()
        timestamps = self.build_timestamps(duration, max_frames=max_frames)

        self.cleanup()
        self.frame_dir.mkdir(parents=True, exist_ok=True)

        frames: List[Dict] = []
        for index, timestamp in enumerate(timestamps):
            frame_path = self.frame_dir / f"frame_{index:04d}.jpg"
            self._run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    str(timestamp),
                    "-i",
                    str(self.video_path),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    str(frame_path),
                ],
                "ffmpeg",
            )
            if not frame_path.exists() or frame_path.stat().st_size == 0:
                raise RuntimeError(f"抽帧失败：{timestamp:.1f} 秒")
            frames.append({"timestamp": timestamp, "image_path": str(frame_path)})

        return frames

    def cleanup(self) -> None:
        if self.frame_dir.exists():
            shutil.rmtree(self.frame_dir)
