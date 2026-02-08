'use client'

import { useEffect, useState } from 'react'
import { getMyShifts, getLeaveRequests, getTrainingRecords, getChannels } from '@/lib/api'

export default function StaffDashboard() {
  const [shifts, setShifts] = useState<any[]>([])
  const [pendingLeave, setPendingLeave] = useState<any[]>([])
  const [expiredTraining, setExpiredTraining] = useState<any[]>([])
  const [channelCount, setChannelCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      const [sh, lv, tr, ch] = await Promise.all([
        getMyShifts(), getLeaveRequests({ status: 'PENDING' }),
        getTrainingRecords(), getChannels(),
      ])
      setShifts(sh.data || [])
      setPendingLeave(lv.data || [])
      setExpiredTraining((tr.data || []).filter((t: any) => t.is_expired))
      setChannelCount((ch.data || []).length)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div className="empty-state">Loading dashboard…</div>

  return (
    <div>
      <div className="page-header">
        <h1>Staff Dashboard</h1>
        <span className="badge badge-success">Tier 2 — Staff</span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{shifts.length}</div>
          <div className="stat-label">Upcoming Shifts</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{pendingLeave.length}</div>
          <div className="stat-label">Pending Leave</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{expiredTraining.length}</div>
          <div className="stat-label">Expired Training</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{channelCount}</div>
          <div className="stat-label">Chat Channels</div>
        </div>
      </div>

      <h2 style={{ marginBottom: '1rem' }}>Upcoming Shifts</h2>
      <div className="table-wrap" style={{ marginBottom: '2rem' }}>
        <table>
          <thead><tr><th>Date</th><th>Time</th><th>Location</th><th>Notes</th></tr></thead>
          <tbody>
            {shifts.slice(0, 5).map((s: any) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.date}</td>
                <td>{s.start_time} – {s.end_time}</td>
                <td>{s.location}</td>
                <td style={{ color: 'var(--color-text-muted)' }}>{s.notes || '—'}</td>
              </tr>
            ))}
            {shifts.length === 0 && <tr><td colSpan={4} className="empty-state">No upcoming shifts</td></tr>}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Quick Links</h2>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            <a href="/app/chat" className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'var(--color-text)' }}>
              <span style={{ fontSize: '1.5rem' }}>💬</span>
              <div><strong>Team Chat</strong><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{channelCount} channels</div></div>
            </a>
            <a href="/app/hse" className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'var(--color-text)' }}>
              <span style={{ fontSize: '1.5rem' }}>🛡️</span>
              <div><strong>Health & Safety</strong><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Compliance dashboard</div></div>
            </a>
            <a href="/app/leave" className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'var(--color-text)' }}>
              <span style={{ fontSize: '1.5rem' }}>🏖️</span>
              <div><strong>Request Leave</strong><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{pendingLeave.length} pending</div></div>
            </a>
          </div>
        </div>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Training Alerts</h2>
          {expiredTraining.length > 0 ? (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {expiredTraining.map((t: any) => (
                <div key={t.id} className="card" style={{ borderLeft: '3px solid var(--color-danger)' }}>
                  <strong>{t.title}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-danger)' }}>Expired: {t.expiry_date}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{t.staff_name}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card empty-state">All training up to date ✓</div>
          )}
        </div>
      </div>
    </div>
  )
}
