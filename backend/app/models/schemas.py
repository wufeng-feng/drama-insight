from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class SceneType(str, Enum):
    """剧情节点类型"""
    HOOK = "opening_hook"        # 开场钩子
    CONFLICT = "conflict"        # 冲突升级
    TWIST = "key_twist"          # 关键反转
    CLIMAX = "climax"            # 高潮名场面
    CLIFFHANGER = "cliffhanger"  # 结尾钩子


class MemeType(str, Enum):
    """名场面类型"""
    IDENTITY_REVEAL = "identity_reveal"   # 身份揭露
    FACE_SLAP = "face_slap"               # 打脸反转
    EMOTIONAL = "emotional"              # 情感爆发
    ACTION = "action"                    # 高能动作
    SUSPENSE = "suspense"                # 悬念钩子


class Scene(BaseModel):
    """剧情节点"""
    type: SceneType
    start_time: float  # 秒
    end_time: float    # 秒
    summary: str       # 剧情摘要（50字内）
    confidence: float  # 置信度 0-1


class MemeMoment(BaseModel):
    """名场面"""
    type: MemeType
    start_time: float
    end_time: float
    description: str
    confidence: float


class AnalysisResult(BaseModel):
    """完整分析结果"""
    video_id: str
    duration: float  # 视频总时长（秒）
    scenes: List[Scene]
    memes: List[MemeMoment]
    overall_summary: str  # 整体剧情一句话总结
    created_at: str


class AnalysisTask(BaseModel):
    """分析任务状态"""
    task_id: str
    status: str  # pending / processing / completed / failed
    progress: int = 0  # 0-100
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
