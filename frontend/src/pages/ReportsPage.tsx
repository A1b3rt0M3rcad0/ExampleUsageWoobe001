import { FileText } from 'lucide-react'
import type { Report } from '../types'

export function ReportsPage({ reports }: { reports: Report[] }) {
  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">AI-GENERATED ARTIFACTS</span>
          <h1>Reports</h1>
          <p>Ask the account assistant to analyze logs and problems, then generate a report.</p>
        </div>
      </div>

      {reports.length === 0 ? (
        <section className="surface-card empty-state">
          <FileText size={28} />
          <h2>No reports yet</h2>
          <p>Try: “Analyze the current problems and create an executive report with recommendations.”</p>
        </section>
      ) : (
        <div className="report-grid">
          {reports.map((report) => (
            <article className="surface-card report-card" key={report.id}>
              <div className="report-title"><FileText size={18} /><div><h2>{report.title}</h2><span>{report.period_label}</span></div></div>
              <p>{report.executive_summary}</p>
              <h3>Findings</h3>
              <ul>{report.findings.map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>Recommendations</h3>
              <ul>{report.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
