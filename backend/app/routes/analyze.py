import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPBackgroundTasks
from app.models.schemas import AnalysisTask, AnalysisResult
from app.services.video_processor import VideoProcessor
from app.services.llm_analyzer import LLMAnalyzer

router = APIRouter()

# 内存中存储任务状态（MVP用，生产换Redis）
tasks: dict[str, AnalysisTask] = {}

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze", response_model=dict)
async def analyze_video(
    background_tasks: HTTPBackgroundTasks,
    file: UploadFile = File(...),
):
    """上传视频并发起分析任务"""
    # 校验文件类型
    allowed_ext = os.getenv("ALLOWED_EXTENSIONS", "mp4,mov,avi,mkv").split(",")
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}")

    # 保存文件
    task_id = str(uuid.uuid4())
    filename = f"{task_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 创建任务
    task = AnalysisTask(task_id=task_id, status="pending")
    tasks[task_id] = task

    # 后台执行分析
    background_tasks.add_task(run_analysis, task_id, filepath)

    return {"task_id": task_id, "status": "pending"}


@router.get("/analyze/{task_id}", response_model=AnalysisTask)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks[task_id]


async def run_analysis(task_id: str, filepath: str):
    """后台执行视频分析"""
    task = tasks[task_id]
    task.status = "processing"

    try:
        # 1. 视频预处理：抽帧 + 获取时长
        task.progress = 10
        processor = VideoProcessor(filepath)
        duration = processor.get_duration()
        frames = processor.extract_keyframes(interval=2.0)  # 每2秒抽一帧

        # 2. 调用多模态LLM分析
        task.progress = 40
        analyzer = LLMAnalyzer()
        result = await analyzer.analyze(
            video_duration=duration,
            frames=frames,
        )

        # 3. 返回结果
        task.progress = 100
        task.status = "completed"
        task.result = AnalysisResult(
            video_id=task_id,
            duration=duration,
            scenes=result["scenes"],
            memes=result["memes"],
            overall_summary=result["overall_summary"],
            created_at=__import__("datetime").datetime.now().isoformat(),
        )

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            os.remove(filepath)
