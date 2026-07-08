import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ── Types ────────────────────────────────────────────────────────────

export interface Session {
  id: string
  company_name: string
  website: string
  objective: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  current_node: string
  error_message: string
  report_markdown: string
  report_json: string
  retry_count: number
  quality_score: number
  created_at: string
  updated_at: string
}

export interface SessionListItem {
  id: string
  company_name: string
  website: string
  objective: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  quality_score: number
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface CreateSessionPayload {
  company_name: string
  website: string
  objective: string
}

// ── Sessions API ─────────────────────────────────────────────────────

export const sessionsApi = {
  list: () => api.get<SessionListItem[]>('/sessions').then(r => r.data),
  get: (id: string) => api.get<Session>(`/sessions/${id}`).then(r => r.data),
  create: (payload: CreateSessionPayload) =>
    api.post<Session>('/sessions', payload).then(r => r.data),
  delete: (id: string) => api.delete(`/sessions/${id}`),
}

// ── Chat API ─────────────────────────────────────────────────────────

export const chatApi = {
  getHistory: (sessionId: string) =>
    api.get<ChatMessage[]>(`/sessions/${sessionId}/chat`).then(r => r.data),
  sendMessage: (sessionId: string, message: string) =>
    api.post<ChatMessage>(`/sessions/${sessionId}/chat`, { message }).then(r => r.data),
}

// ── SSE stream URL ───────────────────────────────────────────────────

export const getStreamUrl = (sessionId: string) =>
  `${import.meta.env.VITE_API_URL || '/api'}/sessions/${sessionId}/stream`

export default api
