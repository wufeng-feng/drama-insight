import { useState } from 'react'
import { Layout, Typography, Progress, Card, Spin } from 'antd'
import VideoUploader from './components/VideoUploader'
import AnalysisResultView from './components/Timeline'
import { uploadVideo, getTaskStatus, type AnalysisResult } from './api'

const { Header, Content } = Layout
const { Title } = Typography

export default function App() {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [polling, setPolling] = useState(false)

  const handleUpload = async (file: File) => {
    setLoading(true)
    setResult(null)
    setProgress(0)
    try {
      const { task_id } = await uploadVideo(file)
      setPolling(true)

      // 轮询任务状态
      const timer = setInterval(async () => {
        try {
          const status = await getTaskStatus(task_id)
          setProgress(status.progress)

          if (status.status === 'completed' && status.result) {
            setResult(status.result)
            setLoading(false)
            setPolling(false)
            clearInterval(timer)
          } else if (status.status === 'failed') {
            setLoading(false)
            setPolling(false)
            clearInterval(timer)
            alert(`分析失败: ${status.error}`)
          }
        } catch (e) {
          console.error(e)
        }
      }, 2000)
    } catch (e: any) {
      setLoading(false)
      alert('上传失败，请重试')
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', borderBottom: '1px solid #eee' }}>
        <Title level={3} style={{ margin: '16px 0' }}>
          剧析 · AI短剧内容理解
        </Title>
      </Header>
      <Content style={{ padding: '24px', maxWidth: 900, margin: '0 auto', width: '100%' }}>
        {!result && !polling && (
          <Card>
            <VideoUploader onUpload={handleUpload} loading={loading} />
          </Card>
        )}

        {polling && (
          <Card>
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" />
              <Progress
                percent={progress}
                status="active"
                style={{ maxWidth: 400, margin: '24px auto' }}
              />
              <p style={{ color: '#666' }}>AI正在分析剧情，请稍候...</p>
            </div>
          </Card>
        )}

        {result && !polling && (
          <Card>
            <AnalysisResultView result={result} />
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <a
                onClick={() => {
                  setResult(null)
                  setProgress(0)
                }}
              >
                分析下一部
              </a>
            </div>
          </Card>
        )}
      </Content>
    </Layout>
  )
}
