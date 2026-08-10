import { Bot, LoaderCircle, RefreshCw } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

const EMBED_SCRIPT_URL =
  import.meta.env.VITE_WOOBE_EMBED_SCRIPT_URL ?? 'http://localhost:8081/chat/v1/embed.js'
const EMBED_BASE_URL = import.meta.env.VITE_WOOBE_IFRAME_BASE_URL ?? 'http://localhost:8081/chat/v1'
const WOOBE_API_BASE_URL = import.meta.env.VITE_WOOBE_API_BASE_URL ?? 'http://localhost:8000'

let loaderPromise: Promise<void> | null = null

function loadWoobeLoader(): Promise<void> {
  if (window.WoobeChat) return Promise.resolve()
  if (loaderPromise) return loaderPromise

  loaderPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-woobe-loader="true"]')
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener('error', () => reject(new Error('Unable to load assistant UI')), { once: true })
      return
    }
    const script = document.createElement('script')
    script.src = EMBED_SCRIPT_URL
    script.async = true
    script.dataset.woobeLoader = 'true'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Unable to load assistant UI'))
    document.head.appendChild(script)
  })

  return loaderPromise
}

export function AssistantPanel({ onActivity }: { onActivity?: () => void }) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const instanceRef = useRef<{ updateToken(token: string): void; destroy(): void } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  async function refreshToken() {
    setRefreshing(true)
    try {
      const token = await api.chatToken()
      instanceRef.current?.updateToken(token.session_token)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to refresh assistant access')
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    let cancelled = false

    async function mount() {
      try {
        await api.initializeChat()
        const token = await api.chatToken()
        await loadWoobeLoader()
        if (cancelled || !containerRef.current || !window.WoobeChat) return

        instanceRef.current = window.WoobeChat.mount({
          container: containerRef.current,
          surfaceId: token.surface_id,
          sessionToken: token.session_token,
          iframeBaseUrl: EMBED_BASE_URL,
          apiBaseUrl: WOOBE_API_BASE_URL,
          mode: 'inline',
          onEvent(event) {
            if (event.type === 'session.expired') void refreshToken()
            if (event.type === 'run.completed') onActivity?.()
          },
        })
        setLoading(false)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unable to initialize assistant')
          setLoading(false)
        }
      }
    }

    void mount()
    return () => {
      cancelled = true
      instanceRef.current?.destroy()
      instanceRef.current = null
    }
  }, [])

  return (
    <aside className="assistant-panel">
      <div className="assistant-header">
        <div>
          <span className="eyebrow">ACCOUNT ASSISTANT</span>
          <div className="assistant-title"><Bot size={18} /> Ask about your system</div>
        </div>
        <button className="icon-button" onClick={() => void refreshToken()} aria-label="Refresh assistant access">
          <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
        </button>
      </div>
      <div className="assistant-body">
        {loading && (
          <div className="assistant-state"><LoaderCircle className="spin" size={20} /> Connecting to your assistant…</div>
        )}
        {error && <div className="assistant-error">{error}</div>}
        <div ref={containerRef} className="chat-container" />
      </div>
    </aside>
  )
}
