import { Activity, FileText, LayoutDashboard, LogOut, ScrollText, TriangleAlert } from 'lucide-react'
import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { AssistantPanel } from './components/AssistantPanel'
import { LogsPage } from './pages/LogsPage'
import { OverviewPage } from './pages/OverviewPage'
import { ProblemsPage } from './pages/ProblemsPage'
import { ReportsPage } from './pages/ReportsPage'
import type { LogEntry, Me, Problem, Report } from './types'


type Page = 'overview' | 'logs' | 'problems' | 'reports'

export default function App() {
  const [me, setMe] = useState<Me | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [problems, setProblems] = useState<Problem[]>([])
  const [reports, setReports] = useState<Report[]>([])
  const [page, setPage] = useState<Page>('overview')
  const [loading, setLoading] = useState(true)
  const [loginError, setLoginError] = useState<string | null>(null)

  async function loadData() {
    const [meData, logData, problemData, reportData] = await Promise.all([
      api.me(),
      api.logs(),
      api.problems(),
      api.reports(),
    ])
    setMe(meData)
    setLogs(logData)
    setProblems(problemData)
    setReports(reportData)
  }

  useEffect(() => {
    loadData().catch(() => setMe(null)).finally(() => setLoading(false))
  }, [])

  async function onLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginError(null)
    const data = new FormData(event.currentTarget)
    try {
      await api.login(String(data.get('email') ?? ''), String(data.get('password') ?? ''))
      await loadData()
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Unable to sign in')
    }
  }

  async function logout() {
    await api.logout()
    setMe(null)
  }

  const nav = useMemo(() => [
    { id: 'overview' as const, label: 'Overview', icon: LayoutDashboard },
    { id: 'logs' as const, label: 'Logs', icon: ScrollText },
    { id: 'problems' as const, label: 'Problems', icon: TriangleAlert },
    { id: 'reports' as const, label: 'Reports', icon: FileText },
  ], [])

  if (loading) return <div className="fullscreen-state"><Activity className="spin" /> Loading account…</div>

  if (!me) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="brand-mark">N</div>
          <span className="eyebrow">NORTHSTAR CLOUD</span>
          <h1>Operational account console</h1>
          <p>Sign in to inspect account activity, detected problems and operational reports.</p>
          <form onSubmit={onLogin}>
            <label>Email<input name="email" type="email" defaultValue="demo@northstar.local" required /></label>
            <label>Password<input name="password" type="password" defaultValue="demo123" required /></label>
            {loginError && <div className="form-error">{loginError}</div>}
            <button type="submit" className="primary-button">Sign in</button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark small">N</div><div><strong>Northstar</strong><span>Cloud</span></div></div>
        <nav>
          {nav.map((item) => (
            <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => setPage(item.id)}>
              <item.icon size={17} /> {item.label}
              {item.id === 'problems' && problems.filter((p) => p.status !== 'resolved').length > 0 && (
                <span className="nav-count">{problems.filter((p) => p.status !== 'resolved').length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-block"><span className="avatar">ML</span><div><strong>{me.name}</strong><span>{me.email}</span></div></div>
          <button className="logout-button" onClick={() => void logout()}><LogOut size={16} /> Sign out</button>
        </div>
      </aside>

      <main className="workspace">
        <section className="content-column">
          {page === 'overview' && <OverviewPage me={me} problems={problems} />}
          {page === 'logs' && <LogsPage logs={logs} />}
          {page === 'problems' && <ProblemsPage problems={problems} />}
          {page === 'reports' && <ReportsPage reports={reports} />}
        </section>
        <AssistantPanel onActivity={() => void loadData()} />
      </main>
    </div>
  )
}
