import { useEffect, useRef, useState } from 'react'
import {
  FileSearchOutlined,
  LoadingOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { Alert, Button, Layout, Progress, Spin } from 'antd'

import {
  getApiErrorMessage,
  getTaskStatus,
  uploadVideo,
  type AnalysisResult,
} from './api'
import AnalysisResultView from './components/Timeline'
import VideoUploader from './components/VideoUploader'

const { Header, Content } = Layout
const MAX_POLL_ATTEMPTS = 90

export default function App() {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState('')
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const videoUrlRef = useRef('')

  const clearPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }

  const releaseVideoUrl = () => {
    if (videoUrlRef.current) {
      URL.revokeObjectURL(videoUrlRef.current)
      videoUrlRef.current = ''
    }
    setVideoUrl('')
  }

  useEffect(() => {
    return () => {
      clearPolling()
      if (videoUrlRef.current) {
        URL.revokeObjectURL(videoUrlRef.current)
      }
    }
  }, [])

  const pollTask = async (taskId: string, attempt = 0): Promise<void> => {
    if (attempt >= MAX_POLL_ATTEMPTS) {
      setLoading(false)
      setError('分析等待超时，请检查后端日志后重试')
      return
    }

    try {
      const task = await getTaskStatus(taskId)
      setProgress(task.progress)

      if (task.status === 'completed' && task.result) {
        setResult(task.result)
        setLoading(false)
        return
      }

      if (task.status === 'failed') {
        setLoading(false)
        setError(task.error || '分析失败，请重试')
        return
      }
    } catch (requestError) {
      if (attempt >= 2) {
        setLoading(false)
        setError(getApiErrorMessage(requestError, '无法查询分析状态，请确认后端已启动'))
        return
      }
    }

    pollTimerRef.current = setTimeout(() => {
      void pollTask(taskId, attempt + 1)
    }, 2000)
  }

  const handleUpload = async (file: File) => {
    clearPolling()
    releaseVideoUrl()

    const objectUrl = URL.createObjectURL(file)
    videoUrlRef.current = objectUrl
    setVideoUrl(objectUrl)
    setLoading(true)
    setResult(null)
    setError(null)
    setProgress(0)

    try {
      const { task_id: taskId } = await uploadVideo(file)
      await pollTask(taskId)
    } catch (uploadError) {
      setLoading(false)
      setError(getApiErrorMessage(uploadError, '上传失败，请确认后端已启动后重试'))
    }
  }

  const reset = () => {
    clearPolling()
    releaseVideoUrl()
    setResult(null)
    setError(null)
    setProgress(0)
  }

  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <FileSearchOutlined />
          </span>
          <div>
            <strong>剧析</strong>
            <span>DramaInsight</span>
          </div>
        </div>
        <span className="product-mode">单集分析 MVP</span>
      </Header>

      <Content className="app-content">
        {error && (
          <Alert
            type="error"
            showIcon
            closable
            message="本次分析未完成"
            description={error}
            onClose={() => setError(null)}
            className="status-alert"
          />
        )}

        {!result && !loading && (
          <div className="surface">
            <VideoUploader onUpload={handleUpload} loading={loading} />
          </div>
        )}

        {loading && (
          <section className="surface processing-panel" aria-live="polite">
            <Spin indicator={<LoadingOutlined spin />} size="large" />
            <div className="processing-copy">
              <span className="eyebrow">分析任务进行中</span>
              <h1>正在定位剧情节点与高光片段</h1>
              <p>系统正在覆盖整段视频抽帧，并校验模型返回的时间戳。</p>
            </div>
            <Progress
              percent={progress}
              status="active"
              strokeColor="#087f5b"
              className="processing-progress"
            />
          </section>
        )}

        {result && !loading && videoUrl && (
          <>
            <div className="surface">
              <AnalysisResultView result={result} videoUrl={videoUrl} />
            </div>
            <div className="page-actions">
              <Button icon={<ReloadOutlined />} onClick={reset}>
                分析下一集
              </Button>
            </div>
          </>
        )}
      </Content>
    </Layout>
  )
}
