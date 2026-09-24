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

export interface ViewingAdvice {
  verdict: 'recommended' | 'optional' | 'skip'
  reason: string
}

export interface AnalysisResult {
  video_id: string
  duration: number
  scenes: Scene[]
  memes: MemeMoment[]
  overall_summary: string
  viewing_advice: ViewingAdvice
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
  const response = await axios.post('/api/analyze', formData)
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await axios.get(`/api/analyze/${taskId}`)
  return response.data
}

export async function sendFeedback(input: {
  task_id: string
  item_type: 'scene' | 'meme'
  item_index: number
  helpful: boolean
  issue?: string
}): Promise<void> {
  await axios.post('/api/feedback', input)
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
  }
  return fallback
}
