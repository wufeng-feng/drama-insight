import base64
import json
import os
from typing import Dict, List

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.models.schemas import AnalysisPayload, MemeMoment, Scene

load_dotenv()

SYSTEM_PROMPT = """你是专业的短剧内容分析助手。输入是一组按时间顺序抽取的画面，每张画面前都标有真实时间戳。

只分析画面中有明确证据的内容，不要假设未提供的台词、人物关系或剧情。没有出现的类别不要为了凑数而输出。

## 剧情节点 scenes
可识别以下类型，每类可以出现零次或多次：
- opening_hook：前30秒内吸引观众继续观看的冲突或悬念
- conflict：矛盾升级或角色进入困境
- key_twist：有画面证据支持的剧情转折
- climax：当前片段中情绪或动作的高点
- cliffhanger：结尾处留下的悬念

## 高光片段 memes
可识别以下类型：
- identity_reveal：身份揭露
- face_slap：逆袭或打脸反转
- emotional：明显的情感爆发
- action：高能动作场面
- suspense：悬念画面

## 本集观看建议 viewing_advice
只评价当前上传视频，不预测整部剧或结局：
- recommended：信息密度或高光较高，建议观看
- optional：节奏一般，可选择观看
- skip：信息密度较低，可以跳过

严格输出一个 JSON 对象，不要输出 Markdown 或解释：
{
  "overall_summary": "当前视频的一句话总结（60字内）",
  "viewing_advice": {
    "verdict": "recommended|optional|skip",
    "reason": "判断理由（80字内）"
  },
  "scenes": [
    {
      "type": "opening_hook|conflict|key_twist|climax|cliffhanger",
      "start_time": 0.0,
      "end_time": 5.0,
      "summary": "剧情摘要",
      "confidence": 0.0
    }
  ],
  "memes": [
    {
      "type": "identity_reveal|face_slap|emotional|action|suspense",
      "start_time": 0.0,
      "end_time": 5.0,
      "description": "高光描述",
      "confidence": 0.0
    }
  ]
}

要求：
- 时间戳必须依据图片前提供的秒数
- confidence 低于 0.6 的项目不要输出
- start_time 和 end_time 必须位于视频时长内
- 画面证据不足时允许 scenes 或 memes 为空数组
"""


class LLMAnalyzer:
    """调用 OpenAI 兼容的多模态接口并校验结构化结果。"""

    def __init__(self):
        api_key = os.getenv("LLM_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            raise RuntimeError("未配置 LLM_API_KEY，请先复制 .env.example 为 .env 并填写 API Key")

        client_options = {
            "api_key": api_key,
            "timeout": float(os.getenv("LLM_TIMEOUT_SECONDS", "90")),
            "max_retries": 2,
        }
        base_url = os.getenv("LLM_BASE_URL")
        if base_url:
            client_options["base_url"] = base_url

        self.client = AsyncOpenAI(**client_options)
        self.model = os.getenv("LLM_MODEL", "doubao-vision-pro-32k")
        self.json_mode = os.getenv("LLM_JSON_MODE", "true").lower() == "true"

    async def analyze(self, video_duration: float, frames: List[Dict]) -> AnalysisPayload:
        if not frames:
            raise RuntimeError("未提取到可分析的视频画面")

        user_content = [
            {
                "type": "text",
                "text": (
                    f"视频总时长为 {video_duration:.1f} 秒。"
                    f"下面提供 {len(frames)} 张覆盖整段视频的采样画面。"
                ),
            }
        ]

        for frame in frames:
            with open(frame["image_path"], "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("ascii")

            user_content.append(
                {
                    "type": "text",
                    "text": f"画面时间戳：{frame['timestamp']:.1f} 秒",
                }
            )
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "low",
                    },
                }
            )

        request = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }
        if self.json_mode:
            request["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**request)
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("模型返回了空结果")

        payload = AnalysisPayload.model_validate(self._parse_json(content))
        return self._normalize_timestamps(payload, video_duration)

    @staticmethod
    def _parse_json(content: str) -> Dict:
        text = content.strip()
        fence = chr(96) * 3
        if text.startswith(fence):
            lines = text.splitlines()
            if lines and lines[0].startswith(fence):
                lines = lines[1:]
            if lines and lines[-1].strip() == fence:
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("模型未返回合法 JSON") from exc

    @staticmethod
    def _normalize_timestamps(
        payload: AnalysisPayload,
        video_duration: float,
    ) -> AnalysisPayload:
        def normalize(items):
            normalized = []
            for item in items:
                start_time = min(max(float(item.start_time), 0.0), video_duration)
                end_time = min(max(float(item.end_time), 0.0), video_duration)
                if end_time <= start_time:
                    continue
                normalized.append(
                    item.model_copy(
                        update={
                            "start_time": round(start_time, 3),
                            "end_time": round(end_time, 3),
                        }
                    )
                )
            return sorted(normalized, key=lambda item: item.start_time)

        scenes: List[Scene] = normalize(payload.scenes)
        memes: List[MemeMoment] = normalize(payload.memes)
        return payload.model_copy(update={"scenes": scenes, "memes": memes})
