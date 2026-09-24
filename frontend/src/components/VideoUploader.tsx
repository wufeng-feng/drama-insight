import { useState } from 'react'
import { InboxOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { Button, Upload, message } from 'antd'
import type { UploadProps } from 'antd'

interface Props {
  onUpload: (file: File) => Promise<void>
  loading: boolean
}

const MAX_VIDEO_SIZE_MB = 100
const allowedExtensions = ['mp4', 'mov', 'avi', 'mkv']

export default function VideoUploader({ onUpload, loading }: Props) {
  const [file, setFile] = useState<File | null>(null)

  const uploadProps: UploadProps = {
    beforeUpload: (selectedFile) => {
      const extension = selectedFile.name.split('.').pop()?.toLowerCase() ?? ''
      if (!allowedExtensions.includes(extension)) {
        message.error('请选择 MP4、MOV、AVI 或 MKV 视频')
        return Upload.LIST_IGNORE
      }
      if (selectedFile.size > MAX_VIDEO_SIZE_MB * 1024 * 1024) {
        message.error(`视频不能超过 ${MAX_VIDEO_SIZE_MB} MB`)
        return Upload.LIST_IGNORE
      }
      setFile(selectedFile)
      return false
    },
    onRemove: () => {
      setFile(null)
    },
    maxCount: 1,
    accept: '.mp4,.mov,.avi,.mkv',
    showUploadList: true,
  }

  return (
    <section className="upload-panel" aria-labelledby="upload-title">
      <div className="upload-copy">
        <span className="eyebrow">单集分析</span>
        <h1 id="upload-title">把短剧时间线交给 AI 先看一遍</h1>
        <p>上传一集视频，生成可跳转的剧情节点、高光片段与本集观看建议。</p>
      </div>

      <Upload.Dragger {...uploadProps} className="video-dragger">
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">拖放视频到这里，或点击选择文件</p>
        <p className="ant-upload-hint">MP4 / MOV / AVI / MKV，最大 100 MB</p>
      </Upload.Dragger>

      <Button
        type="primary"
        size="large"
        icon={<PlayCircleOutlined />}
        disabled={!file}
        loading={loading}
        onClick={() => (file ? onUpload(file) : undefined)}
        className="analyze-button"
      >
        开始 AI 分析
      </Button>
    </section>
  )
}
