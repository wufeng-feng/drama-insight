# 剧析 DramaInsight — AI短剧/影视内容理解助手

> 帮短剧观众快速判断"值不值得看、哪里好看、哪里可以快进"的AI内容理解工具

![tech](https://img.shields.io/badge/React-18-61DAFB) ![tech](https://img.shields.io/badge/FastAPI-0.104-009688) ![tech](https://img.shields.io/badge/Python-3.11-3776AB) ![tech](https://img.shields.io/badge/MultiModal-LLM-FF6B6B)

## 项目简介

剧析是一个AI驱动的短剧内容理解工具。用户上传短剧片段后，AI自动完成：

- **剧情结构化拆解**：开场钩子 / 冲突升级 / 关键反转 / 高潮名场面 / 结尾钩子
- **名场面智能标记**：身份揭露 / 打脸反转 / 情感爆发 / 高能动作 / 悬念钩子
- **时间线可视化**：在视频时间线上标记高光片段，点击直接跳转

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design + Vite |
| 后端 | FastAPI + Python 3.11 + Uvicorn |
| AI能力 | 多模态大模型（豆包视觉理解 / GPT-4o）+ ASR语音识别 |
| 视频处理 | FFmpeg 抽帧 |

## 快速开始

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 填入你的API Key
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可使用。

## 评测

```bash
cd backend
python evals/run_eval.py
```

当前评测集：10集短剧人工标注，名场面标记准确率约80%。

## 项目结构

```
drama-insight/
├── backend/           # FastAPI后端
│   ├── app/
│   │   ├── main.py        # 入口
│   │   ├── routes/        # API路由
│   │   ├── services/      # 业务逻辑
│   │   └── models/        # 数据模型
│   └── evals/             # 评测集与脚本
├── frontend/          # React前端
│   └── src/
│       ├── components/     # 组件
│       └── App.tsx        # 主应用
├── docs/               # 产品文档
└── README.md
```

## 产品设计

完整PRD见 [docs/PRD.md](docs/PRD.md)

## 作者

马聪 — 计算机技术硕士 · AI产品方向
GitHub: [@wufeng-feng](https://github.com/wufeng-feng)
