import type { LogEntry, Me, Problem, Report } from './types'

const API_BASE = import.meta.env.VITE_APP_API_BASE_URL ?? 'http://localhost:8001'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // keep fallback
    }
    throw new Error(detail)
  }
  return response.json() as Promise<T>
}

export const api = {
  login(email: string, password: string) {
    return request<{ success: boolean }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },
  logout() {
    return request<{ success: boolean }>('/api/auth/logout', { method: 'POST' })
  },
  me() {
    return request<Me>('/api/me')
  },
  logs() {
    return request<LogEntry[]>('/api/logs')
  },
  problems() {
    return request<Problem[]>('/api/problems')
  },
  reports() {
    return request<Report[]>('/api/reports')
  },
  initializeChat() {
    return request<{ binding_id: string; session_id: string; target_release_id?: string; surface_id: string }>(
      '/api/chat/session',
      { method: 'POST' },
    )
  },
  chatToken() {
    return request<{
      surface_id: string
      session_id: string
      target_release_id?: string
      session_token: string
      expires_in: number
    }>('/api/chat/session/token', { method: 'POST' })
  },
}
