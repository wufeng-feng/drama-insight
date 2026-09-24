import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from app.models.schemas import (
    AnalysisResult,
    AnalysisTask,
    AnalyzeResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from app.services.llm_analyzer import LLMAnalyzer
from app.services.video_processor import VideoProcessor

router = APIRouter()

# MVP 使用进程内任务状态。服务重启后任务会丢失，生产环境应替换为 Redis。
tasks: dict[str, AnalysisTask] = {}

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024
FEEDBACK_FILE = Path(os.getenv("FEEDBACK_FILE", "./feedback/feedback.jsonl"))


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """上传单集视频并创建异步分析任务。"""
    original_name = file.filename or ""
    extension = Path(original_name).suffix.lower().lstrip(".")
    allowed_extensions = {
        item.strip().lower()
        for item in os.getenv("ALLOWED_EXTENSIONS", "mp4,mov,avi,mkv").split(",")
        if item.strip()
    }
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的格式：{extension or '未知'}",
        )

    task_id = str(uuid.uuid4())
    filepath = UPLOAD_DIR / f"{task_id}.{extension}"
    total_size = 0

    try:
        with filepath.open("wb") as output:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > MAX_VIDEO_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"视频不能超过 {MAX_VIDEO_SIZE_MB} MB",
                    )
                output.write(chunk)
    except HTTPException:
        filepath.unlink(missing_ok=True)
        raise
    except OSError as exc:
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="视频保存失败",
        ) from exc
    finally:
        await file.close()

    if total_size == 0:
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的视频为空",
        )

    tasks[task_id] = AnalysisTask(task_id=task_id, status="pending")
    background_tasks.add_task(run_analysis, task_id, str(filepath))
    return AnalyzeResponse(task_id=task_id)


@router.get("/analyze/{task_id}", response_model=AnalysisTask)
async def get_task_status(task_id: str):
    """查询任务状态。"""
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    return task


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(feedback: FeedbackRequest):
    """记录用户对剧情节点或高光片段的反馈。"""
    task = tasks.get(feedback.task_id)
    if task is None or task.result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在",
        )

    items = (
        task.result.scenes
        if feedback.item_type == "scene"
        else task.result.memes
    )
    if feedback.item_index >= len(items):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="反馈条目不存在",
        )

    feedback_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    record = {
        "feedback_id": feedback_id,
        "created_at": created_at,
        **feedback.model_dump(),
    }

    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_FILE.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")

    return FeedbackResponse(feedback_id=feedback_id, created_at=created_at)


async def run_analysis(task_id: str, filepath: str):
    """后台执行抽帧、模型分析和结果校验。"""
    task = tasks[task_id]
    task.status = "processing"
    processor = VideoProcessor(filepath)

    try:
        task.progress = 10
        duration = processor.get_duration()

        task.progress = 25
        max_frames = int(os.getenv("MAX_ANALYSIS_FRAMES", "20"))
        frames = processor.extract_keyframes(max_frames=max_frames)

        task.progress = 55
        analyzer = LLMAnalyzer()
        payload = await analyzer.analyze(
            video_duration=duration,
            frames=frames,
        )

        task.progress = 100
        task.status = "completed"
        task.result = AnalysisResult(
            video_id=task_id,
            duration=duration,
            created_at=datetime.now(timezone.utc).isoformat(),
            **payload.model_dump(),
        )
    except Exception as exc:
        task.status = "failed"
        task.error = str(exc)
    finally:
        processor.cleanup()
        Path(filepath).unlink(missing_ok=True)
