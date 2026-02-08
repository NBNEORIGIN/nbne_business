'use client'

import { useEffect, useState } from 'react'
import { getAnalyticsDashboard, getLeads } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function AdminAnalyticsPage() {
  const [analytics, setAnalytics] = useState<any>({})
  const [leads, setLeads] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getAnalyticsDashboard(), getLeads()]).then(([a, l]) => {
      setAnalytics(a.data || {})
      setLeads(l.data || [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="empty-state">Loading analytics…</div>

  const bk = analytics.bookings || {}
  const rev = analytics.revenue || {}
  const crm = analytics.crm || {}

  const totalRevenue = rev.total_pence || 0
  const avgBooking = rev.average_pence || 0
  const totalBookings = bk.total || 0
  const conversionRate = crm.total_leads > 0 ? Math.round(((crm.converted || 0) / crm.total_leads) * 100) : 0

  const statusBreakdown = [
    { status: 'CONFIRMED', count: bk.confirmed || 0 },
    { status: 'PENDING', count: bk.pending || 0 },
    { status: 'COMPLETED', count: bk.completed || 0 },
    { status: 'CANCELLED', count: bk.cancelled || 0 },
  ]

  const leadPipeline = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'].map(status => ({
    status,
    count: leads.filter(l => l.status === status).length,
    value: leads.filter(l => l.status === status).reduce((s: number, l: any) => s + (l.value_pence || 0), 0),
  }))

  return (
    <div>
      <div className="page-header"><h1>Analytics</h1><span className="badge badge-danger">Tier 3</span></div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-number">{formatPrice(totalRevenue)}</div><div className="stat-label">Total Revenue</div></div>
        <div className="stat-card"><div className="stat-number">{formatPrice(avgBooking)}</div><div className="stat-label">Avg Booking</div></div>
        <div className="stat-card"><div className="stat-number">{totalBookings}</div><div className="stat-label">Total Bookings</div></div>
        <div className="stat-card"><div className="stat-number">{conversionRate}%</div><div className="stat-label">Lead Conversion</div></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Booking Status</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Status</th><th>Count</th></tr></thead>
              <tbody>
                {statusBreakdown.map(s => (
                  <tr key={s.status}><td><span className={`badge ${s.status === 'CONFIRMED' ? 'badge-success' : s.status === 'CANCELLED' ? 'badge-danger' : s.status === 'COMPLETED' ? 'badge-info' : 'badge-warning'}`}>{s.status}</span></td><td style={{ fontWeight: 600 }}>{s.count}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Revenue Summary</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Metric</th><th>Value</th></tr></thead>
              <tbody>
                <tr><td>Total Revenue</td><td style={{ fontWeight: 600 }}>{formatPrice(totalRevenue)}</td></tr>
                <tr><td>Average Booking</td><td style={{ fontWeight: 600 }}>{formatPrice(avgBooking)}</td></tr>
                <tr><td>Completed Bookings</td><td style={{ fontWeight: 600 }}>{bk.completed || 0}</td></tr>
                <tr><td>Pipeline Value</td><td style={{ fontWeight: 600 }}>{formatPrice(crm.pipeline_pence || 0)}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <h2 style={{ marginBottom: '1rem' }}>CRM Pipeline</h2>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Stage</th><th>Leads</th><th>Value</th></tr></thead>
          <tbody>
            {leadPipeline.map(s => (
              <tr key={s.status}><td><span className={`badge ${s.status === 'CONVERTED' ? 'badge-success' : s.status === 'LOST' ? 'badge-danger' : s.status === 'NEW' ? 'badge-info' : 'badge-warning'}`}>{s.status}</span></td><td style={{ fontWeight: 600 }}>{s.count}</td><td style={{ fontWeight: 600 }}>{formatPrice(s.value)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
