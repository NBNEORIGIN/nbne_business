'use client'

import { useEffect, useState } from 'react'
import { getStaffList, getShifts, getLeaveRequests, getTrainingRecords } from '@/lib/api'

export default function AdminStaffPage() {
  const [tab, setTab] = useState<'profiles' | 'shifts' | 'leave' | 'training'>('profiles')
  const [staff, setStaff] = useState<any[]>([])
  const [shifts, setShifts] = useState<any[]>([])
  const [leave, setLeave] = useState<any[]>([])
  const [training, setTraining] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStaffList(), getShifts(), getLeaveRequests(), getTrainingRecords()]).then(([s, sh, lv, tr]) => {
      setStaff(s.data || [])
      setShifts(sh.data || [])
      setLeave(lv.data || [])
      setTraining(tr.data || [])
      setLoading(false)
    })
  }, [])

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
        <div className="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Role</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead>
            <tbody>
              {staff.map((s: any) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600 }}>{s.display_name}</td>
                  <td>{s.role}</td>
                  <td>{s.email}</td>
                  <td>{s.phone}</td>
                  <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                </tr>
              ))}
              {staff.length === 0 && <tr><td colSpan={5} className="empty-state">No staff profiles</td></tr>}
            </tbody>
          </table>
        </div>
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
    </div>
  )
}
