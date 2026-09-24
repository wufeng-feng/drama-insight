import { useState } from 'react'
import { Upload, Button, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'

interface Props {
  onUpload: (file: File) => void
  loading: boolean
}

export default function VideoUploader({ onUpload, loading }: Props) {
  const [file, setFile] = useState<File | null>(null)

  const uploadProps: UploadProps = {
    beforeUpload: (file) => {
      setFile(file)
      return false
    },
    maxCount: 1,
    accept: '.mp4,.mov,.avi,.mkv',
    showUploadList: true,
  }

  return (
    <div style={{ textAlign: 'center', padding: '40px' }}>
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />} size="large">
          选择短剧视频
        </Button>
      </Upload>
      <div style={{ marginTop: 16 }}>
        <Button
          type="primary"
          size="large"
          disabled={!file}
          loading={loading}
          onClick={() => file && onUpload(file)}
        >
          开始AI分析
        </Button>
      </div>
      <p style={{ marginTop: 16, color: '#999' }}>
        支持 MP4 / MOV / AVI，单集短剧 1-3 分钟效果最佳
      </p>
    </div>
  )
}
