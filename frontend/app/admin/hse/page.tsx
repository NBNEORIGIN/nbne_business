'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getComplianceDashboard, getComplianceItems, getComplianceCalendar,
  getIncidents, getRams, getTrainingList, getComplianceDocuments,
  getComplianceActionLogs, completeComplianceItem, createIncident,
} from '@/lib/api'

type Tab = 'dashboard' | 'register' | 'training' | 'documents' | 'incidents' | 'calendar' | 'rams' | 'logs'

function rag(pct: number) {
  if (pct >= 80) return 'var(--color-success)'
  if (pct >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    compliant: 'badge-success', due_soon: 'badge-warning', overdue: 'badge-danger',
    not_started: 'badge-info', valid: 'badge-success', expiring_soon: 'badge-warning',
    expired: 'badge-danger', OPEN: 'badge-danger', INVESTIGATING: 'badge-warning',
    RESOLVED: 'badge-success', CLOSED: 'badge-info', DRAFT: 'badge-info',
    ACTIVE: 'badge-success', EXPIRED: 'badge-danger', ARCHIVED: 'badge-info',
  }
  return map[s] || 'badge-info'
}

export default function AdminHSEPage() {
  const [tab, setTab] = useState<Tab>('dashboard')
  const [dash, setDash] = useState<any>(null)
  const [items, setItems] = useState<any[]>([])
  const [incidents, setIncidents] = useState<any[]>([])
  const [rams, setRams] = useState<any[]>([])
  const [training, setTraining] = useState<any[]>([])
  const [docs, setDocs] = useState<any[]>([])
  const [calendar, setCalendar] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showIncidentForm, setShowIncidentForm] = useState(false)
  const [itemFilter, setItemFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [d, it, inc, r, tr, doc, cal, lg] = await Promise.all([
        getComplianceDashboard(),
        getComplianceItems(),
        getIncidents(),
        getRams(),
        getTrainingList(),
        getComplianceDocuments(),
        getComplianceCalendar(90),
        getComplianceActionLogs({ limit: 30 }),
      ])
      if (d.data) setDash(d.data)
      if (it.data) setItems(it.data)
      if (inc.data) setIncidents(inc.data)
      if (r.data) setRams(r.data)
      if (tr.data) setTraining(tr.data)
      if (doc.data) setDocs(doc.data)
      if (cal.data?.events) setCalendar(cal.data.events)
      if (lg.data) setLogs(lg.data)
      if (d.error) setError(d.error)
    } catch (e: any) {
      setError(e.message || 'Failed to load')
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function handleComplete(id: number) {
    await completeComplianceItem(id)
    load()
  }

  async function handleCreateIncident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const data = {
      title: fd.get('title'),
      description: fd.get('description'),
      severity: fd.get('severity'),
      location: fd.get('location'),
      incident_date: new Date().toISOString(),
      injury_type: fd.get('injury_type') || 'none',
      riddor_reportable: fd.get('riddor') === 'on',
    }
    const res = await createIncident(data)
    if (res.data) {
      setShowIncidentForm(false)
      load()
    }
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'register', label: 'Register' },
    { key: 'training', label: 'Training' },
    { key: 'documents', label: 'Documents' },
    { key: 'incidents', label: 'Incidents' },
    { key: 'calendar', label: 'Calendar' },
    { key: 'rams', label: 'RAMS' },
    { key: 'logs', label: 'Audit Log' },
  ]

  const filteredItems = itemFilter ? items.filter(i => i.status === itemFilter) : items

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading H&amp;S data...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Health &amp; Safety</h1>
        <span className="badge badge-danger">Tier 3 — Full Access</span>
      </div>

      {error && <div className="card" style={{ background: '#fef2f2', color: '#991b1b', marginBottom: '1rem' }}>{error}</div>}

      <div className="tabs" style={{ overflowX: 'auto' }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ===== DASHBOARD ===== */}
      {tab === 'dashboard' && dash && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: '2rem', marginBottom: '2rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div className="score-circle" style={{ borderColor: rag(dash.score), margin: '0 auto', color: rag(dash.score) }}>
                {dash.score}%
              </div>
              <div style={{ marginTop: '0.5rem', fontWeight: 600, fontSize: '0.9rem' }}>Compliance Score</div>
            </div>
            <div>
              {(dash.categories || []).map((cat: any) => (
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
              {(!dash.categories || dash.categories.length === 0) && (
                <div style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                  No compliance categories yet. Run baseline seed to populate.
                </div>
              )}
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number" style={{ color: 'var(--color-danger)' }}>{dash.overdue}</div>
              <div className="stat-label">Overdue</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: 'var(--color-warning)' }}>{dash.due_soon}</div>
              <div className="stat-label">Due Soon</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{dash.compliant}</div>
              <div className="stat-label">Compliant</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{dash.not_started}</div>
              <div className="stat-label">Not Started</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: 'var(--color-danger)' }}>{dash.open_incidents}</div>
              <div className="stat-label">Open Incidents</div>
            </div>
            <div className="stat-card">
              <div className="stat-number" style={{ color: 'var(--color-warning)' }}>{dash.expired_training}</div>
              <div className="stat-label">Expired Training</div>
            </div>
          </div>

          {dash.riddor_count > 0 && (
            <div className="card" style={{ background: '#fef2f2', borderLeft: '4px solid var(--color-danger)', marginTop: '1rem' }}>
              <strong>RIDDOR:</strong> {dash.riddor_count} reportable incident(s) recorded
            </div>
          )}
        </div>
      )}

      {/* ===== COMPLIANCE REGISTER ===== */}
      {tab === 'register' && (
        <div>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            {['', 'overdue', 'due_soon', 'compliant', 'not_started'].map(f => (
              <button key={f} className={`btn btn-sm ${itemFilter === f ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setItemFilter(f)}>
                {f ? f.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'All'}
              </button>
            ))}
            <a href="/api/compliance/export/" target="_blank" className="btn btn-sm btn-ghost" style={{ marginLeft: 'auto' }}>
              Export CSV
            </a>
          </div>
          {filteredItems.length === 0 ? (
            <div className="empty-state">No compliance items found</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Item</th><th>Category</th><th>Frequency</th><th>Last Done</th><th>Next Due</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>{filteredItems.map(item => (
                <tr key={item.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{item.title}</div>
                    {item.legal_requirement && <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)' }}>⚖️ Legal</span>}
                  </td>
                  <td>{item.category_name}</td>
                  <td style={{ fontSize: '0.85rem' }}>{item.frequency_type.replace('_', ' ')}</td>
                  <td style={{ fontSize: '0.85rem' }}>{item.last_completed_date || '—'}</td>
                  <td style={{ fontSize: '0.85rem' }}>{item.next_due_date || '—'}</td>
                  <td><span className={`badge ${statusBadge(item.status)}`}>{item.status.replace('_', ' ')}</span></td>
                  <td>
                    {item.status !== 'compliant' && (
                      <button className="btn btn-sm btn-primary" onClick={() => handleComplete(item.id)}>Complete</button>
                    )}
                  </td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ===== TRAINING ===== */}
      {tab === 'training' && (
        <div>
          {training.length === 0 ? (
            <div className="empty-state">No training records yet</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Staff Member</th><th>Training Type</th><th>Provider</th><th>Issue Date</th><th>Expiry Date</th><th>Status</th></tr></thead>
              <tbody>{training.map(tr => (
                <tr key={tr.id}>
                  <td style={{ fontWeight: 600 }}>{tr.user_name}</td>
                  <td>{tr.training_type.replace('_', ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</td>
                  <td>{tr.provider || '—'}</td>
                  <td>{tr.issue_date}</td>
                  <td>{tr.expiry_date || 'N/A'}</td>
                  <td><span className={`badge ${statusBadge(tr.status)}`}>{tr.status.replace('_', ' ')}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ===== DOCUMENTS ===== */}
      {tab === 'documents' && (
        <div>
          {docs.length === 0 ? (
            <div className="empty-state">No documents uploaded yet</div>
          ) : (
            <div className="doc-grid">
              {docs.map(doc => (
                <div key={doc.id} className="card doc-card">
                  <h3>{doc.title}</h3>
                  <div className="doc-meta">
                    <span className={`badge ${statusBadge(doc.is_expired ? 'expired' : 'valid')}`}>
                      {doc.is_expired ? 'Expired' : 'Current'}
                    </span>
                    <span className="badge badge-info">v{doc.version}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      {doc.document_type.replace('_', ' ')}
                    </span>
                  </div>
                  {doc.expiry_date && (
                    <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: 'var(--color-text-muted)' }}>
                      Expires: {doc.expiry_date}
                    </div>
                  )}
                  {doc.uploaded_by_name && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      Uploaded by {doc.uploaded_by_name}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===== INCIDENTS ===== */}
      {tab === 'incidents' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowIncidentForm(!showIncidentForm)}>
              {showIncidentForm ? 'Cancel' : '+ Report Incident'}
            </button>
          </div>

          {showIncidentForm && (
            <form onSubmit={handleCreateIncident} className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Report New Incident</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Title *</label>
                  <input name="title" required className="input" placeholder="Brief description" />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Location</label>
                  <input name="location" className="input" placeholder="Where it happened" />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Severity</label>
                  <select name="severity" className="input">
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Injury Type</label>
                  <select name="injury_type" className="input">
                    <option value="none">No Injury</option>
                    <option value="minor">Minor Injury</option>
                    <option value="major">Major Injury</option>
                    <option value="dangerous_occurrence">Dangerous Occurrence</option>
                  </select>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Description *</label>
                  <textarea name="description" required className="input" rows={3} placeholder="Full details of what happened" />
                </div>
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <input type="checkbox" name="riddor" /> RIDDOR Reportable
                  </label>
                </div>
              </div>
              <div style={{ marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Submit Report</button>
              </div>
            </form>
          )}

          {incidents.length === 0 ? (
            <div className="empty-state">No incidents reported</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Title</th><th>Severity</th><th>Injury</th><th>RIDDOR</th><th>Reported By</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>{incidents.map(inc => (
                <tr key={inc.id}>
                  <td style={{ fontWeight: 600 }}>{inc.title}</td>
                  <td><span className={`badge ${statusBadge(inc.severity)}`}>{inc.severity}</span></td>
                  <td style={{ fontSize: '0.85rem' }}>{inc.injury_type?.replace('_', ' ') || '—'}</td>
                  <td>{inc.riddor_reportable ? '⚠️ Yes' : 'No'}</td>
                  <td>{inc.reported_by_name || '—'}</td>
                  <td style={{ fontSize: '0.85rem' }}>{inc.incident_date ? new Date(inc.incident_date).toLocaleDateString() : '—'}</td>
                  <td><span className={`badge ${statusBadge(inc.status)}`}>{inc.status}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ===== CALENDAR ===== */}
      {tab === 'calendar' && (
        <div>
          {calendar.length === 0 ? (
            <div className="empty-state">No upcoming compliance events</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Date</th><th>Type</th><th>Event</th><th>Status</th></tr></thead>
              <tbody>{calendar.map(ev => (
                <tr key={ev.id}>
                  <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{ev.date}</td>
                  <td>
                    <span className={`badge ${ev.type === 'overdue' ? 'badge-danger' : ev.type === 'training_expiry' ? 'badge-warning' : 'badge-info'}`}>
                      {ev.type.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{ev.title}</td>
                  <td><span className={`badge ${statusBadge(ev.status)}`}>{ev.status.replace('_', ' ')}</span></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ===== RAMS ===== */}
      {tab === 'rams' && (
        <div>
          {rams.length === 0 ? (
            <div className="empty-state">No RAMS documents</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Title</th><th>Reference</th><th>Status</th><th>Issue Date</th><th>Expiry</th><th>Created By</th></tr></thead>
              <tbody>{rams.map(r => (
                <tr key={r.id}>
                  <td style={{ fontWeight: 600 }}>{r.title}</td>
                  <td>{r.reference_number || '—'}</td>
                  <td><span className={`badge ${statusBadge(r.status)}`}>{r.status}</span></td>
                  <td>{r.issue_date || '—'}</td>
                  <td>{r.expiry_date || '—'}</td>
                  <td>{r.created_by_name || '—'}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}

      {/* ===== AUDIT LOG ===== */}
      {tab === 'logs' && (
        <div>
          {logs.length === 0 ? (
            <div className="empty-state">No compliance actions logged yet</div>
          ) : (
            <div className="table-wrap"><table>
              <thead><tr><th>Time</th><th>Action</th><th>User</th><th>Target</th><th>Notes</th></tr></thead>
              <tbody>{logs.map(log => (
                <tr key={log.id}>
                  <td style={{ fontSize: '0.85rem', whiteSpace: 'nowrap' }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td><span className="badge badge-info">{log.action.replace('_', ' ')}</span></td>
                  <td>{log.user_name}</td>
                  <td style={{ fontSize: '0.85rem' }}>{log.target}</td>
                  <td style={{ fontSize: '0.85rem', maxWidth: 300 }}>{log.notes}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </div>
      )}
    </div>
  )
}
