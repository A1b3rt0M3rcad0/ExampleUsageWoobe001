export interface ServiceHealth {
  name: string
  status: 'healthy' | 'degraded' | string
}

export interface Account {
  id: string
  name: string
  plan: string
  monthly_api_calls: number
  monthly_api_limit: number
  usage_percent: number
  renewal_in_days: number
  status: string
  services: ServiceHealth[]
  api_credentials: Array<Record<string, string>>
}

export interface Me {
  user_id: string
  account_id: string
  email: string
  name: string
  account: Account
}

export interface LogEntry {
  id: string
  occurred_at: string
  severity: string
  service: string
  event: string
  message: string
  request_id?: string
  metadata: Record<string, unknown>
}

export interface Problem {
  id: string
  status: string
  severity: string
  title: string
  service: string
  detected_at: string
  last_seen_at: string
  occurrences: number
  summary: string
  evidence: string[]
}

export interface Report {
  id: string
  title: string
  period_label: string
  executive_summary: string
  findings: string[]
  recommendations: string[]
  generated_by: string
  created_at: string
}

declare global {
  interface Window {
    WoobeChat?: {
      mount(options: {
        container: string | HTMLElement
        surfaceId: string
        sessionToken: string
        mode?: 'inline' | 'floating'
        iframeBaseUrl?: string
        apiBaseUrl?: string
        onEvent?: (event: { type: string; payload?: unknown }) => void
      }): {
        updateToken(token: string): void
        destroy(): void
      }
    }
  }
}
