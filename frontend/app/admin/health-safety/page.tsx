'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getWiggumDashboard, getComplianceItems, completeComplianceItem, deleteComplianceItem,
  completeComplianceItemWithEvidence, createComplianceItem, parseComplianceCommand,
  getIncidents, createIncident, updateIncidentStatus,
  getAccidents, createAccident, updateAccident,
  getComplianceDocuments, getRams,
  getComplianceCalendar, getComplianceAuditLog,
} from '@/lib/api'

type View = 'active' | 'sorted'
type Tab = 'today' | 'register' | 'calendar' | 'incidents' | 'accidents' | 'documents' | 'audit'

const BANNER: Record<string, { bg: string; border: string; color: string; icon: string }> = {
  green: { bg: '#f0fdf4', border: '#22c55e', color: '#15803d', icon: '✓' },
  amber: { bg: '#fffbeb', border: '#f59e0b', color: '#92400e', icon: '!' },
  red:   { bg: '#fef2f2', border: '#ef4444', color: '#991b1b', icon: '✕' },
}

function fmtDate(d: string | null) {
  if (!d) return '—'
  return new Date(d + 'T00:00:00').toLocaleDateString('en-GB')
}

function riddorDaysLeft(accDate: string): number | null {
  if (!accDate) return null
  const deadline = new Date(new Date(accDate + 'T00:00:00').getTime() + 10 * 86400000)
  return Math.ceil((deadline.getTime() - Date.now()) / 86400000)
}

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default function HealthSafetyPage() {
  const [tab, setTab] = useState<Tab>('today')
  const [view, setView] = useState<View>('active')
  const [loading, setLoading] = useState(true)
  const [wiggum, setWiggum] = useState<any>(null)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [toast, setToast] = useState<string | null>(null)

  // Completion modal
  const [completeModal, setCompleteModal] = useState<any>(null)

  // NL input
  const [nlText, setNlText] = useState('')
  const [nlResult, setNlResult] = useState<any>(null)
  const [nlLoading, setNlLoading] = useState(false)

  // Register
  const [items, setItems] = useState<any[]>([])
  const [showAddItem, setShowAddItem] = useState(false)
  const [itemForm, setItemForm] = useState({ title: '', category: '', item_type: 'LEGAL', frequency_type: 'annual', next_due_date: '', notes: '', plain_english_why: '' })
  const [regStatusFilter, setRegStatusFilter] = useState('')
  const [regTypeFilter, setRegTypeFilter] = useState('')
  const [resolveMode, setResolveMode] = useState(false)

  // Incidents
  const [incidents, setIncidents] = useState<any[]>([])
  const [showAddInc, setShowAddInc] = useState(false)
  const [incFilter, setIncFilter] = useState('')

  // Accidents
  const [accidents, setAccidents] = useState<any[]>([])
  const [showAddAcc, setShowAddAcc] = useState(false)
  const [accStatusFilter, setAccStatusFilter] = useState('')
  const [accSevFilter, setAccSevFilter] = useState('')
  const [accRiddorFilter, setAccRiddorFilter] = useState(false)

  // Documents
  const [docs, setDocs] = useState<any[]>([])
  const [rams, setRams] = useState<any[]>([])

  // Calendar
  const now = new Date()
  const [calYear, setCalYear] = useState(now.getFullYear())
  const [calMonth, setCalMonth] = useState(now.getMonth() + 1)
  const [calData, setCalData] = useState<any>(null)
  const [selectedDay, setSelectedDay] = useState<string | null>(null)

  // Audit
  const [auditLog, setAuditLog] = useState<any[]>([])

  const flash = useCallback((msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500) }, [])

  const loadCore = useCallback(async () => {
    setLoading(true)
    const [w, it, inc, acc, dc, rm] = await Promise.all([
      getWiggumDashboard(), getComplianceItems(), getIncidents(), getAccidents(), getComplianceDocuments(), getRams(),
    ])
    if (w.data) setWiggum(w.data)
    if (it.data) setItems(it.data)
    if (inc.data) setIncidents(inc.data)
    if (acc.data) setAccidents(acc.data)
    if (dc.data) setDocs(dc.data)
    if (rm.data) setRams(rm.data)
    setLoading(false)
  }, [])

  useEffect(() => { loadCore() }, [loadCore])

  // Calendar lazy load
  useEffect(() => {
    if (tab === 'calendar') getComplianceCalendar(calYear, calMonth).then(r => { if (r.data) setCalData(r.data) })
  }, [tab, calYear, calMonth])

  // Audit lazy load
  useEffect(() => {
    if (tab === 'audit') getComplianceAuditLog(30).then(r => { if (r.data) setAuditLog(r.data.logs || []) })
  }, [tab])

  // ── Handlers ──

  async function handleModalComplete(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!completeModal) return
    const fd = new FormData(e.currentTarget)
    const res = await completeComplianceItemWithEvidence(completeModal.id, fd)
    if (!res.error) {
      flash(res.data?.message || 'Completed')
      setCompleteModal(null)
      loadCore()
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this compliance item?')) return
    await deleteComplianceItem(id)
    loadCore()
  }

  async function handleAddItem(e: React.FormEvent) {
    e.preventDefault()
    if (!itemForm.title.trim()) return
    await createComplianceItem(itemForm)
    setShowAddItem(false)
    setItemForm({ title: '', category: '', item_type: 'LEGAL', frequency_type: 'annual', next_due_date: '', notes: '', plain_english_why: '' })
    flash('Item added')
    loadCore()
  }

  async function handleNlSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!nlText.trim()) return
    setNlLoading(true)
    const res = await parseComplianceCommand(nlText)
    setNlResult(res.data)
    setNlLoading(false)
    if (res.data?.action === 'complete' && res.data?.item_id) {
      setSelectedItem(wiggum?.action_items?.find((a: any) => a.id === res.data.item_id) || null)
    }
  }

  async function handleNlConfirm() {
    if (nlResult?.action === 'complete' && nlResult?.item_id) {
      await completeComplianceItem(nlResult.item_id)
      setNlResult(null); setNlText('')
      flash('Completed'); loadCore()
    }
  }

  async function handleAddIncident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createIncident({
      title: fd.get('title'), description: fd.get('description'),
      severity: fd.get('severity'), location: fd.get('location'),
      incident_date: new Date().toISOString(), riddor_reportable: fd.get('riddor') === 'on',
    })
    setShowAddInc(false); flash('Incident reported'); loadCore()
  }

  async function handleAddAccident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createAccident({
      date: fd.get('date'), time: fd.get('time') || null,
      location: fd.get('location'), person_involved: fd.get('person_involved'),
      person_role: fd.get('person_role'), description: fd.get('description'),
      severity: fd.get('severity'), riddor_reportable: fd.get('riddor') === 'on',
      follow_up_required: fd.get('follow_up') === 'on', reported_by: fd.get('reported_by'),
    })
    setShowAddAcc(false); flash('Accident logged'); loadCore()
  }

  async function handleAccidentStatus(id: number, newStatus: string) {
    await updateAccident(id, { status: newStatus })
    flash(`Status → ${newStatus}`); loadCore()
  }

  if (loading) return <div className="empty-state">Loading…</div>

  const w = wiggum || { status_level: 'green', status_message: 'Loading…', action_items: [], sorted_items: [], counts: {}, score: 0, score_label: 'Safe' }
  const banner = BANNER[w.status_level] || BANNER.green
  const openInc = incidents.filter(i => i.status === 'OPEN' || i.status === 'INVESTIGATING')
  const openAcc = accidents.filter(a => a.status !== 'CLOSED')

  // Register filtering
  let regItems = resolveMode ? items.filter(i => i.status !== 'COMPLIANT') : items
  if (regStatusFilter && !resolveMode) regItems = regItems.filter(i => i.status === regStatusFilter)
  if (regTypeFilter) regItems = regItems.filter(i => i.item_type === regTypeFilter)

  // Incident filtering
  const incFiltered = incFilter === 'riddor' ? incidents.filter(i => i.riddor_reportable) : incFilter ? incidents.filter(i => i.status === incFilter) : incidents

  // Accident filtering
  let accFiltered = accidents
  if (accStatusFilter) accFiltered = accFiltered.filter(a => a.status === accStatusFilter)
  if (accSevFilter) accFiltered = accFiltered.filter(a => a.severity === accSevFilter)
  if (accRiddorFilter) accFiltered = accFiltered.filter(a => a.riddor_reportable)

  // Documents
  const allDocs = [
    ...docs.map(d => ({ ...d, source: 'vault' })),
    ...rams.map(r => ({ id: `rams-${r.id}`, title: r.title, document_type: 'rams', is_current: r.status === 'ACTIVE', is_expired: r.status === 'EXPIRED', expiry_date: r.expiry_date, source: 'rams' })),
  ]

  // Calendar grid
  function buildCalGrid(year: number, month: number) {
    const first = new Date(year, month - 1, 1)
    const startDay = (first.getDay() + 6) % 7
    const daysInMonth = new Date(year, month, 0).getDate()
    const weeks: (number | null)[][] = []
    let week: (number | null)[] = Array(startDay).fill(null)
    for (let d = 1; d <= daysInMonth; d++) { week.push(d); if (week.length === 7) { weeks.push(week); week = [] } }
    if (week.length > 0) { while (week.length < 7) week.push(null); weeks.push(week) }
    return weeks
  }

  const calDays = calData?.days || {}

  const TABS: { key: Tab; label: string; badge?: number }[] = [
    { key: 'today', label: 'Today', badge: w.action_items?.length || 0 },
    { key: 'register', label: 'Register' },
    { key: 'calendar', label: 'Calendar' },
    { key: 'incidents', label: 'Incidents', badge: openInc.length },
    { key: 'accidents', label: 'Accidents', badge: openAcc.length },
    { key: 'documents', label: 'Documents' },
    { key: 'audit', label: 'Audit' },
  ]

  return (
    <div>
      {/* ═══ COMPLETION MODAL ═══ */}
      {completeModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ maxWidth: 560, width: '100%', background: '#fff', borderRadius: 12, padding: '1.5rem', position: 'relative', maxHeight: '90vh', overflowY: 'auto' }}>
            <button onClick={() => setCompleteModal(null)} style={{ position: 'absolute', top: 12, right: 16, background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: 'var(--color-text-muted)' }}>×</button>
            <h2 style={{ margin: '0 0 0.25rem', fontSize: '1.1rem' }}>{completeModal.title}</h2>
            <div style={{ display: 'flex', gap: 6, marginBottom: '0.75rem', flexWrap: 'wrap' }}>
              <span className={`badge ${completeModal.item_type === 'LEGAL' ? 'badge-danger' : 'badge-info'}`}>{completeModal.item_type === 'LEGAL' ? 'Legal' : 'Best Practice'}</span>
              <span className={`badge ${completeModal.status === 'OVERDUE' ? 'badge-danger' : completeModal.status === 'DUE_SOON' ? 'badge-warning' : 'badge-success'}`}>{(completeModal.status || '').replace(/_/g, ' ')}</span>
            </div>
            {completeModal.description && <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{completeModal.description}</p>}
            {completeModal.plain_english_why && <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{completeModal.plain_english_why}</p>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
              <div><span style={{ color: 'var(--color-text-muted)' }}>Category:</span> {completeModal.category}</div>
              <div><span style={{ color: 'var(--color-text-muted)' }}>Frequency:</span> {(completeModal.frequency_type || '').replace(/_/g, ' ')}</div>
              <div><span style={{ color: 'var(--color-text-muted)' }}>Next Due:</span> {fmtDate(completeModal.next_due_date)}</div>
              <div><span style={{ color: 'var(--color-text-muted)' }}>Last Done:</span> {fmtDate(completeModal.last_completed_date)}</div>
              {completeModal.legal_reference && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--color-text-muted)' }}>Legal Ref:</span> {completeModal.legal_reference}</div>}
            </div>
            {completeModal.document && (
              <div style={{ padding: '0.5rem', background: '#f0fdf4', borderRadius: 6, marginBottom: '0.75rem', fontSize: '0.85rem' }}>
                <strong>Current evidence:</strong> <a href={completeModal.document} target="_blank" rel="noopener" style={{ color: 'var(--color-primary)', textDecoration: 'underline' }}>View</a>
              </div>
            )}
            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem' }}>
              <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem' }}>{completeModal.status === 'COMPLIANT' ? 'Record new completion' : 'Mark as complete'}</h3>
              <form onSubmit={handleModalComplete}>
                <div style={{ display: 'grid', gap: '0.6rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
                    <div><label className="form-label">Completion Date *</label><input className="form-input" name="completed_date" type="date" required defaultValue={new Date().toISOString().split('T')[0]} /></div>
                    <div><label className="form-label">Completed By</label><input className="form-input" name="completed_by" placeholder="Name" /></div>
                  </div>
                  <div><label className="form-label">Upload Evidence {completeModal.evidence_required ? '*' : '(optional)'}</label><input name="evidence" type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" style={{ fontSize: '0.85rem' }} /></div>
                  <div><label className="form-label">Comments</label><textarea className="form-input" name="comments" rows={2} placeholder="Notes…" /></div>
                </div>
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                  <button type="submit" className="btn btn-primary">{completeModal.status === 'COMPLIANT' ? 'Record' : 'Mark Complete'}</button>
                  <button type="button" className="btn" onClick={() => setCompleteModal(null)}>Cancel</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ═══ HEADER ═══ */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Health &amp; Safety — Today</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{w.score_label}</span>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: banner.color }}>{w.score}%</span>
        </div>
      </div>

      {/* ═══ STATUS BANNER ═══ */}
      <div style={{ background: banner.bg, borderLeft: `5px solid ${banner.border}`, padding: '1rem 1.25rem', borderRadius: 8, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: '1.5rem', fontWeight: 800, color: banner.color, lineHeight: 1 }}>{banner.icon}</span>
        <span style={{ fontSize: '1.05rem', fontWeight: 600, color: banner.color }}>{w.status_message}</span>
      </div>

      {/* ═══ NATURAL LANGUAGE INPUT ═══ */}
      <form onSubmit={handleNlSubmit} style={{ marginBottom: '1.25rem', display: 'flex', gap: 8 }}>
        <input style={{ flex: 1, padding: '0.6rem 0.9rem', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: '0.95rem' }}
          placeholder='Type a command… e.g. "Upload fire risk assessment" or "Log accident Ben cut hand"'
          value={nlText} onChange={e => setNlText(e.target.value)} />
        <button type="submit" className="btn btn-primary" disabled={nlLoading} style={{ whiteSpace: 'nowrap' }}>{nlLoading ? '…' : 'Go'}</button>
      </form>
      {nlResult && (
        <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.9rem' }}>{nlResult.message}</span>
          <div style={{ display: 'flex', gap: 6 }}>
            {nlResult.action === 'complete' && nlResult.item_id && <button className="btn btn-sm btn-primary" onClick={handleNlConfirm}>Yes, mark complete</button>}
            <button className="btn btn-sm" onClick={() => { setNlResult(null); setNlText('') }}>Dismiss</button>
          </div>
        </div>
      )}

      {/* ═══ TABS ═══ */}
      <div className="tabs" style={{ marginBottom: '1rem' }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
            {(t.badge ?? 0) > 0 && t.key !== 'today' && (
              <span style={{ marginLeft: 6, background: 'var(--color-danger)', color: '#fff', borderRadius: 999, padding: '1px 6px', fontSize: '0.7rem', fontWeight: 700 }}>{t.badge}</span>
            )}
          </button>
        ))}
      </div>

      {/* ═══════ TODAY — WIGGUM LOOP ═══════ */}
      {tab === 'today' && (
        <div>
          <div style={{ display: 'flex', gap: 4, marginBottom: '1rem' }}>
            <button className={`filter-pill ${view === 'active' ? 'active' : ''}`} onClick={() => setView('active')}>Active</button>
            <button className={`filter-pill ${view === 'sorted' ? 'active' : ''}`} onClick={() => setView('sorted')}>Sorted</button>
          </div>

          {view === 'active' ? (
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                {w.action_items.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-success)' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>Sorted</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>Nothing needs doing right now.</div>
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead><tr><th style={{ width: '30%' }}>What</th><th style={{ width: '25%' }}>Why it matters</th><th style={{ width: '15%' }}>When</th><th style={{ width: '15%' }}>Do this</th><th style={{ width: '15%' }}></th></tr></thead>
                      <tbody>
                        {w.action_items.map((a: any) => (
                          <tr key={a.id} onClick={() => setSelectedItem(a)} style={{ cursor: 'pointer', background: selectedItem?.id === a.id ? '#f0f9ff' : undefined }}>
                            <td>
                              <div style={{ fontWeight: 600 }}>{a.what}</div>
                              {a.item_type === 'LEGAL' && <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)', fontWeight: 600 }}>Legal requirement</span>}
                            </td>
                            <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{a.why}</td>
                            <td><span style={{ fontSize: '0.85rem', fontWeight: a.status === 'OVERDUE' ? 700 : 400, color: a.status === 'OVERDUE' ? 'var(--color-danger)' : undefined }}>{a.days_info || '—'}</span></td>
                            <td>
                              <button className={`btn btn-sm ${a.status === 'OVERDUE' && a.item_type === 'LEGAL' ? 'btn-danger' : 'btn-primary'}`}
                                onClick={(e) => { e.stopPropagation(); const item = items.find(i => i.id === a.id); setCompleteModal(item || a) }}>
                                {a.do_this}
                              </button>
                            </td>
                            <td><button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); handleDelete(a.id) }} style={{ opacity: 0.5 }}>Del</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
              {selectedItem && (
                <div style={{ width: 300, flexShrink: 0, background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1.25rem' }}>
                  <h3 style={{ fontSize: '0.95rem', marginBottom: 8 }}>What this means</h3>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{selectedItem.what}</div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: 12 }}>{selectedItem.plain_english_why || selectedItem.why}</p>
                  {selectedItem.description && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.4, marginBottom: 12 }}>{selectedItem.description}</p>}
                  {selectedItem.legal_reference && <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginBottom: 12 }}>Ref: {selectedItem.legal_reference}</p>}
                  <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => { const item = items.find(i => i.id === selectedItem.id); setCompleteModal(item || selectedItem) }}>{selectedItem.do_this}</button>
                </div>
              )}
            </div>
          ) : (
            <div>
              {w.sorted_items.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)' }}>
                  <div style={{ fontSize: '1.1rem', marginBottom: 4 }}>Nothing completed recently</div>
                  <div style={{ fontSize: '0.85rem' }}>Items you complete will appear here.</div>
                </div>
              ) : (
                <div>
                  {w.sorted_items.filter((s: any) => s.when === 'today').length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h3 style={{ fontSize: '0.95rem', color: 'var(--color-success)', marginBottom: 8 }}>Completed today</h3>
                      {w.sorted_items.filter((s: any) => s.when === 'today').map((s: any) => (
                        <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
                          <span style={{ color: 'var(--color-success)', fontWeight: 700 }}>✓</span>
                          <span style={{ fontWeight: 500 }}>{s.title}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>{s.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {w.sorted_items.filter((s: any) => s.when !== 'today').length > 0 && (
                    <div>
                      <h3 style={{ fontSize: '0.95rem', color: 'var(--color-text-muted)', marginBottom: 8 }}>This week</h3>
                      {w.sorted_items.filter((s: any) => s.when !== 'today').map((s: any) => (
                        <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
                          <span style={{ color: 'var(--color-success)' }}>✓</span>
                          <span>{s.title}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>{s.when}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ═══════ REGISTER ═══════ */}
      {tab === 'register' && (
        <div>
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {[{ l: 'All', v: '' }, { l: 'Overdue', v: 'OVERDUE' }, { l: 'Due Soon', v: 'DUE_SOON' }, { l: 'Compliant', v: 'COMPLIANT' }].map(f => (
              <button key={f.v} className={`filter-pill ${regStatusFilter === f.v && !resolveMode ? 'active' : ''}`} onClick={() => { setRegStatusFilter(f.v); setResolveMode(false) }}>{f.l}</button>
            ))}
            <span style={{ width: 1, height: 18, background: 'var(--color-border)', margin: '0 4px' }} />
            {[{ l: 'All Types', v: '' }, { l: 'Legal', v: 'LEGAL' }, { l: 'Best Practice', v: 'BEST_PRACTICE' }].map(f => (
              <button key={f.v} className={`filter-pill ${regTypeFilter === f.v ? 'active' : ''}`} onClick={() => setRegTypeFilter(f.v)}>{f.l}</button>
            ))}
            <span style={{ width: 1, height: 18, background: 'var(--color-border)', margin: '0 4px' }} />
            <button className={`filter-pill ${resolveMode ? 'active' : ''}`} onClick={() => setResolveMode(!resolveMode)} style={resolveMode ? { background: 'var(--color-danger)', color: '#fff', borderColor: 'var(--color-danger)' } : {}}>
              {resolveMode ? '✓ Resolve Mode' : 'Resolve Mode'}
            </button>
            <div style={{ marginLeft: 'auto' }}>
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
                <div><label className="form-label">Why it matters</label><input className="form-input" value={itemForm.plain_english_why} onChange={e => setItemForm({ ...itemForm, plain_english_why: e.target.value })} placeholder="Plain English" /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Add Item</button></div>
            </form>
          )}

          {regItems.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">{resolveMode ? 'Nothing needs action' : 'No items match'}</div>
              <div className="empty-cta-desc">{resolveMode ? 'All compliance items are current.' : 'Try adjusting your filters or add a new item.'}</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {regItems.map((item: any) => (
                <div key={item.id} onClick={() => setCompleteModal(item)} style={{
                  display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.65rem 0.85rem',
                  background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, cursor: 'pointer',
                  borderLeft: `4px solid ${item.status === 'OVERDUE' ? 'var(--color-danger)' : item.status === 'DUE_SOON' ? 'var(--color-warning)' : 'var(--color-success)'}`,
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.title}</span>
                      <span className={`badge ${item.item_type === 'LEGAL' ? 'badge-danger' : 'badge-info'}`} style={{ fontSize: '0.6rem' }}>{item.item_type === 'LEGAL' ? 'Legal' : 'BP'}</span>
                      {item.document && <span style={{ fontSize: '0.7rem', color: 'var(--color-success)' }}>✓ cert</span>}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                      {item.category} · {(item.frequency_type || '').replace(/_/g, ' ')} {item.regulatory_ref ? `· ${item.regulatory_ref}` : ''}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: item.status === 'OVERDUE' ? 'var(--color-danger)' : item.status === 'DUE_SOON' ? 'var(--color-warning)' : 'var(--color-success)' }}>
                      {(item.status || '').replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{fmtDate(item.next_due_date)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ CALENDAR ═══════ */}
      {tab === 'calendar' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <button className="btn btn-sm" onClick={() => { if (calMonth === 1) { setCalMonth(12); setCalYear(calYear - 1) } else setCalMonth(calMonth - 1) }}>← Prev</button>
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{MONTHS[calMonth - 1]} {calYear}</h2>
            <button className="btn btn-sm" onClick={() => { if (calMonth === 12) { setCalMonth(1); setCalYear(calYear + 1) } else setCalMonth(calMonth + 1) }}>Next →</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, borderRadius: 8, overflow: 'hidden' }}>
            {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d => (
              <div key={d} style={{ padding: '0.4rem', textAlign: 'center', fontWeight: 700, fontSize: '0.75rem', background: 'var(--color-bg-alt, #f1f5f9)', color: 'var(--color-text-muted)' }}>{d}</div>
            ))}
            {buildCalGrid(calYear, calMonth).flat().map((day, i) => {
              if (day === null) return <div key={`e${i}`} style={{ padding: '0.4rem', background: '#fafafa', minHeight: 56 }} />
              const dateStr = `${calYear}-${String(calMonth).padStart(2,'0')}-${String(day).padStart(2,'0')}`
              const dayItems = calDays[dateStr] || []
              const hasRed = dayItems.some((x: any) => x.colour === 'red')
              const hasAmber = dayItems.some((x: any) => x.colour === 'amber')
              const isToday = dateStr === new Date().toISOString().split('T')[0]
              const isSel = dateStr === selectedDay
              return (
                <div key={dateStr} onClick={() => setSelectedDay(isSel ? null : dateStr)} style={{
                  padding: '0.35rem', background: isSel ? '#eff6ff' : '#fff', minHeight: 56,
                  cursor: dayItems.length > 0 ? 'pointer' : 'default',
                  borderTop: isToday ? '3px solid var(--color-primary)' : undefined,
                  border: hasRed ? '2px solid var(--color-danger)' : isSel ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: isToday ? 700 : 400, marginBottom: 2 }}>{day}</div>
                  <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                    {dayItems.map((item: any, idx: number) => (
                      <span key={idx} style={{ width: 7, height: 7, borderRadius: '50%', background: item.colour === 'red' ? 'var(--color-danger)' : item.colour === 'amber' ? 'var(--color-warning)' : 'var(--color-success)', display: 'inline-block' }} />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ marginTop: '0.5rem', display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            {[{ l: 'Overdue', c: 'var(--color-danger)' }, { l: 'Due soon', c: 'var(--color-warning)' }, { l: 'Compliant', c: 'var(--color-success)' }].map(x => (
              <div key={x.l} style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: x.c, display: 'inline-block' }} />{x.l}</div>
            ))}
          </div>
          {selectedDay && calDays[selectedDay] && (
            <div style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginTop: '1rem' }}>
              <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem' }}>Items due {fmtDate(selectedDay)}</h3>
              {calDays[selectedDay].map((item: any) => (
                <div key={item.id} onClick={() => { const full = items.find(i => i.id === item.id); if (full) setCompleteModal(full) }} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.4rem 0', borderBottom: '1px solid var(--color-border)', cursor: 'pointer',
                }}>
                  <div><span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{item.title}</span> <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{item.category}</span></div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span className={`badge ${item.item_type === 'LEGAL' ? 'badge-danger' : 'badge-info'}`} style={{ fontSize: '0.6rem' }}>{item.item_type === 'LEGAL' ? 'Legal' : 'BP'}</span>
                    <span className={`badge ${item.status === 'OVERDUE' ? 'badge-danger' : item.status === 'DUE_SOON' ? 'badge-warning' : 'badge-success'}`} style={{ fontSize: '0.6rem' }}>{item.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ INCIDENTS ═══════ */}
      {tab === 'incidents' && (
        <div>
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {[{ l: 'All', v: '' }, { l: 'Open', v: 'OPEN' }, { l: 'Investigating', v: 'INVESTIGATING' }, { l: 'Resolved', v: 'RESOLVED' }, { l: 'RIDDOR', v: 'riddor' }].map(f => (
              <button key={f.v} className={`filter-pill ${incFilter === f.v ? 'active' : ''}`} onClick={() => setIncFilter(f.v)}>{f.l}</button>
            ))}
            <div style={{ marginLeft: 'auto' }}><button className="btn btn-primary" onClick={() => setShowAddInc(!showAddInc)}>{showAddInc ? 'Cancel' : '+ Report Incident'}</button></div>
          </div>
          {showAddInc && (
            <form onSubmit={handleAddIncident} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Title *</label><input className="form-input" name="title" required /></div>
                <div><label className="form-label">Location</label><input className="form-input" name="location" /></div>
                <div><label className="form-label">Severity</label><select className="form-input" name="severity"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR Reportable</label></div>
                <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Description *</label><textarea className="form-input" name="description" required rows={3} /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Submit</button></div>
            </form>
          )}
          {incFiltered.length === 0 ? (
            <div className="empty-cta"><div className="empty-cta-title">No incidents</div><div className="empty-cta-desc">Report incidents as they happen.</div></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Incident</th><th>Severity</th><th>RIDDOR</th><th>Date</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {incFiltered.map(inc => (
                    <tr key={inc.id}>
                      <td><div style={{ fontWeight: 600 }}>{inc.title}</div>{inc.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{inc.location}</div>}</td>
                      <td><span className={`badge ${inc.severity === 'HIGH' || inc.severity === 'CRITICAL' ? 'badge-danger' : inc.severity === 'MEDIUM' ? 'badge-warning' : 'badge-info'}`}>{inc.severity}</span></td>
                      <td>{inc.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)' }}>No</span>}</td>
                      <td style={{ fontSize: '0.85rem' }}>{inc.incident_date ? new Date(inc.incident_date).toLocaleDateString() : '—'}</td>
                      <td><span className={`badge ${inc.status === 'OPEN' ? 'badge-danger' : inc.status === 'INVESTIGATING' ? 'badge-warning' : 'badge-success'}`}>{inc.status}</span></td>
                      <td>{(inc.status === 'OPEN' || inc.status === 'INVESTIGATING') && <button className="btn btn-sm" onClick={() => updateIncidentStatus(inc.id, 'RESOLVED').then(loadCore)}>Resolve</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ ACCIDENTS ═══════ */}
      {tab === 'accidents' && (
        <div>
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={() => setShowAddAcc(!showAddAcc)}>{showAddAcc ? 'Cancel' : '+ Log Accident'}</button>
            <span style={{ width: 1, height: 18, background: 'var(--color-border)', margin: '0 4px' }} />
            {[{ l: 'All', v: '' }, { l: 'Open', v: 'OPEN' }, { l: 'Investigating', v: 'INVESTIGATING' }, { l: 'Closed', v: 'CLOSED' }].map(f => (
              <button key={f.v} className={`filter-pill ${accStatusFilter === f.v ? 'active' : ''}`} onClick={() => setAccStatusFilter(f.v)}>{f.l}</button>
            ))}
            <span style={{ width: 1, height: 18, background: 'var(--color-border)', margin: '0 4px' }} />
            {[{ l: 'All Severity', v: '' }, { l: 'Minor', v: 'MINOR' }, { l: 'Moderate', v: 'MODERATE' }, { l: 'Major', v: 'MAJOR' }].map(f => (
              <button key={f.v} className={`filter-pill ${accSevFilter === f.v ? 'active' : ''}`} onClick={() => setAccSevFilter(f.v)}>{f.l}</button>
            ))}
            <button className={`filter-pill ${accRiddorFilter ? 'active' : ''}`} onClick={() => setAccRiddorFilter(!accRiddorFilter)}
              style={accRiddorFilter ? { background: 'var(--color-danger)', color: '#fff', borderColor: 'var(--color-danger)' } : {}}>
              {accRiddorFilter ? '✓ RIDDOR' : 'RIDDOR'}
            </button>
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
                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end', paddingBottom: 4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR</label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}><input type="checkbox" name="follow_up" /> Follow-up needed</label>
                </div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Log Accident</button></div>
            </form>
          )}

          {accFiltered.length === 0 ? (
            <div className="empty-cta"><div className="empty-cta-title">No accidents match</div><div className="empty-cta-desc">Adjust filters or log a new accident.</div></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {accFiltered.map((a: any) => {
                const days = a.riddor_reportable && !a.riddor_reported_date ? riddorDaysLeft(a.date) : null
                return (
                  <div key={a.id} style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '0.75rem 1rem', borderLeft: `4px solid ${a.severity === 'MAJOR' || a.severity === 'FATAL' ? 'var(--color-danger)' : a.severity === 'MODERATE' ? 'var(--color-warning)' : 'var(--color-primary)'}` }}>
                    {a.riddor_reportable && (
                      <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: '0.4rem 0.75rem', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--color-danger)', fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>RIDDOR Reporting Required</span>
                        {days !== null && days > 0 && <span style={{ padding: '2px 8px', borderRadius: 999, background: 'var(--color-danger)', color: '#fff', fontSize: '0.7rem', fontWeight: 700 }}>{days} days left</span>}
                        {days !== null && days <= 0 && <span style={{ padding: '2px 8px', borderRadius: 999, background: 'var(--color-danger)', color: '#fff', fontSize: '0.7rem', fontWeight: 700 }}>OVERDUE</span>}
                        {a.hse_reference && <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Ref: {a.hse_reference}</span>}
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 2 }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{a.person_involved}</span>
                          {a.person_role && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>({a.person_role})</span>}
                          <span className={`badge ${a.severity === 'MAJOR' || a.severity === 'FATAL' ? 'badge-danger' : a.severity === 'MODERATE' ? 'badge-warning' : 'badge-info'}`}>{a.severity}</span>
                          <span className={`badge ${a.status === 'CLOSED' ? 'badge-success' : a.status === 'OPEN' ? 'badge-danger' : 'badge-warning'}`}>{a.status}</span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{(a.description || '').substring(0, 120)}{(a.description || '').length > 120 ? '…' : ''}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{fmtDate(a.date)} {a.time || ''} {a.location ? `· ${a.location}` : ''}</div>
                        {a.follow_up_required && !a.follow_up_completed && <div style={{ fontSize: '0.75rem', color: 'var(--color-warning)', fontWeight: 600, marginTop: 4 }}>Follow-up required</div>}
                      </div>
                      {a.status !== 'CLOSED' && (
                        <select defaultValue="" onChange={e => { if (e.target.value) handleAccidentStatus(a.id, e.target.value); e.target.value = '' }}
                          className="form-input" style={{ width: 'auto', fontSize: '0.8rem', padding: '0.3rem 0.5rem' }}>
                          <option value="" disabled>Update…</option>
                          <option value="INVESTIGATING">Investigating</option>
                          <option value="FOLLOW_UP">Follow-up</option>
                          <option value="CLOSED">Close</option>
                        </select>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--color-text-muted)', padding: '0.75rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 8 }}>
            <strong>RIDDOR:</strong> Reporting of Injuries, Diseases and Dangerous Occurrences Regulations 2013. Certain accidents must be reported to HSE within 10 days.
          </div>
        </div>
      )}

      {/* ═══════ DOCUMENTS ═══════ */}
      {tab === 'documents' && (
        <div>
          {allDocs.length === 0 ? (
            <div className="empty-cta"><div className="empty-cta-title">No documents</div><div className="empty-cta-desc">Policies, certificates, insurance documents and RAMS will appear here.</div></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
              {allDocs.map(doc => (
                <div key={doc.id} style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{doc.title}</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
                    <span className={`badge ${doc.is_expired ? 'badge-danger' : 'badge-success'}`}>{doc.is_expired ? 'Expired' : 'Current'}</span>
                    <span className="badge badge-neutral">{(doc.document_type || '').replace(/_/g, ' ')}</span>
                  </div>
                  {doc.expiry_date && <div style={{ fontSize: '0.8rem', color: doc.is_expired ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>{doc.is_expired ? 'Expired' : 'Expires'}: {doc.expiry_date}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ AUDIT TRAIL ═══════ */}
      {tab === 'audit' && (
        <div>
          {auditLog.length === 0 ? (
            <div className="empty-cta"><div className="empty-cta-title">No audit entries</div><div className="empty-cta-desc">Score changes will appear here as compliance items are updated.</div></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              {auditLog.map((log: any, i: number) => {
                const scoreColor = log.score >= 80 ? 'var(--color-success)' : log.score >= 60 ? 'var(--color-warning)' : 'var(--color-danger)'
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0.75rem', background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8 }}>
                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.85rem', color: scoreColor, flexShrink: 0, border: `2px solid ${scoreColor}` }}>{log.score}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                        {log.score}%
                        <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', fontWeight: 700, color: log.change > 0 ? 'var(--color-success)' : log.change < 0 ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>
                          {log.change > 0 ? `+${log.change}%` : log.change < 0 ? `${log.change}%` : '—'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{new Date(log.calculated_at).toLocaleString('en-GB')} · {log.trigger}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.7rem', color: 'var(--color-text-muted)', flexShrink: 0 }}>
                      <span style={{ color: 'var(--color-success)' }}>{log.compliant_count} ✓</span>
                      <span style={{ color: log.overdue_count > 0 ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>{log.overdue_count} !</span>
                      <span>{log.total_items} total</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)', padding: '0.5rem 1.25rem', borderRadius: 6, backgroundColor: '#111827', color: '#fff', fontSize: '0.82rem', fontWeight: 500, zIndex: 1001 }}>
          {toast}
        </div>
      )}
    </div>
  )
}
