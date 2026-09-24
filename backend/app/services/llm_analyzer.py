import os
import base64
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """你是一个专业的短剧内容分析专家。你擅长分析短剧视频的剧情结构和名场面。

请你根据提供的短剧视频帧，分析以下内容：

## 1. 剧情节点（scenes）
请识别视频中的5类剧情节点，每类可能出现多次：
- opening_hook（开场钩子）：前30秒内吸引观众看下去的冲突或悬念
- conflict（冲突升级）：矛盾激化，主角陷入困境
- key_twist（关键反转）：出乎意料的剧情转折
- climax（高潮名场面）：情绪最高点，爽点或虐点
- cliffhanger（结尾钩子）：最后10秒留悬念

## 2. 名场面（memes）
请识别视频中的高光片段，分为5类：
- identity_reveal（身份揭露）：主角真实身份曝光
- face_slap（打脸反转）：被看不起的人逆袭
- emotional（情感爆发）：强烈情绪宣泄，哭戏/对峙/告白
- action（高能动作）：视觉冲击强的动作场面
- suspense（悬念钩子）：结尾留大悬念

## 输出要求
请严格输出JSON格式，不要有任何额外解释：
{
  "overall_summary": "一句话总结这段剧情（30字内）",
  "scenes": [
    {
      "type": "opening_hook|conflict|key_twist|climax|cliffhanger",
      "start_time": 起始秒数,
      "end_time": 结束秒数,
      "summary": "剧情摘要（50字内）",
      "confidence": 0.0到1.0
    }
  ],
  "memes": [
    {
      "type": "identity_reveal|face_slap|emotional|action|suspense",
      "start_time": 起始秒数,
      "end_time": 结束秒数,
      "description": "名场面描述（30字内）",
      "confidence": 0.0到1.0
    }
  ]
}

注意：
- 时间戳要准确，基于视频实际时间
- 不要编造不存在的剧情
- confidence低于0.6的不要输出
- 如果某类没有出现，对应数组留空"""


class LLMAnalyzer:
    """多模态大模型分析服务"""

    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        self.model = os.getenv("LLM_MODEL", "doubao-vision-pro-32k")

    async def analyze(self, video_duration: float, frames: List[Dict]) -> Dict:
        """
        分析短剧视频，返回剧情节点和名场面
        MVP版本：把帧图片转base64发给多模态模型
        """
        # 构建用户消息：包含时长信息和帧图片
        user_content = [
            {
                "type": "text",
                "text": f"这是一段{video_duration:.0f}秒的短剧片段，请按要求分析剧情节点和名场面。"
            }
        ]

        # 最多取20帧，避免token超限
        sample_frames = frames[:20] if len(frames) > 20 else frames

        for frame in sample_frames:
            with open(frame["image_path"], "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"
                }
            })

        # 调用多模态模型
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        # 解析结果
        import json
        result = json.loads(response.choices[0].message.content)
        return result
