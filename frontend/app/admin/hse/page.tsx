'use client'

import { useState } from 'react'
import { DEMO_COMPLIANCE_SCORE, DEMO_HAZARD_FINDINGS, DEMO_RISK_ASSESSMENTS, DEMO_EQUIPMENT, DEMO_INCIDENTS, DEMO_RAMS } from '@/lib/demo-data'

export default function AdminHSEPage() {
  const [tab, setTab] = useState<'dashboard' | 'assessments' | 'findings' | 'equipment' | 'incidents' | 'rams'>('dashboard')
  const score = DEMO_COMPLIANCE_SCORE

  function scoreColor(pct: number) {
    if (pct >= 80) return 'var(--color-success)'
    if (pct >= 60) return 'var(--color-warning)'
    return 'var(--color-danger)'
  }

  return (
    <div>
      <div className="page-header"><h1>Health &amp; Safety</h1><span className="badge badge-danger">Tier 3 — Full Access</span></div>
      <div className="tabs">
        {(['dashboard', 'assessments', 'findings', 'equipment', 'incidents', 'rams'] as const).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'rams' ? 'RAMS' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'dashboard' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '2rem', marginBottom: '2rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div className="score-circle" style={{ borderColor: scoreColor(score.overall), margin: '0 auto', color: scoreColor(score.overall) }}>{score.overall}%</div>
              <div style={{ marginTop: '0.5rem', fontWeight: 600 }}>Overall Score</div>
            </div>
            <div>
              {score.categories.map(cat => (
                <div key={cat.name} className="compliance-bar">
                  <span className="compliance-bar-label">{cat.name}</span>
                  <div className="compliance-bar-track">
                    <div className="compliance-bar-fill" style={{ width: `${(cat.score / cat.max) * 100}%`, background: scoreColor((cat.score / cat.max) * 100) }} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, width: 40, textAlign: 'right' }}>{cat.score}/{cat.max}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="stats-grid">
            <div className="stat-card"><div className="stat-number" style={{ color: 'var(--color-danger)' }}>{score.overdue_actions}</div><div className="stat-label">Overdue Actions</div></div>
            <div className="stat-card"><div className="stat-number" style={{ color: 'var(--color-warning)' }}>{score.upcoming_reviews}</div><div className="stat-label">Upcoming Reviews</div></div>
            <div className="stat-card"><div className="stat-number">{DEMO_HAZARD_FINDINGS.filter(f => f.status === 'OPEN').length}</div><div className="stat-label">Open Findings</div></div>
            <div className="stat-card"><div className="stat-number">{DEMO_INCIDENTS.filter(i => i.status !== 'RESOLVED').length}</div><div className="stat-label">Open Incidents</div></div>
          </div>
        </div>
      )}

      {tab === 'assessments' && (
        <div className="table-wrap"><table>
          <thead><tr><th>Title</th><th>Area</th><th>Assessor</th><th>Date</th><th>Review</th><th>Findings</th><th>Status</th></tr></thead>
          <tbody>{DEMO_RISK_ASSESSMENTS.map(ra => (
            <tr key={ra.id}><td style={{ fontWeight: 600 }}>{ra.title}</td><td>{ra.site_area}</td><td>{ra.assessor}</td><td>{ra.assessment_date}</td><td>{ra.review_date}</td><td>{ra.findings_count} ({ra.high_risks} high)</td><td><span className={`badge ${ra.status === 'CURRENT' ? 'badge-success' : 'badge-warning'}`}>{ra.status}</span></td></tr>
          ))}</tbody>
        </table></div>
      )}

      {tab === 'findings' && (
        <div className="table-wrap"><table>
          <thead><tr><th>Category</th><th>Description</th><th>Severity</th><th>Confidence</th><th>Ref</th><th>Controls</th><th>Status</th></tr></thead>
          <tbody>{DEMO_HAZARD_FINDINGS.map(f => (
            <tr key={f.id}><td style={{ fontWeight: 600 }}>{f.category}</td><td style={{ maxWidth: 250 }}>{f.description}</td><td><span className={`badge ${f.severity === 'HIGH' || f.severity === 'CRITICAL' ? 'badge-danger' : f.severity === 'MEDIUM' ? 'badge-warning' : 'badge-info'}`}>{f.severity}</span></td><td>{Math.round(f.confidence * 100)}%</td><td style={{ fontSize: '0.8rem' }}>{f.regulatory_ref}</td><td style={{ fontSize: '0.8rem', maxWidth: 200 }}>{f.control_measures.join('; ')}</td><td><span className={`badge ${f.status === 'RESOLVED' ? 'badge-success' : f.status === 'IN_PROGRESS' ? 'badge-warning' : 'badge-danger'}`}>{f.status}</span></td></tr>
          ))}</tbody>
        </table></div>
      )}

      {tab === 'equipment' && (
        <div className="table-wrap"><table>
          <thead><tr><th>Equipment</th><th>Location</th><th>Category</th><th>Last Inspection</th><th>Next Inspection</th><th>Status</th></tr></thead>
          <tbody>{DEMO_EQUIPMENT.map(eq => (
            <tr key={eq.id}><td style={{ fontWeight: 600 }}>{eq.name}</td><td>{eq.location}</td><td>{eq.category}</td><td>{eq.last_inspection}</td><td>{eq.next_inspection}</td><td><span className={`badge ${eq.status === 'OK' ? 'badge-success' : eq.status === 'DUE_SOON' ? 'badge-warning' : 'badge-danger'}`}>{eq.status}</span></td></tr>
          ))}</tbody>
        </table></div>
      )}

      {tab === 'incidents' && (
        <div className="table-wrap"><table>
          <thead><tr><th>Title</th><th>Severity</th><th>Reported By</th><th>Date</th><th>Description</th><th>Status</th></tr></thead>
          <tbody>{DEMO_INCIDENTS.map(inc => (
            <tr key={inc.id}><td style={{ fontWeight: 600 }}>{inc.title}</td><td><span className={`badge ${inc.severity === 'HIGH' || inc.severity === 'CRITICAL' ? 'badge-danger' : inc.severity === 'MEDIUM' ? 'badge-warning' : 'badge-info'}`}>{inc.severity}</span></td><td>{inc.reported_by}</td><td>{new Date(inc.reported_at).toLocaleDateString()}</td><td style={{ maxWidth: 300, fontSize: '0.85rem' }}>{inc.description}</td><td><span className={`badge ${inc.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}`}>{inc.status}</span></td></tr>
          ))}</tbody>
        </table></div>
      )}

      {tab === 'rams' && (
        <div className="table-wrap"><table>
          <thead><tr><th>Title</th><th>Version</th><th>Created By</th><th>Approved By</th><th>Status</th></tr></thead>
          <tbody>{DEMO_RAMS.map(r => (
            <tr key={r.id}><td style={{ fontWeight: 600 }}>{r.title}</td><td>v{r.version}</td><td>{r.created_by}</td><td>{r.approved_by || '—'}</td><td><span className={`badge ${r.status === 'APPROVED' ? 'badge-success' : 'badge-warning'}`}>{r.status}</span></td></tr>
          ))}</tbody>
        </table></div>
      )}
    </div>
  )
}
