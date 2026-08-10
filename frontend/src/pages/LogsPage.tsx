import type { LogEntry } from '../types'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function LogsPage({ logs }: { logs: LogEntry[] }) {
  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">SYSTEM ACTIVITY</span>
          <h1>Logs</h1>
          <p>Recent application events available to the account assistant.</p>
        </div>
      </div>
      <section className="surface-card table-card">
        <table>
          <thead>
            <tr><th>Time</th><th>Level</th><th>Service</th><th>Event</th><th>Message</th><th>Request</th></tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="muted nowrap">{formatDate(log.occurred_at)}</td>
                <td><span className={`severity ${log.severity.toLowerCase()}`}>{log.severity}</span></td>
                <td>{log.service}</td>
                <td className="mono">{log.event}</td>
                <td>{log.message}</td>
                <td className="mono muted">{log.request_id ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
