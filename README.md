# 剧析 DramaInsight

> 上传一集短剧，在整段视频上生成可跳转的剧情节点、高光片段和本集观看建议。

![React](https://img.shields.io/badge/React-18-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Python](https://img.shields.io/badge/Python-3.11-3776AB)
![CI](https://github.com/wufeng-feng/drama-insight/actions/workflows/ci.yml/badge.svg)

## 当前 MVP

- **剧情结构化拆解**：识别开场钩子、冲突、反转、高潮和结尾钩子
- **高光片段定位**：输出高光类型、时间范围、描述和置信度
- **本集观看建议**：只评价当前视频，不预测整部剧或结局
- **播放器联动**：点击分析结果可跳转到对应视频时间点
- **反馈闭环**：用户可以标记结果“有用”或“不准”
- **可复现实验**：支持真实接口评测及 Precision / Recall / F1

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 18、TypeScript、Ant Design、Vite |
| 后端 | FastAPI、Pydantic、Uvicorn |
| AI | OpenAI 兼容的多模态模型接口 |
| 视频处理 | FFmpeg、FFprobe，全片均匀抽帧 |
| 评测 | 人工标注 JSON、一对一时间容差匹配 |

## 前置条件

- Python 3.11+
- Node.js 20+
- pnpm 11+（可通过 Corepack 启用）
- FFmpeg 和 FFprobe 已加入系统 PATH
- 一个支持图片输入的 OpenAI 兼容模型 API Key

先检查视频依赖：

```powershell
ffmpeg -version
ffprobe -version
```

## 本地启动

### 1. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `backend/.env`，填写：

```dotenv
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=your-real-api-key
LLM_MODEL=doubao-vision-pro-32k
```

启动服务：

```powershell
uvicorn app.main:app --reload --port 8000
```

访问 `http://localhost:8000/health`。当 `ffmpeg` 和 `ffprobe` 都为 `true` 时，服务状态为 `ok`。

### 2. 前端

```powershell
cd frontend
pnpm install
pnpm run dev
```

打开 `http://localhost:5173`。

## 测试与构建

```powershell
cd backend
python -m unittest discover -s tests -v
python -m compileall app

cd ..\frontend
pnpm run build
```

## 真实评测

数据文件放在 `backend/evals/dataset`。每条数据需要人工标注的 `scenes`、`memes`，以及以下两种输入之一：

- `prediction`：已经保存的模型结果
- `video_path`：相对当前 JSON 的视频路径，同时启动后端并传入 `--api-url`

运行：

```powershell
cd backend
python evals/run_eval.py --api-url http://localhost:8000
```

脚本只对真实预测输出 Precision、Recall 和 F1。仓库当前仅包含格式示例，**尚未形成可对外宣称的准确率**。

## 数据与隐私

- 上传视频仅用于本次分析
- 分析完成或失败后，原视频和抽帧图片都会删除
- 用户反馈写入本地 `backend/feedback/feedback.jsonl`
- 请只使用自有、授权或公开许可的视频素材

## 当前限制

- 当前版本仅依据画面采样分析，尚未接入 ASR，涉及台词的剧情可能判断不完整
- 任务状态保存在进程内，服务重启后会丢失；生产环境应替换为 Redis
- 本项目只做单集分析，不提供剧名搜索、整剧抓取或烂尾预测

产品范围与验收标准见 [docs/PRD.md](docs/PRD.md)。

## 项目结构

```text
drama-insight/
├── backend/
│   ├── app/              # API、模型和视频处理
│   ├── evals/            # 数据集格式与真实评测脚本
│   └── tests/            # 单元测试
├── frontend/             # React 操作界面
├── docs/PRD.md           # 精简 MVP 产品范围
└── .github/workflows/    # 持续集成
```

## 作者

马聪，计算机技术硕士，AI 产品方向

GitHub: [@wufeng-feng](https://github.com/wufeng-feng)
