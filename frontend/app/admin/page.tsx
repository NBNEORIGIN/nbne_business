'use client'

import { useEffect, useState } from 'react'
import { getAnalyticsDashboard, getBookings, getAuditLog } from '@/lib/api'

function formatPrice(pence: number) {
  return '£' + (pence / 100).toFixed(2)
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<any>({})
  const [bookings, setBookings] = useState<any[]>([])
  const [audit, setAudit] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getAnalyticsDashboard(),
      getBookings(),
      getAuditLog({ limit: 5 }),
    ]).then(([a, b, au]) => {
      setAnalytics(a.data || {})
      setBookings(b.data || [])
      setAudit(au.data || [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="empty-state">Loading dashboard…</div>

  const bk = analytics.bookings || {}
  const rev = analytics.revenue || {}
  const st = analytics.staff || {}
  const crm = analytics.crm || {}
  const comp = analytics.compliance || {}

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <span className="badge badge-danger">Tier 3 — Owner</span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{formatPrice(rev.total_pence || 0)}</div>
          <div className="stat-label">Total Revenue</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{(bk.confirmed || 0) + (bk.pending || 0)}</div>
          <div className="stat-label">Active Bookings</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{st.total || 0}</div>
          <div className="stat-label">Staff Members</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{crm.new || 0}</div>
          <div className="stat-label">New Leads</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{comp.active_rams || 0}</div>
          <div className="stat-label">Active RAMS</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{comp.open_incidents || 0}</div>
          <div className="stat-label">Open Incidents</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Recent Bookings</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Customer</th><th>Service</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>
                {bookings.slice(0, 5).map((b: any) => (
                  <tr key={b.id}>
                    <td style={{ fontWeight: 600 }}>{b.customer_name}</td>
                    <td>{b.service_name}</td>
                    <td>{b.slot_date}</td>
                    <td><span className={`badge ${b.status === 'CONFIRMED' ? 'badge-success' : b.status === 'CANCELLED' ? 'badge-danger' : 'badge-warning'}`}>{b.status}</span></td>
                  </tr>
                ))}
                {bookings.length === 0 && <tr><td colSpan={4} className="empty-state">No bookings</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h2 style={{ marginBottom: '1rem' }}>Audit Trail</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>User</th><th>Action</th><th>Entity</th><th>Time</th></tr></thead>
              <tbody>
                {audit.slice(0, 5).map((a: any) => (
                  <tr key={a.id}>
                    <td style={{ fontWeight: 600 }}>{a.user_name || 'System'}</td>
                    <td><span className="badge badge-info">{a.action}</span></td>
                    <td style={{ fontSize: '0.8rem', maxWidth: 200 }}>{a.entity_type} {a.entity_id ? `#${a.entity_id}` : ''}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(a.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
                {audit.length === 0 && <tr><td colSpan={4} className="empty-state">No audit entries</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
