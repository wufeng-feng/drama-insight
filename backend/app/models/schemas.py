from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class SceneType(str, Enum):
    """剧情节点类型。"""

    HOOK = "opening_hook"
    CONFLICT = "conflict"
    TWIST = "key_twist"
    CLIMAX = "climax"
    CLIFFHANGER = "cliffhanger"


class MemeType(str, Enum):
    """高光片段类型。"""

    IDENTITY_REVEAL = "identity_reveal"
    FACE_SLAP = "face_slap"
    EMOTIONAL = "emotional"
    ACTION = "action"
    SUSPENSE = "suspense"


class TimedItem(BaseModel):
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time 必须大于 start_time")
        return self


class Scene(TimedItem):
    """剧情节点。"""

    type: SceneType
    summary: str = Field(min_length=1, max_length=100)


class MemeMoment(TimedItem):
    """高光片段。"""

    type: MemeType
    description: str = Field(min_length=1, max_length=100)


class ViewingAdvice(BaseModel):
    """只针对当前上传单集的观看建议。"""

    verdict: Literal["recommended", "optional", "skip"]
    reason: str = Field(min_length=1, max_length=120)


class AnalysisPayload(BaseModel):
    """模型返回并完成校验后的分析内容。"""

    scenes: List[Scene] = Field(default_factory=list)
    memes: List[MemeMoment] = Field(default_factory=list)
    overall_summary: str = Field(min_length=1, max_length=120)
    viewing_advice: ViewingAdvice


class AnalysisResult(AnalysisPayload):
    """完整分析结果。"""

    video_id: str
    duration: float = Field(gt=0)
    created_at: str


class AnalysisTask(BaseModel):
    """分析任务状态。"""

    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    task_id: str
    status: Literal["pending"] = "pending"


class FeedbackRequest(BaseModel):
    task_id: str
    item_type: Literal["scene", "meme"]
    item_index: int = Field(ge=0)
    helpful: bool
    issue: Optional[str] = Field(default=None, max_length=200)


class FeedbackResponse(BaseModel):
    feedback_id: str
    created_at: str
