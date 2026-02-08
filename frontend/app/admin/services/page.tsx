'use client'

import { useEffect, useState } from 'react'
import { getServices } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function AdminServicesPage() {
  const [services, setServices] = useState<any[]>([])
  const [editing, setEditing] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading services…</div>

  function toggleActive(id: number) {
    setServices(prev => prev.map(s => s.id === id ? { ...s, active: !s.active } : s))
  }

  function saveEdit() {
    if (!editing) return
    setServices(prev => prev.map(s => s.id === editing.id ? editing : s))
    setEditing(null)
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
                <td>{s.deposit_pence > 0 ? formatPrice(s.deposit_pence) : '—'}</td>
                <td><span className={`badge ${s.active ? 'badge-success' : 'badge-neutral'}`}>{s.active ? 'Active' : 'Inactive'}</span></td>
                <td className="actions-row">
                  <button className="btn btn-outline btn-sm" onClick={() => setEditing({ ...s })}>Edit</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => toggleActive(s.id)}>{s.active ? 'Disable' : 'Enable'}</button>
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                <div><label>Duration (min)</label><input type="number" value={editing.duration_minutes} onChange={e => setEditing({ ...editing, duration_minutes: +e.target.value })} /></div>
                <div><label>Price (pence)</label><input type="number" value={editing.price_pence} onChange={e => setEditing({ ...editing, price_pence: +e.target.value })} /></div>
                <div><label>Deposit (pence)</label><input type="number" value={editing.deposit_pence} onChange={e => setEditing({ ...editing, deposit_pence: +e.target.value })} /></div>
              </div>
              <div className="actions-row" style={{ justifyContent: 'flex-end' }}>
                <button className="btn btn-outline" onClick={() => setEditing(null)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveEdit}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
