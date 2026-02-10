'use client'

import { useEffect, useState } from 'react'
import { getServices, updateService } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }
function penceToPounds(pence: number) { return (pence / 100).toFixed(2) }
function poundsToPence(pounds: string) { return Math.round(parseFloat(pounds || '0') * 100) }

function depositDisplay(s: any) {
  if (s.deposit_percentage && s.deposit_percentage > 0) return `${s.deposit_percentage}%`
  if (s.deposit_pence && s.deposit_pence > 0) return formatPrice(s.deposit_pence)
  return '—'
}

export default function AdminServicesPage() {
  const [services, setServices] = useState<any[]>([])
  const [editing, setEditing] = useState<any | null>(null)
  const [depositMode, setDepositMode] = useState<'fixed' | 'percent'>('fixed')
  const [priceInput, setPriceInput] = useState('')
  const [depositInput, setDepositInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading services…</div>

  function openEdit(s: any) {
    setEditing({ ...s })
    setPriceInput(penceToPounds(s.price_pence))
    if (s.deposit_percentage && s.deposit_percentage > 0) {
      setDepositMode('percent')
      setDepositInput(String(s.deposit_percentage))
    } else {
      setDepositMode('fixed')
      setDepositInput(penceToPounds(s.deposit_pence || 0))
    }
  }

  async function saveEdit() {
    if (!editing) return
    setSaving(true)
    const payload: any = {
      name: editing.name,
      description: editing.description,
      category: editing.category,
      duration_minutes: editing.duration_minutes,
      price_pence: poundsToPence(priceInput),
      colour: editing.colour,
      is_active: editing.is_active,
      sort_order: editing.sort_order,
    }
    if (depositMode === 'percent') {
      payload.deposit_percentage = parseInt(depositInput || '0', 10)
      payload.deposit_pence = 0
    } else {
      payload.deposit_pence = poundsToPence(depositInput)
      payload.deposit_percentage = 0
    }
    const res = await updateService(editing.id, payload)
    setSaving(false)
    if (res.data) {
      setServices(prev => prev.map(s => s.id === editing.id ? res.data : s))
      setEditing(null)
    }
  }

  async function toggleActive(id: number, currentlyActive: boolean) {
    const res = await updateService(id, { is_active: !currentlyActive })
    if (res.data) {
      setServices(prev => prev.map(s => s.id === id ? res.data : s))
    }
  }

  return (
    <div>
      <div className="page-header"><h1>Services & Pricing</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Service</th><th>Category</th><th>Duration</th><th>Price</th><th>Deposit</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {services.map(s => (
              <tr key={s.id}>
                <td><div style={{ fontWeight: 600 }}>{s.name}</div><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{s.description}</div></td>
                <td>{s.category}</td>
                <td>{s.duration_minutes} min</td>
                <td style={{ fontWeight: 600 }}>{formatPrice(s.price_pence)}</td>
                <td>{depositDisplay(s)}</td>
                <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                <td className="actions-row">
                  <button className="btn btn-outline btn-sm" onClick={() => openEdit(s)}>Edit</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => toggleActive(s.id, s.is_active)}>{s.is_active ? 'Disable' : 'Enable'}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: '1rem' }}>Edit Service</h2>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div><label>Name</label><input value={editing.name} onChange={e => setEditing({ ...editing, name: e.target.value })} /></div>
              <div><label>Description</label><textarea rows={2} value={editing.description} onChange={e => setEditing({ ...editing, description: e.target.value })} /></div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div><label>Duration (min)</label><input type="number" value={editing.duration_minutes} onChange={e => setEditing({ ...editing, duration_minutes: +e.target.value })} /></div>
                <div><label>Price (£)</label><input type="number" step="0.01" min="0" value={priceInput} onChange={e => setPriceInput(e.target.value)} placeholder="0.00" /></div>
              </div>
              <div>
                <label style={{ marginBottom: 6, display: 'block' }}>Deposit</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <button type="button" className={`btn btn-sm ${depositMode === 'fixed' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setDepositMode('fixed')}>£ Fixed</button>
                  <button type="button" className={`btn btn-sm ${depositMode === 'percent' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setDepositMode('percent')}>% Percentage</button>
                </div>
                {depositMode === 'fixed' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 600 }}>£</span>
                    <input type="number" step="0.01" min="0" value={depositInput} onChange={e => setDepositInput(e.target.value)} placeholder="0.00" style={{ flex: 1 }} />
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input type="number" min="0" max="100" value={depositInput} onChange={e => setDepositInput(e.target.value)} placeholder="50" style={{ flex: 1 }} />
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
              <div className="actions-row" style={{ justifyContent: 'flex-end' }}>
                <button className="btn btn-outline" onClick={() => setEditing(null)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveEdit} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
