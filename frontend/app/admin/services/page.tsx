'use client'

import { useEffect, useState } from 'react'
import { getServices, createService, updateService, deleteService, getBookableStaff } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }
function penceToPounds(pence: number) { return (pence / 100).toFixed(2) }
function poundsToPence(pounds: string) { return Math.round(parseFloat(pounds || '0') * 100) }

function depositDisplay(s: any) {
  if (s.deposit_percentage && s.deposit_percentage > 0) return `${s.deposit_percentage}%`
  if (s.deposit_pence && s.deposit_pence > 0) return formatPrice(s.deposit_pence)
  return '—'
}

const emptyService = {
  name: '', description: '', category: '', duration_minutes: 60,
  colour: '', sort_order: 0, is_active: true,
}

export default function AdminServicesPage() {
  const [services, setServices] = useState<any[]>([])
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<any>({ ...emptyService })
  const [depositMode, setDepositMode] = useState<'fixed' | 'percent'>('fixed')
  const [priceInput, setPriceInput] = useState('')
  const [depositInput, setDepositInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'active' | 'inactive' | 'all'>('active')
  const [allStaff, setAllStaff] = useState<any[]>([])
  const [selectedStaffIds, setSelectedStaffIds] = useState<number[]>([])

  const loadServices = () => {
    getServices({ all: true }).then(r => { setServices(r.data || []); setLoading(false) })
  }

  useEffect(() => {
    loadServices()
    getBookableStaff().then(r => setAllStaff(r.data || []))
  }, [])

  const activeServices = services.filter(s => s.is_active)
  const inactiveServices = services.filter(s => !s.is_active)
  const serviceCategories = Array.from(new Set(services.map((s: any) => s.category).filter(Boolean)))
  const filteredServices = filter === 'active' ? activeServices : filter === 'inactive' ? inactiveServices : services

  function openAdd() {
    setForm({ ...emptyService })
    setPriceInput('')
    setDepositInput('')
    setDepositMode('fixed')
    setSelectedStaffIds([])
    setEditingId(null)
    setError('')
    setShowModal(true)
  }

  function openEdit(s: any) {
    setForm({
      name: s.name || '',
      description: s.description || '',
      category: s.category || '',
      duration_minutes: s.duration_minutes || 60,
      colour: s.colour || '',
      sort_order: s.sort_order || 0,
      is_active: s.is_active ?? true,
    })
    setPriceInput(penceToPounds(s.price_pence || 0))
    if (s.deposit_percentage && s.deposit_percentage > 0) {
      setDepositMode('percent')
      setDepositInput(String(s.deposit_percentage))
    } else {
      setDepositMode('fixed')
      setDepositInput(penceToPounds(s.deposit_pence || 0))
    }
    setSelectedStaffIds(s.staff_ids || [])
    setEditingId(s.id)
    setError('')
    setShowModal(true)
  }

  async function handleSave() {
    setError('')
    if (!form.name.trim()) { setError('Service name is required.'); return }
    if (!form.duration_minutes || form.duration_minutes < 1) { setError('Duration must be at least 1 minute.'); return }

    setSaving(true)
    const payload: any = {
      name: form.name,
      description: form.description,
      category: form.category,
      duration_minutes: form.duration_minutes,
      price_pence: poundsToPence(priceInput),
      colour: form.colour,
      is_active: form.is_active,
      sort_order: form.sort_order,
    }
    if (depositMode === 'percent') {
      payload.deposit_percentage = parseInt(depositInput || '0', 10)
      payload.deposit_pence = 0
    } else {
      payload.deposit_pence = poundsToPence(depositInput)
      payload.deposit_percentage = 0
    }
    payload.staff_ids = selectedStaffIds

    let res
    if (editingId) {
      res = await updateService(editingId, payload)
    } else {
      res = await createService(payload)
    }
    setSaving(false)
    if (res.error) { setError(res.error); return }
    setShowModal(false)
    loadServices()
  }

  async function toggleActive(id: number, currentlyActive: boolean) {
    const res = await updateService(id, { is_active: !currentlyActive })
    if (res.data) {
      setServices(prev => prev.map(s => s.id === id ? res.data : s))
    }
  }

  async function handleDelete(s: any) {
    if (!confirm(`Delete "${s.name}"? This cannot be undone. If the service has bookings, it will fail — disable it instead.`)) return
    const res = await deleteService(s.id)
    if (res.error) { alert(res.error); return }
    loadServices()
  }

  if (loading) return <div className="empty-state">Loading services…</div>

  return (
    <div>
      <div className="page-header"><h1>Services & Pricing</h1></div>
      <p className="staff-header-sub">What you offer, how long it takes, what it costs.</p>

      {/* Status strip */}
      <div className="status-strip">
        <div className="status-strip-item"><span className="status-strip-num">{activeServices.length}</span><span className="status-strip-label">Active</span></div>
        <div className="status-strip-item"><span className="status-strip-num">{inactiveServices.length}</span><span className="status-strip-label">Inactive</span></div>
        <div className="status-strip-item"><span className="status-strip-num">{services.length}</span><span className="status-strip-label">Total</span></div>
      </div>

      {/* Subheader */}
      <div className="tab-subheader">
        <div className="tab-subheader-left">
          <div className="filter-pills">
            <button className={`filter-pill ${filter === 'active' ? 'active' : ''}`} onClick={() => setFilter('active')}>Active ({activeServices.length})</button>
            <button className={`filter-pill ${filter === 'inactive' ? 'active' : ''}`} onClick={() => setFilter('inactive')}>Inactive ({inactiveServices.length})</button>
            <button className={`filter-pill ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All ({services.length})</button>
          </div>
        </div>
        <div className="tab-subheader-right">
          <button className="btn btn-primary" onClick={openAdd}>+ Add Service</button>
        </div>
      </div>

      {filteredServices.length === 0 ? (
        <div className="empty-cta">
          <div className="empty-cta-title">{filter === 'active' ? 'No active services' : filter === 'inactive' ? 'No inactive services' : 'No services yet'}</div>
          <div className="empty-cta-desc">Add your first service to start taking bookings. Include the name, duration, price, and any deposit required.</div>
          <button className="btn btn-primary" onClick={openAdd}>+ Add Service</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Service</th><th>Category</th><th>Duration</th><th>Price</th><th>Deposit</th><th>Staff</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {filteredServices.map(s => (
                <tr key={s.id} style={!s.is_active ? { opacity: 0.55 } : undefined}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {s.colour && <span style={{ width: 10, height: 10, borderRadius: '50%', background: s.colour, flexShrink: 0 }} />}
                      <div>
                        <div style={{ fontWeight: 600 }}>{s.name}</div>
                        {s.description && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.description}</div>}
                      </div>
                    </div>
                  </td>
                  <td>{s.category || '—'}</td>
                  <td>{s.duration_minutes} min</td>
                  <td style={{ fontWeight: 600 }}>{formatPrice(s.price_pence)}</td>
                  <td>{depositDisplay(s)}</td>
                  <td style={{ maxWidth: 180 }}>
                    {(s.staff_ids || []).length > 0
                      ? allStaff.filter((st: any) => s.staff_ids?.includes(st.id)).map((st: any) => st.name).join(', ') || `${s.staff_ids.length} assigned`
                      : <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>None</span>}
                  </td>
                  <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="btn btn-sm" onClick={() => openEdit(s)} style={{ marginRight: 6 }}>Edit</button>
                    <button className="btn btn-sm" onClick={() => toggleActive(s.id, s.is_active)} style={{ marginRight: 6 }}>{s.is_active ? 'Disable' : 'Enable'}</button>
                    {!s.is_active && <button className="btn btn-sm btn-danger" onClick={() => handleDelete(s)}>Delete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit Service Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <h2 style={{ marginBottom: 16 }}>{editingId ? 'Edit Service' : 'Add Service'}</h2>
            {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{error}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div>
                <label className="form-label">Service Name *</label>
                <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Cut & Style" />
              </div>
              <div>
                <label className="form-label">Description</label>
                <textarea className="form-input" rows={2} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Brief description shown to customers" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Category</label>
                  <input className="form-input" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} placeholder="e.g. Cuts, Colour, Wellness" list="svc-cat-list" />
                  <datalist id="svc-cat-list">{serviceCategories.map((c: string) => <option key={c} value={c} />)}</datalist>
                </div>
                <div>
                  <label className="form-label">Duration (minutes) *</label>
                  <input className="form-input" type="number" min={1} value={form.duration_minutes} onChange={e => setForm({ ...form, duration_minutes: +e.target.value })} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Price (£)</label>
                  <input className="form-input" type="number" step="0.01" min="0" value={priceInput} onChange={e => setPriceInput(e.target.value)} placeholder="0.00" />
                </div>
                <div>
                  <label className="form-label">Colour</label>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <input className="form-input" value={form.colour} onChange={e => setForm({ ...form, colour: e.target.value })} placeholder="#2563eb" style={{ flex: 1 }} />
                    {form.colour && <span style={{ width: 24, height: 24, borderRadius: 4, background: form.colour, border: '1px solid var(--color-border)', flexShrink: 0 }} />}
                  </div>
                </div>
              </div>
              <div>
                <label className="form-label" style={{ marginBottom: 6 }}>Deposit</label>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <button type="button" className={`filter-pill ${depositMode === 'fixed' ? 'active' : ''}`} onClick={() => setDepositMode('fixed')}>£ Fixed</button>
                  <button type="button" className={`filter-pill ${depositMode === 'percent' ? 'active' : ''}`} onClick={() => setDepositMode('percent')}>% Percentage</button>
                </div>
                {depositMode === 'fixed' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 600 }}>£</span>
                    <input className="form-input" type="number" step="0.01" min="0" value={depositInput} onChange={e => setDepositInput(e.target.value)} placeholder="0.00" style={{ flex: 1 }} />
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input className="form-input" type="number" min="0" max="100" value={depositInput} onChange={e => setDepositInput(e.target.value)} placeholder="50" style={{ flex: 1 }} />
                    <span style={{ fontWeight: 600 }}>%</span>
                    {priceInput && depositInput && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        = {formatPrice(Math.round(poundsToPence(priceInput) * parseInt(depositInput || '0', 10) / 100))}
                      </span>
                    )}
                  </div>
                )}
                {depositMode === 'fixed' && priceInput && depositInput && poundsToPence(priceInput) > 0 && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    = {Math.round(poundsToPence(depositInput) / poundsToPence(priceInput) * 100)}% of price
                  </div>
                )}
              </div>
              <div>
                <label className="form-label">Assigned Staff</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '8px 0' }}>
                  {allStaff.length === 0 && <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>No staff found</span>}
                  {allStaff.map((st: any) => (
                    <label key={st.id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.9rem', cursor: 'pointer', padding: '4px 10px', borderRadius: 6, border: '1px solid var(--color-border)', background: selectedStaffIds.includes(st.id) ? 'var(--color-primary-light, #e0e7ff)' : 'transparent' }}>
                      <input type="checkbox" checked={selectedStaffIds.includes(st.id)} onChange={e => {
                        if (e.target.checked) setSelectedStaffIds(prev => [...prev, st.id])
                        else setSelectedStaffIds(prev => prev.filter(id => id !== st.id))
                      }} />
                      {st.name}
                    </label>
                  ))}
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Sort Order</label>
                  <input className="form-input" type="number" value={form.sort_order} onChange={e => setForm({ ...form, sort_order: +e.target.value })} />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />
                    Active (visible to customers)
                  </label>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving…' : editingId ? 'Save Changes' : 'Add Service'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
