'use client'

import { useEffect, useState } from 'react'
import { getStaffList, getShifts, getLeaveRequests, getTrainingRecords, createStaff, updateStaff, deleteStaff } from '@/lib/api'

interface StaffForm {
  first_name: string
  last_name: string
  email: string
  phone: string
  role: string
}

const emptyForm: StaffForm = { first_name: '', last_name: '', email: '', phone: '', role: 'staff' }

export default function AdminStaffPage() {
  const [tab, setTab] = useState<'profiles' | 'shifts' | 'leave' | 'training'>('profiles')
  const [staff, setStaff] = useState<any[]>([])
  const [shifts, setShifts] = useState<any[]>([])
  const [leave, setLeave] = useState<any[]>([])
  const [training, setTraining] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const [showAddModal, setShowAddModal] = useState(false)
  const [editingStaff, setEditingStaff] = useState<any | null>(null)
  const [form, setForm] = useState<StaffForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [createdCreds, setCreatedCreds] = useState<{ name: string; username: string; email: string; temp_password: string } | null>(null)

  const loadData = () => {
    setLoading(true)
    Promise.all([getStaffList(), getShifts(), getLeaveRequests(), getTrainingRecords()]).then(([s, sh, lv, tr]) => {
      setStaff(s.data || [])
      setShifts(sh.data || [])
      setLeave(lv.data || [])
      setTraining(tr.data || [])
      setLoading(false)
    })
  }

  useEffect(() => { loadData() }, [])

  const openAdd = () => {
    setForm(emptyForm)
    setError('')
    setEditingStaff(null)
    setShowAddModal(true)
  }

  const openEdit = (s: any) => {
    const nameParts = (s.display_name || '').split(' ')
    setForm({
      first_name: nameParts[0] || '',
      last_name: nameParts.slice(1).join(' ') || '',
      email: s.email || '',
      phone: s.phone || '',
      role: s.role || 'staff',
    })
    setError('')
    setEditingStaff(s)
    setShowAddModal(true)
  }

  const handleAuthError = (res: { error: string | null; status: number }) => {
    if (res.status === 401 || res.error?.toLowerCase().includes('inactive') || res.error?.toLowerCase().includes('expired')) {
      window.location.href = '/login'
      return true
    }
    return false
  }

  const handleSave = async () => {
    setError('')
    if (!form.first_name.trim() || !form.last_name.trim()) { setError('First and last name are required.'); return }
    if (!form.email.trim()) { setError('Email is required.'); return }
    setSaving(true)
    if (editingStaff) {
      const res = await updateStaff(editingStaff.id, form)
      if (res.error) { if (handleAuthError(res)) return; setError(res.error); setSaving(false); return }
    } else {
      const res = await createStaff(form)
      if (res.error) { if (handleAuthError(res)) return; setError(res.error); setSaving(false); return }
      // Show temp credentials to admin
      if (res.data) {
        setCreatedCreds({
          name: `${form.first_name} ${form.last_name}`,
          username: res.data.username || form.email.split('@')[0],
          email: form.email,
          temp_password: res.data.temp_password || '',
        })
      }
    }
    setSaving(false)
    setShowAddModal(false)
    loadData()
  }

  const handleDelete = async (s: any) => {
    if (!confirm(`Deactivate ${s.display_name}? They will no longer be able to log in.`)) return
    const res = await deleteStaff(s.id)
    if (res.error) { alert(res.error); return }
    loadData()
  }

  if (loading) return <div className="empty-state">Loading staff data…</div>

  return (
    <div>
      <div className="page-header"><h1>Staff Management</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="tabs">
        {(['profiles', 'shifts', 'leave', 'training'] as const).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>{t.charAt(0).toUpperCase() + t.slice(1)}</button>
        ))}
      </div>

      {tab === 'profiles' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-primary" onClick={openAdd}>+ Add Staff Member</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Role</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {staff.map((s: any) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.display_name}</td>
                    <td>{s.role}</td>
                    <td>{s.email}</td>
                    <td>{s.phone || '—'}</td>
                    <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>
                      <button className="btn btn-sm" onClick={() => openEdit(s)} style={{ marginRight: 8 }}>Edit</button>
                      {s.is_active && <button className="btn btn-sm btn-danger" onClick={() => handleDelete(s)}>Deactivate</button>}
                    </td>
                  </tr>
                ))}
                {staff.length === 0 && <tr><td colSpan={6} className="empty-state">No staff profiles</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'shifts' && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Date</th><th>Staff</th><th>Start</th><th>End</th><th>Hours</th><th>Location</th><th>Notes</th></tr></thead>
            <tbody>
              {shifts.map((s: any) => (
                <tr key={s.id}><td style={{ fontWeight: 600 }}>{s.date}</td><td>{s.staff_name}</td><td>{s.start_time}</td><td>{s.end_time}</td><td>{s.duration_hours ? `${s.duration_hours}h` : '—'}</td><td>{s.location}</td><td style={{ color: 'var(--color-text-muted)' }}>{s.notes || '—'}</td></tr>
              ))}
              {shifts.length === 0 && <tr><td colSpan={7} className="empty-state">No shifts</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'leave' && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Staff</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th></tr></thead>
            <tbody>
              {leave.map((l: any) => (
                <tr key={l.id}><td style={{ fontWeight: 600 }}>{l.staff_name}</td><td>{l.leave_type}</td><td>{l.start_date}</td><td>{l.end_date}</td><td>{l.duration_days}</td><td style={{ maxWidth: 200 }}>{l.reason}</td><td><span className={`badge ${l.status === 'APPROVED' ? 'badge-success' : l.status === 'PENDING' ? 'badge-warning' : 'badge-danger'}`}>{l.status}</span></td></tr>
              ))}
              {leave.length === 0 && <tr><td colSpan={7} className="empty-state">No leave requests</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'training' && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Staff</th><th>Course</th><th>Provider</th><th>Completed</th><th>Expiry</th><th>Status</th></tr></thead>
            <tbody>
              {training.map((t: any) => (
                <tr key={t.id}><td style={{ fontWeight: 600 }}>{t.staff_name}</td><td>{t.title}</td><td>{t.provider}</td><td>{t.completed_date}</td><td>{t.expiry_date || 'N/A'}</td><td><span className={`badge ${t.is_expired ? 'badge-danger' : 'badge-success'}`}>{t.is_expired ? 'EXPIRED' : 'VALID'}</span></td></tr>
              ))}
              {training.length === 0 && <tr><td colSpan={6} className="empty-state">No training records</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit Staff Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 style={{ marginBottom: 16 }}>{editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}</h2>
            {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{error}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">First Name *</label>
                  <input className="form-input" value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} placeholder="e.g. Sam" />
                </div>
                <div>
                  <label className="form-label">Last Name *</label>
                  <input className="form-input" value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} placeholder="e.g. Kim" />
                </div>
              </div>
              <div>
                <label className="form-label">Email *</label>
                <input className="form-input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="e.g. sam.kim@company.com" />
              </div>
              <div>
                <label className="form-label">Phone</label>
                <input className="form-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="e.g. 07700 900000" />
              </div>
              <div>
                <label className="form-label">Role</label>
                <select className="form-input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                  <option value="staff">Staff</option>
                  <option value="manager">Manager</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving…' : editingStaff ? 'Save Changes' : 'Add Staff'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Credentials Modal — shown after successful staff creation */}
      {createdCreds && (
        <div className="modal-overlay" onClick={() => setCreatedCreds(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 style={{ marginBottom: 4 }}>Staff Member Created</h2>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: 16, fontSize: '0.9rem' }}>Share these login details with <strong>{createdCreds.name}</strong>. They will be asked to set their own password on first login.</p>
            <div style={{ background: 'var(--color-primary-light)', borderRadius: 'var(--radius-md)', padding: '1rem', display: 'grid', gap: 8, fontSize: '0.9rem' }}>
              <div><strong>Login URL:</strong> <code>{window.location.origin}/login</code></div>
              <div><strong>Email:</strong> <code>{createdCreds.email}</code></div>
              <div><strong>Temporary Password:</strong> <code style={{ fontSize: '1.1rem', fontWeight: 700 }}>{createdCreds.temp_password}</code></div>
            </div>
            <p style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>This password is shown once. The staff member must change it on their first login.</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button className="btn btn-primary" onClick={() => setCreatedCreds(null)}>Done</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
