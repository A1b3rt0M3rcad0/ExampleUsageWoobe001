import { CircleAlert } from 'lucide-react'
import type { Problem } from '../types'

export function ProblemsPage({ problems }: { problems: Problem[] }) {
  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">DETECTED CONDITIONS</span>
          <h1>Problems</h1>
          <p>Correlated issues derived from system activity.</p>
        </div>
      </div>
      <div className="problem-stack">
        {problems.map((problem) => (
          <article className="surface-card problem-card" key={problem.id}>
            <div className="problem-topline">
              <div className="problem-title"><CircleAlert size={18} /><h2>{problem.title}</h2></div>
              <div className="badge-row">
                <span className={`severity ${problem.severity}`}>{problem.severity}</span>
                <span className="status-pill neutral">{problem.status}</span>
              </div>
            </div>
            <p>{problem.summary}</p>
            <div className="problem-meta"><span>{problem.service}</span><span>{problem.occurrences} occurrences</span></div>
            <div className="evidence-list">
              {problem.evidence.map((item) => <span key={item}>• {item}</span>)}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
