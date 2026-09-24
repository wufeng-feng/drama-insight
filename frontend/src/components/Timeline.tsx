import { Timeline, Tag } from 'antd'
import type { AnalysisResult } from '../api'

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

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

interface Props {
  result: AnalysisResult
}

export default function AnalysisResultView({ result }: Props) {
  return (
    <div>
      <h3>剧情结构时间线</h3>
      <Timeline
        items={result.scenes.map((scene) => ({
          color: sceneColorMap[scene.type] || 'gray',
          children: (
            <div>
              <Tag color={sceneColorMap[scene.type]}>
                {sceneLabelMap[scene.type] || scene.type}
              </Tag>
              <span style={{ marginLeft: 8, color: '#666' }}>
                {formatTime(scene.start_time)} - {formatTime(scene.end_time)}
              </span>
              <p style={{ marginTop: 4 }}>{scene.summary}</p>
            </div>
          ),
        }))}
      />

      <h3 style={{ marginTop: 24 }}>名场面标记</h3>
      <Timeline
        items={result.memes.map((meme) => ({
          color: memeColorMap[meme.type] || 'gray',
          children: (
            <div>
              <Tag color={memeColorMap[meme.type]}>
                {memeLabelMap[meme.type] || meme.type}
              </Tag>
              <span style={{ marginLeft: 8, color: '#666' }}>
                {formatTime(meme.start_time)} - {formatTime(meme.end_time)}
              </span>
              <p style={{ marginTop: 4 }}>{meme.description}</p>
            </div>
          ),
        }))}
      />

      <div style={{ marginTop: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
        <strong>一句话总结：</strong>{result.overall_summary}
      </div>
    </div>
  )
}
