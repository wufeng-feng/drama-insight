import axios from 'axios'

export interface Scene {
  type: string
  start_time: number
  end_time: number
  summary: string
  confidence: number
}

export interface MemeMoment {
  type: string
  start_time: number
  end_time: number
  description: string
  confidence: number
}

export interface AnalysisResult {
  video_id: string
  duration: number
  scenes: Scene[]
  memes: MemeMoment[]
  overall_summary: string
  created_at: string
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result?: AnalysisResult
  error?: string
}

export async function uploadVideo(file: File): Promise<{ task_id: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await axios.post('/api/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const res = await axios.get(`/api/analyze/${taskId}`)
  return res.data
}
