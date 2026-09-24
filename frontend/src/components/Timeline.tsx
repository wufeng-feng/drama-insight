import { useRef, useState } from 'react'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import { Button, Empty, Space, Tag, Timeline, message } from 'antd'

import { sendFeedback, type AnalysisResult } from '../api'

const sceneColorMap: Record<string, string> = {
  opening_hook: 'blue',
  conflict: 'orange',
  key_twist: 'purple',
  climax: 'red',
  cliffhanger: 'cyan',
}

const sceneLabelMap: Record<string, string> = {
  opening_hook: '开场钩子',
  conflict: '冲突升级',
  key_twist: '关键反转',
  climax: '高潮',
  cliffhanger: '结尾钩子',
}

const memeColorMap: Record<string, string> = {
  identity_reveal: 'gold',
  face_slap: 'volcano',
  emotional: 'magenta',
  action: 'geekblue',
  suspense: 'lime',
}

const memeLabelMap: Record<string, string> = {
  identity_reveal: '身份揭露',
  face_slap: '打脸反转',
  emotional: '情感爆发',
  action: '高能动作',
  suspense: '悬念钩子',
}

const adviceMap = {
  recommended: { label: '建议观看', color: 'green' },
  optional: { label: '选择观看', color: 'gold' },
  skip: { label: '可以跳过', color: 'default' },
} as const

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

interface FeedbackButtonsProps {
  taskId: string
  itemType: 'scene' | 'meme'
  itemIndex: number
}

function FeedbackButtons({
  taskId,
  itemType,
  itemIndex,
}: FeedbackButtonsProps) {
  const [submitted, setSubmitted] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async (helpful: boolean) => {
    setLoading(true)
    try {
      await sendFeedback({
        task_id: taskId,
        item_type: itemType,
        item_index: itemIndex,
        helpful,
        issue: helpful ? undefined : '用户标记结果不准确',
      })
      setSubmitted(helpful)
      message.success('反馈已记录')
    } catch {
      message.error('反馈提交失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Space size={4} className="feedback-actions">
      <Button
        size="small"
        type={submitted === true ? 'primary' : 'text'}
        icon={<CheckCircleOutlined />}
        loading={loading}
        disabled={submitted !== null}
        onClick={() => submit(true)}
      >
        有用
      </Button>
      <Button
        size="small"
        type={submitted === false ? 'primary' : 'text'}
        danger={submitted === false}
        icon={<CloseCircleOutlined />}
        loading={loading}
        disabled={submitted !== null}
        onClick={() => submit(false)}
      >
        不准
      </Button>
    </Space>
  )
}

interface Props {
  result: AnalysisResult
  videoUrl: string
}

export default function AnalysisResultView({ result, videoUrl }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const advice = adviceMap[result.viewing_advice.verdict]

  const seekTo = (seconds: number) => {
    const video = videoRef.current
    if (!video) {
      return
    }
    video.currentTime = Math.max(0, Math.min(seconds, result.duration))
    void video.play().catch(() => undefined)
  }

  const sceneItems = result.scenes.map((scene, index) => ({
    key: `scene-${index}`,
    color: sceneColorMap[scene.type] || 'gray',
    children: (
      <div className="timeline-entry">
        <div className="entry-heading">
          <Space size={8} wrap>
            <Tag color={sceneColorMap[scene.type]}>
              {sceneLabelMap[scene.type] || scene.type}
            </Tag>
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => seekTo(scene.start_time)}
            >
              {formatTime(scene.start_time)} - {formatTime(scene.end_time)}
            </Button>
            <span className="confidence">
              置信度 {Math.round(scene.confidence * 100)}%
            </span>
          </Space>
        </div>
        <p>{scene.summary}</p>
        <FeedbackButtons
          taskId={result.video_id}
          itemType="scene"
          itemIndex={index}
        />
      </div>
    ),
  }))

  const memeItems = result.memes.map((meme, index) => ({
    key: `meme-${index}`,
    color: memeColorMap[meme.type] || 'gray',
    children: (
      <div className="timeline-entry">
        <div className="entry-heading">
          <Space size={8} wrap>
            <Tag color={memeColorMap[meme.type]}>
              {memeLabelMap[meme.type] || meme.type}
            </Tag>
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => seekTo(meme.start_time)}
            >
              {formatTime(meme.start_time)} - {formatTime(meme.end_time)}
            </Button>
            <span className="confidence">
              置信度 {Math.round(meme.confidence * 100)}%
            </span>
          </Space>
        </div>
        <p>{meme.description}</p>
        <FeedbackButtons
          taskId={result.video_id}
          itemType="meme"
          itemIndex={index}
        />
      </div>
    ),
  }))

  return (
    <div className="result-view">
      <section className="video-workspace" aria-label="视频播放器">
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          preload="metadata"
          className="video-player"
        />
      </section>

      <section className="insight-summary" aria-labelledby="summary-title">
        <div>
          <span className="section-kicker">本集结论</span>
          <h2 id="summary-title">{result.overall_summary}</h2>
          <p>{result.viewing_advice.reason}</p>
        </div>
        <Tag color={advice.color} className="advice-tag">
          {advice.label}
        </Tag>
      </section>

      <div className="analysis-columns">
        <section className="analysis-section" aria-labelledby="scene-title">
          <div className="section-heading">
            <span className="section-kicker">结构拆解</span>
            <h2 id="scene-title">剧情时间线</h2>
          </div>
          {sceneItems.length ? (
            <Timeline items={sceneItems} />
          ) : (
            <Empty description="没有识别到可靠的剧情节点" />
          )}
        </section>

        <section className="analysis-section" aria-labelledby="meme-title">
          <div className="section-heading">
            <span className="section-kicker">高光定位</span>
            <h2 id="meme-title">高光片段</h2>
          </div>
          {memeItems.length ? (
            <Timeline items={memeItems} />
          ) : (
            <Empty description="没有识别到可靠的高光片段" />
          )}
        </section>
      </div>
    </div>
  )
}
