'use client'

import { useState, useEffect, useCallback } from 'react'
import { getIncidents, createIncident } from '@/lib/api'

type Filter = '' | 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'CLOSED' | 'riddor'

function statusBadge(s: string) {
  const map: Record<string, string> = {
    OPEN: 'badge-danger', INVESTIGATING: 'badge-warning',
    RESOLVED: 'badge-success', CLOSED: 'badge-info',
    LOW: 'badge-info', MEDIUM: 'badge-warning',
    HIGH: 'badge-danger', CRITICAL: 'badge-danger',
  }
  return map[s] || 'badge-info'
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<any[]>([])
  const [filter, setFilter] = useState<Filter>('')
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getIncidents()
    if (res.data) setIncidents(res.data)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
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
      setShowForm(false)
      load()
    }
  }

  const filtered = incidents.filter(inc => {
    if (!filter) return true
    if (filter === 'riddor') return inc.riddor_reportable
    return inc.status === filter
  })

  const counts = {
    all: incidents.length,
    OPEN: incidents.filter(i => i.status === 'OPEN').length,
    INVESTIGATING: incidents.filter(i => i.status === 'INVESTIGATING').length,
    RESOLVED: incidents.filter(i => i.status === 'RESOLVED').length,
    CLOSED: incidents.filter(i => i.status === 'CLOSED').length,
    riddor: incidents.filter(i => i.riddor_reportable).length,
  }

  const FILTERS: { key: Filter; label: string; count: number; activeClass?: string }[] = [
    { key: '', label: 'All', count: counts.all },
    { key: 'OPEN', label: 'Open', count: counts.OPEN, activeClass: 'active-danger' },
    { key: 'INVESTIGATING', label: 'Investigating', count: counts.INVESTIGATING, activeClass: 'active-warning' },
    { key: 'RESOLVED', label: 'Resolved', count: counts.RESOLVED, activeClass: 'active-success' },
    { key: 'CLOSED', label: 'Closed', count: counts.CLOSED },
    { key: 'riddor', label: 'RIDDOR', count: counts.riddor, activeClass: 'active-danger' },
  ]

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h2 style={{ margin: 0 }}>Incidents</h2>
        <button className="btn btn-sm btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Report Incident'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Report New Incident</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label>Title *</label>
              <input name="title" required placeholder="Brief description" />
            </div>
            <div>
              <label>Location</label>
              <input name="location" placeholder="Where it happened" />
            </div>
            <div>
              <label>Severity</label>
              <select name="severity">
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label>Injury Type</label>
              <select name="injury_type">
                <option value="none">No Injury</option>
                <option value="minor">Minor Injury</option>
                <option value="major">Major Injury</option>
                <option value="dangerous_occurrence">Dangerous Occurrence</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label>Description *</label>
              <textarea name="description" required rows={3} placeholder="Full details of what happened" />
            </div>
            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" name="riddor" style={{ width: 'auto' }} /> RIDDOR Reportable
              </label>
            </div>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <button type="submit" className="btn btn-primary">Submit Report</button>
          </div>
        </form>
      )}

      <div className="tag-filters">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`tag-filter ${filter === f.key ? (f.activeClass || 'active') : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No incidents match this filter</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Incident</th>
                <th>Severity</th>
                <th>Injury</th>
                <th>RIDDOR</th>
                <th>Reported By</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(inc => (
                <tr key={inc.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{inc.title}</div>
                    {inc.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{inc.location}</div>}
                  </td>
                  <td><span className={`badge ${statusBadge(inc.severity)}`}>{inc.severity}</span></td>
                  <td style={{ fontSize: '0.85rem' }}>{(inc.injury_type || 'none').replace(/_/g, ' ')}</td>
                  <td>{inc.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>No</span>}</td>
                  <td style={{ fontSize: '0.85rem' }}>{inc.reported_by_name || '—'}</td>
                  <td style={{ fontSize: '0.85rem' }}>{inc.incident_date ? new Date(inc.incident_date).toLocaleDateString() : '—'}</td>
                  <td><span className={`badge ${statusBadge(inc.status)}`}>{inc.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
