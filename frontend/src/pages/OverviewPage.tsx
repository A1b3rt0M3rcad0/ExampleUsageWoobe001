import { Activity, AlertTriangle, CheckCircle2, Gauge, KeyRound } from 'lucide-react'
import type { Me, Problem } from '../types'

export function OverviewPage({ me, problems }: { me: Me; problems: Problem[] }) {
  const openProblems = problems.filter((problem) => problem.status !== 'resolved')
  const activeCredentials = me.account.api_credentials.filter((credential) => credential.status === 'active').length

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">ACCOUNT OVERVIEW</span>
          <h1>{me.account.name}</h1>
          <p>Operational state, usage and account-level risks.</p>
        </div>
        <span className="status-pill healthy"><CheckCircle2 size={14} /> Account active</span>
      </div>

      <div className="metric-grid">
        <section className="metric-card">
          <Gauge size={19} />
          <span>Monthly usage</span>
          <strong>{me.account.usage_percent.toFixed(1)}%</strong>
          <small>{me.account.monthly_api_calls.toLocaleString()} / {me.account.monthly_api_limit.toLocaleString()} calls</small>
        </section>
        <section className="metric-card">
          <AlertTriangle size={19} />
          <span>Active problems</span>
          <strong>{openProblems.length}</strong>
          <small>{openProblems.filter((p) => p.severity === 'high').length} high severity</small>
        </section>
        <section className="metric-card">
          <KeyRound size={19} />
          <span>Active credentials</span>
          <strong>{activeCredentials}</strong>
          <small>{me.account.api_credentials.length} total credentials</small>
        </section>
        <section className="metric-card">
          <Activity size={19} />
          <span>Plan</span>
          <strong>{me.account.plan}</strong>
          <small>Renews in {me.account.renewal_in_days} days</small>
        </section>
      </div>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">SERVICE HEALTH</span>
            <h2>Current services</h2>
          </div>
        </div>
        <div className="service-list">
          {me.account.services.map((service) => (
            <div className="service-row" key={service.name}>
              <span>{service.name}</span>
              <span className={`status-pill ${service.status === 'healthy' ? 'healthy' : 'warning'}`}>
                {service.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
