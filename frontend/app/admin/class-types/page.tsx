'use client'

import { useState, useEffect } from 'react'
import { getClassTypes, createClassType, updateClassType, deleteClassType } from '@/lib/api'

const DIFFICULTIES = ['all', 'beginner', 'intermediate', 'advanced']
const CATEGORIES = ['Cardio', 'Strength', 'Mind & Body', 'Flexibility', 'Dance', 'Aqua', '']

export default function ClassTypesAdmin() {
  const [classTypes, setClassTypes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<any>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', category: '', duration_minutes: 45, difficulty: 'all', max_capacity: 20, colour: '#ef4444', price_pence: 0 })
  const [priceInput, setPriceInput] = useState('0')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    const res = await getClassTypes()
    setClassTypes(res.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function openNew() {
    setEditing(null)
    setForm({ name: '', description: '', category: '', duration_minutes: 45, difficulty: 'all', max_capacity: 20, colour: '#ef4444', price_pence: 0 })
    setPriceInput('0')
    setShowForm(true)
    setError('')
  }

  function openEdit(ct: any) {
    setEditing(ct)
    setForm({
      name: ct.name, description: ct.description || '', category: ct.category || '',
      duration_minutes: ct.duration_minutes, difficulty: ct.difficulty,
      max_capacity: ct.max_capacity, colour: ct.colour || '#ef4444',
      price_pence: ct.price_pence || 0,
    })
    setPriceInput(((ct.price_pence || 0) / 100).toFixed(2))
    setShowForm(true)
    setError('')
  }

  async function handleSave() {
    if (!form.name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    const payload = { ...form, price_pence: Math.round(parseFloat(priceInput || '0') * 100) }
    const res = editing
      ? await updateClassType(editing.id, payload)
      : await createClassType(payload)
    setSaving(false)
    if (res.error) { setError(res.error); return }
    setShowForm(false)
    load()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this class type?')) return
    await deleteClassType(id)
    load()
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Class Types</h1>
        <button onClick={openNew} className="btn btn-primary">+ Add Class Type</button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>{editing ? 'Edit Class Type' : 'New Class Type'}</h2>
          {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. HIIT, Yoga Flow"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Description</label>
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} placeholder="Brief description"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem', resize: 'vertical' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Category</label>
              <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c || '(none)'}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Difficulty</label>
              <select value={form.difficulty} onChange={e => setForm({ ...form, difficulty: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                {DIFFICULTIES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Duration (mins)</label>
              <input type="number" min={5} value={form.duration_minutes} onChange={e => setForm({ ...form, duration_minutes: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Max Capacity</label>
              <input type="number" min={1} value={form.max_capacity} onChange={e => setForm({ ...form, max_capacity: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Price (£, 0 = included)</label>
              <input type="number" min={0} step="0.01" value={priceInput} onChange={e => setPriceInput(e.target.value)} placeholder="0.00"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Colour</label>
              <input type="color" value={form.colour} onChange={e => setForm({ ...form, colour: e.target.value })}
                style={{ width: 48, height: 36, border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer' }} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button onClick={handleSave} disabled={saving} className="btn btn-primary">{saving ? 'Saving...' : 'Save'}</button>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <p style={{ color: '#6b7280' }}>Loading class types...</p>
      ) : classTypes.length === 0 ? (
        <p style={{ color: '#6b7280' }}>No class types configured yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          {classTypes.map((ct: any) => (
            <div key={ct.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '0.85rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                {ct.colour && <div style={{ width: 4, height: 36, borderRadius: 2, background: ct.colour }} />}
                <div>
                  <strong>{ct.name}</strong>
                  <span style={{ color: '#6b7280', fontSize: '0.85rem', marginLeft: '0.75rem' }}>
                    {ct.duration_minutes}min · {ct.difficulty} · max {ct.max_capacity}
                    {ct.category && ` · ${ct.category}`}
                    {ct.price_pence > 0 && ` · £${(ct.price_pence / 100).toFixed(2)}`}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button onClick={() => openEdit(ct)} className="btn btn-ghost" style={{ fontSize: '0.82rem' }}>Edit</button>
                <button onClick={() => handleDelete(ct.id)} className="btn btn-ghost" style={{ fontSize: '0.82rem', color: '#dc2626' }}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
