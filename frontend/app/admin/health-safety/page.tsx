'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getComplianceDashboard, getComplianceItems, getTrainingList, getIncidents,
  getComplianceDocuments, completeComplianceItem,
} from '@/lib/api'

function rag(pct: number) {
  if (pct >= 80) return 'var(--color-success)'
  if (pct >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function daysUntil(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  d.setHours(0, 0, 0, 0)
  return Math.ceil((d.getTime() - now.getTime()) / 86400000)
}

export default function HealthSafetyOverview() {
  const [dash, setDash] = useState<any>(null)
  const [urgentItems, setUrgentItems] = useState<any[]>([])
  const [upcomingItems, setUpcomingItems] = useState<any[]>([])
  const [trainingCount, setTrainingCount] = useState({ total: 0, expiring: 0, expired: 0 })
  const [incidentCount, setIncidentCount] = useState({ open: 0, total: 0 })
  const [docCount, setDocCount] = useState({ total: 0, expired: 0 })
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const [d, items, tr, inc, docs] = await Promise.all([
      getComplianceDashboard(),
      getComplianceItems(),
      getTrainingList(),
      getIncidents(),
      getComplianceDocuments(),
    ])

    if (d.data) setDash(d.data)

    if (items.data) {
      const sorted = [...items.data].sort((a, b) => {
        const priority: Record<string, number> = { overdue: 0, due_soon: 1, not_started: 2, compliant: 3 }
        return (priority[a.status] ?? 9) - (priority[b.status] ?? 9)
      })
      setUrgentItems(sorted.filter(i => i.status === 'overdue').slice(0, 5))
      setUpcomingItems(sorted.filter(i => i.status === 'due_soon').slice(0, 5))
    }

    if (tr.data) {
      setTrainingCount({
        total: tr.data.length,
        expiring: tr.data.filter((t: any) => t.status === 'expiring_soon').length,
        expired: tr.data.filter((t: any) => t.status === 'expired').length,
      })
    }

    if (inc.data) {
      setIncidentCount({
        total: inc.data.length,
        open: inc.data.filter((i: any) => i.status === 'OPEN' || i.status === 'INVESTIGATING').length,
      })
    }

    if (docs.data) {
      setDocCount({
        total: docs.data.length,
        expired: docs.data.filter((d: any) => d.is_expired).length,
      })
    }

    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function handleComplete(id: number) {
    await completeComplianceItem(id)
    load()
  }

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>

  const score = dash?.score ?? 0

  return (
    <div>
      {/* === HERO: Peace of Mind Score + KPIs === */}
      <div className="hse-hero">
        <div className="hse-score-wrap">
          <div className="hse-score-ring" style={{ borderColor: rag(score), color: rag(score) }}>
            {score}%
          </div>
          <div className="hse-score-label">Peace of Mind Score</div>
        </div>

        <div className="hse-kpi-strip">
          <div className="hse-kpi">
            <div className="hse-kpi-num" style={{ color: 'var(--color-danger)' }}>{dash?.overdue ?? 0}</div>
            <div className="hse-kpi-label">Overdue</div>
          </div>
          <div className="hse-kpi">
            <div className="hse-kpi-num" style={{ color: 'var(--color-warning)' }}>{dash?.due_soon ?? 0}</div>
            <div className="hse-kpi-label">Due Soon</div>
          </div>
          <div className="hse-kpi">
            <div className="hse-kpi-num" style={{ color: 'var(--color-warning)' }}>{trainingCount.expiring + trainingCount.expired}</div>
            <div className="hse-kpi-label">Training Expiring</div>
          </div>
          <div className="hse-kpi">
            <div className="hse-kpi-num" style={{ color: incidentCount.open > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>{incidentCount.open}</div>
            <div className="hse-kpi-label">Open Incidents</div>
          </div>
        </div>
      </div>

      {/* === IMMEDIATE ACTIONS === */}
      {urgentItems.length > 0 && (
        <div className="hse-actions">
          <h2>Immediate Actions</h2>
          <div className="hse-action-list">
            {urgentItems.map(item => (
              <div key={item.id} className="hse-action-row urgent">
                <div className="hse-action-dot" style={{ background: 'var(--color-danger)' }} />
                <div className="hse-action-body">
                  <div className="hse-action-title">{item.title}</div>
                  <div className="hse-action-meta">
                    {item.category_name}
                    {item.next_due_date && <> &middot; Due {item.next_due_date} ({daysUntil(item.next_due_date)}d overdue)</>}
                    {item.legal_requirement && <> &middot; <span style={{ color: 'var(--color-danger)' }}>Legal requirement</span></>}
                  </div>
                </div>
                <button className="btn btn-sm btn-danger" onClick={() => handleComplete(item.id)}>
                  Mark Done
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* === UPCOMING === */}
      {upcomingItems.length > 0 && (
        <div className="hse-actions">
          <h2>Upcoming</h2>
          <div className="hse-action-list">
            {upcomingItems.map(item => (
              <div key={item.id} className="hse-action-row warning">
                <div className="hse-action-dot" style={{ background: 'var(--color-warning)' }} />
                <div className="hse-action-body">
                  <div className="hse-action-title">{item.title}</div>
                  <div className="hse-action-meta">
                    {item.category_name}
                    {item.next_due_date && <> &middot; Due {item.next_due_date} ({daysUntil(item.next_due_date)}d)</>}
                  </div>
                </div>
                <button className="btn btn-sm btn-primary" onClick={() => handleComplete(item.id)}>
                  Complete
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {urgentItems.length === 0 && upcomingItems.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', marginBottom: '2rem', color: 'var(--color-success)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>All clear</div>
          <div style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>No overdue or upcoming compliance items</div>
        </div>
      )}

      {/* === SUMMARY STATS (category bars) === */}
      {dash?.categories?.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Compliance by Category</h3>
          {dash.categories.map((cat: any) => (
            <div key={cat.id} className="compliance-bar">
              <span className="compliance-bar-label">
                {cat.legal_requirement && '⚖️ '}{cat.name}
              </span>
              <div className="compliance-bar-track">
                <div className="compliance-bar-fill" style={{ width: `${cat.score_pct}%`, background: rag(cat.score_pct) }} />
              </div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, width: 50, textAlign: 'right' }}>
                {cat.compliant}/{cat.total}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* === RIDDOR ALERT === */}
      {dash?.riddor_count > 0 && (
        <div className="card" style={{ background: '#fef2f2', borderLeft: '4px solid var(--color-danger)', marginBottom: '2rem' }}>
          <strong>RIDDOR:</strong> {dash.riddor_count} reportable incident(s) recorded
        </div>
      )}

      {/* === QUICK LINKS === */}
      <div className="hse-quick-links">
        <a href="/admin/health-safety/register" className="hse-quick-link">
          <span className="hse-quick-link-icon">📋</span>
          Compliance Register
          <span className="hse-quick-link-count">{dash?.total ?? 0} items</span>
        </a>
        <a href="/admin/health-safety/training" className="hse-quick-link">
          <span className="hse-quick-link-icon">🎓</span>
          Staff Training
          <span className="hse-quick-link-count">{trainingCount.total} records</span>
        </a>
        <a href="/admin/health-safety/incidents" className="hse-quick-link">
          <span className="hse-quick-link-icon">⚠️</span>
          Incidents
          <span className="hse-quick-link-count">{incidentCount.total} reported</span>
        </a>
        <a href="/admin/health-safety/documents" className="hse-quick-link">
          <span className="hse-quick-link-icon">📁</span>
          Documents
          <span className="hse-quick-link-count">{docCount.total} files</span>
        </a>
      </div>
    </div>
  )
}
