'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getComplianceDashboard, getComplianceItems, createComplianceItem, completeComplianceItem,
  deleteComplianceItem, getIncidents, createIncident, updateIncidentStatus,
  getComplianceDocuments, getRams, getAccidents, createAccident,
} from '@/lib/api'

function rag(pct: number) {
  if (pct >= 80) return 'var(--color-success)'
  if (pct >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function daysUntil(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  now.setHours(0, 0, 0, 0); d.setHours(0, 0, 0, 0)
  return Math.ceil((d.getTime() - now.getTime()) / 86400000)
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    COMPLIANT: 'badge-success', compliant: 'badge-success',
    DUE_SOON: 'badge-warning', due_soon: 'badge-warning',
    OVERDUE: 'badge-danger', overdue: 'badge-danger',
    OPEN: 'badge-danger', INVESTIGATING: 'badge-warning',
    RESOLVED: 'badge-success', CLOSED: 'badge-info',
    valid: 'badge-success', expiring_soon: 'badge-warning', expired: 'badge-danger',
    LOW: 'badge-info', MEDIUM: 'badge-warning', HIGH: 'badge-danger', CRITICAL: 'badge-danger',
  }
  return map[s] || 'badge-info'
}

type Tab = 'overview' | 'register' | 'incidents' | 'accidents' | 'documents'

export default function HealthSafetyPage() {
  const [tab, setTab] = useState<Tab>('overview')
  const [loading, setLoading] = useState(true)

  // Dashboard
  const [dash, setDash] = useState<any>(null)

  // Register
  const [items, setItems] = useState<any[]>([])
  const [regFilter, setRegFilter] = useState('')
  const [showAddItem, setShowAddItem] = useState(false)
  const [itemForm, setItemForm] = useState({ title: '', category: '', item_type: 'BEST_PRACTICE', frequency_type: 'annual', next_due_date: '', notes: '' })
  const [itemSaving, setItemSaving] = useState(false)

  // Incidents
  const [incidents, setIncidents] = useState<any[]>([])
  const [incFilter, setIncFilter] = useState('')
  const [showAddInc, setShowAddInc] = useState(false)

  // Accidents
  const [accidents, setAccidents] = useState<any[]>([])
  const [accFilter, setAccFilter] = useState('')
  const [showAddAcc, setShowAddAcc] = useState(false)

  // Documents
  const [docs, setDocs] = useState<any[]>([])
  const [rams, setRams] = useState<any[]>([])
  const [docFilter, setDocFilter] = useState('')

  const loadAll = useCallback(async () => {
    setLoading(true)
    const [d, it, inc, acc, dc, rm] = await Promise.all([
      getComplianceDashboard(),
      getComplianceItems(),
      getIncidents(),
      getAccidents(),
      getComplianceDocuments(),
      getRams(),
    ])
    if (d.data) setDash(d.data)
    if (it.data) setItems(it.data)
    if (inc.data) setIncidents(inc.data)
    if (acc.data) setAccidents(acc.data)
    if (dc.data) setDocs(dc.data)
    if (rm.data) setRams(rm.data)
    setLoading(false)
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  // --- Handlers ---
  async function handleCompleteItem(id: number) {
    await completeComplianceItem(id)
    loadAll()
  }

  async function handleDeleteItem(id: number) {
    if (!confirm('Delete this compliance item?')) return
    await deleteComplianceItem(id)
    loadAll()
  }

  async function handleAddItem(e: React.FormEvent) {
    e.preventDefault()
    if (!itemForm.title.trim()) return
    setItemSaving(true)
    await createComplianceItem(itemForm)
    setItemSaving(false)
    setShowAddItem(false)
    setItemForm({ title: '', category: '', item_type: 'BEST_PRACTICE', frequency_type: 'annual', next_due_date: '', notes: '' })
    loadAll()
  }

  async function handleAddIncident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createIncident({
      title: fd.get('title'), description: fd.get('description'),
      severity: fd.get('severity'), location: fd.get('location'),
      incident_date: new Date().toISOString(),
      riddor_reportable: fd.get('riddor') === 'on',
    })
    setShowAddInc(false)
    loadAll()
  }

  async function handleAddAccident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createAccident({
      date: fd.get('date'), time: fd.get('time') || null,
      location: fd.get('location'), person_involved: fd.get('person_involved'),
      person_role: fd.get('person_role'), description: fd.get('description'),
      severity: fd.get('severity'), riddor_reportable: fd.get('riddor') === 'on',
      reported_by: fd.get('reported_by'),
    })
    setShowAddAcc(false)
    loadAll()
  }

  async function handleResolveIncident(id: number) {
    await updateIncidentStatus(id, 'RESOLVED')
    loadAll()
  }

  if (loading) return <div className="empty-state">Loading Health &amp; Safety…</div>

  // --- Derived data ---
  const score = dash?.score ?? 0
  const overdueItems = items.filter(i => i.status === 'OVERDUE' || i.status === 'overdue')
  const dueSoonItems = items.filter(i => i.status === 'DUE_SOON' || i.status === 'due_soon')
  const openIncidents = incidents.filter(i => i.status === 'OPEN' || i.status === 'INVESTIGATING')
  const openAccidents = accidents.filter(a => a.status !== 'CLOSED')

  // Register filtering
  const regFiltered = regFilter
    ? items.filter(i => regFilter === 'LEGAL' ? i.item_type === 'LEGAL' : i.status?.toUpperCase() === regFilter)
    : items

  // Incident filtering
  const incFiltered = incFilter
    ? (incFilter === 'riddor' ? incidents.filter(i => i.riddor_reportable) : incidents.filter(i => i.status === incFilter))
    : incidents

  // Accident filtering
  const accFiltered = accFilter
    ? (accFilter === 'riddor' ? accidents.filter(a => a.riddor_reportable) : accidents.filter(a => a.status === accFilter))
    : accidents

  // Documents merged
  const allDocs = [
    ...docs.map(d => ({ ...d, source: 'vault' })),
    ...rams.map(r => ({ id: `rams-${r.id}`, title: r.title, document_type: 'rams', is_current: r.status === 'ACTIVE', is_expired: r.status === 'EXPIRED', expiry_date: r.expiry_date, uploaded_by_name: r.created_by_name, reference_number: r.reference_number, source: 'rams' })),
  ]
  const docFiltered = docFilter
    ? (docFilter === 'expired' ? allDocs.filter(d => d.is_expired) : docFilter === 'current' ? allDocs.filter(d => d.is_current && !d.is_expired) : docFilter === 'rams' ? allDocs.filter(d => d.source === 'rams') : allDocs.filter(d => d.document_type === docFilter))
    : allDocs

  const tabLabels: Record<Tab, string> = { overview: 'Overview', register: 'Register', incidents: 'Incidents', accidents: 'Accidents', documents: 'Documents' }

  return (
    <div>
      <div className="page-header"><h1>Health &amp; Safety</h1></div>
      <p className="staff-header-sub">Compliance score, overdue actions, incidents, documents.</p>

      {/* Status strip */}
      <div className="status-strip">
        <div className="status-strip-item">
          <span className="status-strip-num" style={{ color: rag(score) }}>{score}%</span>
          <span className="status-strip-label">Score</span>
        </div>
        <div className="status-strip-item">
          <span className="status-strip-num" style={{ color: overdueItems.length > 0 ? 'var(--color-danger)' : undefined }}>{overdueItems.length}</span>
          <span className="status-strip-label">Overdue</span>
        </div>
        <div className="status-strip-item">
          <span className="status-strip-num" style={{ color: dueSoonItems.length > 0 ? 'var(--color-warning)' : undefined }}>{dueSoonItems.length}</span>
          <span className="status-strip-label">Due Soon</span>
        </div>
        <div className="status-strip-item">
          <span className="status-strip-num" style={{ color: openIncidents.length > 0 ? 'var(--color-danger)' : undefined }}>{openIncidents.length}</span>
          <span className="status-strip-label">Open Incidents</span>
        </div>
        <div className="status-strip-item">
          <span className="status-strip-num" style={{ color: openAccidents.length > 0 ? 'var(--color-danger)' : undefined }}>{openAccidents.length}</span>
          <span className="status-strip-label">Open Accidents</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(['overview', 'register', 'incidents', 'accidents', 'documents'] as Tab[]).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {tabLabels[t]}
            {t === 'incidents' && openIncidents.length > 0 && <span style={{ marginLeft: 6, background: 'var(--color-danger)', color: '#fff', borderRadius: 999, padding: '1px 6px', fontSize: '0.7rem', fontWeight: 700 }}>{openIncidents.length}</span>}
            {t === 'register' && overdueItems.length > 0 && <span style={{ marginLeft: 6, background: 'var(--color-danger)', color: '#fff', borderRadius: 999, padding: '1px 6px', fontSize: '0.7rem', fontWeight: 700 }}>{overdueItems.length}</span>}
          </button>
        ))}
      </div>

      {/* ═══════ OVERVIEW TAB ═══════ */}
      {tab === 'overview' && (
        <div>
          {/* Immediate actions */}
          {overdueItems.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '0.75rem', color: 'var(--color-danger)' }}>Immediate Actions</h3>
              {overdueItems.slice(0, 5).map(item => (
                <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0.6rem 0', borderBottom: '1px solid var(--color-border)' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-danger)', flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      {item.category}{item.next_due_date && ` · Due ${item.next_due_date} (${daysUntil(item.next_due_date)}d overdue)`}
                      {item.item_type === 'LEGAL' && <span style={{ color: 'var(--color-danger)', marginLeft: 6 }}>Legal</span>}
                    </div>
                  </div>
                  <button className="btn btn-sm btn-danger" onClick={() => handleCompleteItem(item.id)}>Mark Done</button>
                </div>
              ))}
            </div>
          )}

          {dueSoonItems.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '0.75rem', color: 'var(--color-warning)' }}>Upcoming</h3>
              {dueSoonItems.slice(0, 5).map(item => (
                <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0.6rem 0', borderBottom: '1px solid var(--color-border)' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-warning)', flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                      {item.category}{item.next_due_date && ` · Due ${item.next_due_date} (${daysUntil(item.next_due_date)}d)`}
                    </div>
                  </div>
                  <button className="btn btn-sm" onClick={() => handleCompleteItem(item.id)}>Complete</button>
                </div>
              ))}
            </div>
          )}

          {overdueItems.length === 0 && dueSoonItems.length === 0 && (
            <div className="empty-cta" style={{ marginBottom: '1.5rem' }}>
              <div className="empty-cta-title" style={{ color: 'var(--color-success)' }}>All clear</div>
              <div className="empty-cta-desc">No overdue or upcoming compliance items.</div>
            </div>
          )}

          {/* Category bars */}
          {dash?.categories?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '0.75rem' }}>Compliance by Category</h3>
              {dash.categories.map((cat: any) => (
                <div key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: '0.85rem', width: 140, flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cat.name}</span>
                  <div style={{ flex: 1, height: 8, background: 'var(--color-border)', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${cat.score_pct || 0}%`, background: rag(cat.score_pct || 0), borderRadius: 4, transition: 'width 300ms ease' }} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, width: 50, textAlign: 'right' }}>{cat.compliant}/{cat.total}</span>
                </div>
              ))}
            </div>
          )}

          {/* RIDDOR alert */}
          {dash?.riddor_count > 0 && (
            <div style={{ background: '#fef2f2', borderLeft: '4px solid var(--color-danger)', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1.5rem' }}>
              <strong>RIDDOR:</strong> {dash.riddor_count} reportable incident(s) recorded
            </div>
          )}
        </div>
      )}

      {/* ═══════ REGISTER TAB ═══════ */}
      {tab === 'register' && (
        <div>
          <div className="tab-subheader">
            <div className="tab-subheader-left">
              <div className="filter-pills">
                {[
                  { key: '', label: `All (${items.length})` },
                  { key: 'OVERDUE', label: `Overdue (${overdueItems.length})` },
                  { key: 'DUE_SOON', label: `Due Soon (${dueSoonItems.length})` },
                  { key: 'COMPLIANT', label: `Compliant (${items.filter(i => (i.status || '').toUpperCase() === 'COMPLIANT').length})` },
                  { key: 'LEGAL', label: `Legal (${items.filter(i => i.item_type === 'LEGAL').length})` },
                ].map(f => (
                  <button key={f.key} className={`filter-pill ${regFilter === f.key ? 'active' : ''}`} onClick={() => setRegFilter(f.key)}>{f.label}</button>
                ))}
              </div>
            </div>
            <div className="tab-subheader-right">
              <button className="btn btn-primary" onClick={() => setShowAddItem(!showAddItem)}>{showAddItem ? 'Cancel' : '+ Add Item'}</button>
            </div>
          </div>

          {showAddItem && (
            <form onSubmit={handleAddItem} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Title *</label><input className="form-input" value={itemForm.title} onChange={e => setItemForm({ ...itemForm, title: e.target.value })} required /></div>
                <div><label className="form-label">Category</label><input className="form-input" value={itemForm.category} onChange={e => setItemForm({ ...itemForm, category: e.target.value })} placeholder="e.g. Fire Safety" /></div>
                <div><label className="form-label">Type</label><select className="form-input" value={itemForm.item_type} onChange={e => setItemForm({ ...itemForm, item_type: e.target.value })}><option value="LEGAL">Legal Requirement</option><option value="BEST_PRACTICE">Best Practice</option></select></div>
                <div><label className="form-label">Frequency</label><select className="form-input" value={itemForm.frequency_type} onChange={e => setItemForm({ ...itemForm, frequency_type: e.target.value })}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option><option value="biennial">Every 2 Years</option><option value="5_year">Every 5 Years</option><option value="ad_hoc">Ad Hoc</option></select></div>
                <div><label className="form-label">Next Due Date</label><input className="form-input" type="date" value={itemForm.next_due_date} onChange={e => setItemForm({ ...itemForm, next_due_date: e.target.value })} /></div>
                <div><label className="form-label">Notes</label><input className="form-input" value={itemForm.notes} onChange={e => setItemForm({ ...itemForm, notes: e.target.value })} /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary" disabled={itemSaving}>{itemSaving ? 'Saving…' : 'Add Item'}</button>
              </div>
            </form>
          )}

          {regFiltered.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No compliance items</div>
              <div className="empty-cta-desc">Add your first compliance item — fire safety, PAT testing, insurance, etc.</div>
              <button className="btn btn-primary" onClick={() => setShowAddItem(true)}>+ Add Item</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Item</th><th>Category</th><th>Frequency</th><th>Last Done</th><th>Next Due</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {regFiltered.map(item => (
                    <tr key={item.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{item.title}</div>
                        {item.item_type === 'LEGAL' && <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)' }}>Legal requirement</span>}
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>{item.category}</td>
                      <td style={{ fontSize: '0.85rem' }}>{(item.frequency_type || '').replace(/_/g, ' ')}</td>
                      <td style={{ fontSize: '0.85rem' }}>{item.last_completed_date || '—'}</td>
                      <td style={{ fontSize: '0.85rem', fontWeight: (item.status || '').toUpperCase() === 'OVERDUE' ? 700 : 400 }}>{item.next_due_date || '—'}</td>
                      <td><span className={`badge ${statusBadge(item.status)}`}>{(item.status || '').replace(/_/g, ' ')}</span></td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        {(item.status || '').toUpperCase() !== 'COMPLIANT' && <button className="btn btn-sm" onClick={() => handleCompleteItem(item.id)} style={{ marginRight: 4 }}>Done</button>}
                        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteItem(item.id)}>Del</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ INCIDENTS TAB ═══════ */}
      {tab === 'incidents' && (
        <div>
          <div className="tab-subheader">
            <div className="tab-subheader-left">
              <div className="filter-pills">
                {[
                  { key: '', label: `All (${incidents.length})` },
                  { key: 'OPEN', label: `Open (${incidents.filter(i => i.status === 'OPEN').length})` },
                  { key: 'INVESTIGATING', label: `Investigating (${incidents.filter(i => i.status === 'INVESTIGATING').length})` },
                  { key: 'RESOLVED', label: `Resolved (${incidents.filter(i => i.status === 'RESOLVED').length})` },
                  { key: 'riddor', label: `RIDDOR (${incidents.filter(i => i.riddor_reportable).length})` },
                ].map(f => (
                  <button key={f.key} className={`filter-pill ${incFilter === f.key ? 'active' : ''}`} onClick={() => setIncFilter(f.key)}>{f.label}</button>
                ))}
              </div>
            </div>
            <div className="tab-subheader-right">
              <button className="btn btn-primary" onClick={() => setShowAddInc(!showAddInc)}>{showAddInc ? 'Cancel' : '+ Report Incident'}</button>
            </div>
          </div>

          {showAddInc && (
            <form onSubmit={handleAddIncident} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Title *</label><input className="form-input" name="title" required /></div>
                <div><label className="form-label">Location</label><input className="form-input" name="location" /></div>
                <div><label className="form-label">Severity</label><select className="form-input" name="severity"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}><label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem', cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR Reportable</label></div>
                <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Description *</label><textarea className="form-input" name="description" required rows={3} /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Submit Report</button></div>
            </form>
          )}

          {incFiltered.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No incidents</div>
              <div className="empty-cta-desc">Report incidents as they happen — slips, near-misses, equipment failures.</div>
              <button className="btn btn-primary" onClick={() => setShowAddInc(true)}>+ Report Incident</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Incident</th><th>Severity</th><th>RIDDOR</th><th>Date</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {incFiltered.map(inc => (
                    <tr key={inc.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{inc.title}</div>
                        {inc.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{inc.location}</div>}
                      </td>
                      <td><span className={`badge ${statusBadge(inc.severity)}`}>{inc.severity}</span></td>
                      <td>{inc.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>No</span>}</td>
                      <td style={{ fontSize: '0.85rem' }}>{inc.incident_date ? new Date(inc.incident_date).toLocaleDateString() : '—'}</td>
                      <td><span className={`badge ${statusBadge(inc.status)}`}>{inc.status}</span></td>
                      <td>{(inc.status === 'OPEN' || inc.status === 'INVESTIGATING') && <button className="btn btn-sm" onClick={() => handleResolveIncident(inc.id)}>Resolve</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ ACCIDENTS TAB ═══════ */}
      {tab === 'accidents' && (
        <div>
          <div className="tab-subheader">
            <div className="tab-subheader-left">
              <div className="filter-pills">
                {[
                  { key: '', label: `All (${accidents.length})` },
                  { key: 'OPEN', label: `Open (${accidents.filter(a => a.status === 'OPEN').length})` },
                  { key: 'INVESTIGATING', label: `Investigating (${accidents.filter(a => a.status === 'INVESTIGATING').length})` },
                  { key: 'CLOSED', label: `Closed (${accidents.filter(a => a.status === 'CLOSED').length})` },
                  { key: 'riddor', label: `RIDDOR (${accidents.filter(a => a.riddor_reportable).length})` },
                ].map(f => (
                  <button key={f.key} className={`filter-pill ${accFilter === f.key ? 'active' : ''}`} onClick={() => setAccFilter(f.key)}>{f.label}</button>
                ))}
              </div>
            </div>
            <div className="tab-subheader-right">
              <button className="btn btn-primary" onClick={() => setShowAddAcc(!showAddAcc)}>{showAddAcc ? 'Cancel' : '+ Log Accident'}</button>
            </div>
          </div>

          {showAddAcc && (
            <form onSubmit={handleAddAccident} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Date *</label><input className="form-input" name="date" type="date" required defaultValue={new Date().toISOString().split('T')[0]} /></div>
                <div><label className="form-label">Time</label><input className="form-input" name="time" type="time" /></div>
                <div><label className="form-label">Person Involved *</label><input className="form-input" name="person_involved" required /></div>
                <div><label className="form-label">Role</label><select className="form-input" name="person_role"><option value="Staff">Staff</option><option value="Client">Client</option><option value="Visitor">Visitor</option><option value="Contractor">Contractor</option></select></div>
                <div><label className="form-label">Location</label><input className="form-input" name="location" /></div>
                <div><label className="form-label">Severity</label><select className="form-input" name="severity"><option value="MINOR">Minor (First Aid)</option><option value="MODERATE">Moderate (Medical)</option><option value="MAJOR">Major (Hospital)</option><option value="FATAL">Fatal</option></select></div>
                <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Description *</label><textarea className="form-input" name="description" required rows={3} /></div>
                <div><label className="form-label">Reported By</label><input className="form-input" name="reported_by" /></div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}><label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem', cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR Reportable</label></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Log Accident</button></div>
            </form>
          )}

          {accFiltered.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No accidents logged</div>
              <div className="empty-cta-desc">Log workplace accidents here — includes RIDDOR reporting support.</div>
              <button className="btn btn-primary" onClick={() => setShowAddAcc(true)}>+ Log Accident</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Person</th><th>Role</th><th>Severity</th><th>RIDDOR</th><th>Date</th><th>Status</th></tr></thead>
                <tbody>
                  {accFiltered.map(a => (
                    <tr key={a.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{a.person_involved}</div>
                        {a.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{a.location}</div>}
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>{a.person_role || '—'}</td>
                      <td><span className={`badge ${statusBadge(a.severity)}`}>{a.severity}</span></td>
                      <td>{a.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>No</span>}</td>
                      <td style={{ fontSize: '0.85rem' }}>{a.date}</td>
                      <td><span className={`badge ${statusBadge(a.status)}`}>{a.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ DOCUMENTS TAB ═══════ */}
      {tab === 'documents' && (
        <div>
          <div className="tab-subheader">
            <div className="tab-subheader-left">
              <div className="filter-pills">
                {[
                  { key: '', label: `All (${allDocs.length})` },
                  { key: 'current', label: `Current (${allDocs.filter(d => d.is_current && !d.is_expired).length})` },
                  { key: 'expired', label: `Expired (${allDocs.filter(d => d.is_expired).length})` },
                  { key: 'rams', label: `RAMS (${rams.length})` },
                ].map(f => (
                  <button key={f.key} className={`filter-pill ${docFilter === f.key ? 'active' : ''}`} onClick={() => setDocFilter(f.key)}>{f.label}</button>
                ))}
              </div>
            </div>
          </div>

          {docFiltered.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No documents</div>
              <div className="empty-cta-desc">Policies, certificates, insurance documents and RAMS will appear here.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
              {docFiltered.map(doc => (
                <div key={doc.id} style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{doc.title}</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
                    <span className={`badge ${doc.is_expired ? 'badge-danger' : 'badge-success'}`}>{doc.is_expired ? 'Expired' : 'Current'}</span>
                    <span className="badge badge-neutral">{(doc.document_type || '').replace(/_/g, ' ')}</span>
                  </div>
                  {doc.expiry_date && <div style={{ fontSize: '0.8rem', color: doc.is_expired ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>{doc.is_expired ? 'Expired' : 'Expires'}: {doc.expiry_date}</div>}
                  {doc.reference_number && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Ref: {doc.reference_number}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
