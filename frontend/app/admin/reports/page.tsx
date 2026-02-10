'use client'

import { useEffect, useState } from 'react'
import { getBookingReports, getStaffList } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

function todayStr() { return new Date().toISOString().slice(0, 10) }
function daysAgo(n: number) { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10) }

type ReportTab = 'overview' | 'daily' | 'monthly' | 'staff'

export default function AdminReportsPage() {
  const [tab, setTab] = useState<ReportTab>('overview')
  const [dateFrom, setDateFrom] = useState(daysAgo(30))
  const [dateTo, setDateTo] = useState(todayStr())
  const [staffFilter, setStaffFilter] = useState<number | undefined>()
  const [data, setData] = useState<any>(null)
  const [staffList, setStaffList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getStaffList().then(r => setStaffList(r.data || []))
  }, [])

  useEffect(() => {
    setLoading(true)
    getBookingReports({ report: tab, date_from: dateFrom, date_to: dateTo, staff_id: staffFilter }).then(r => {
      setData(r.data)
      setLoading(false)
    })
  }, [tab, dateFrom, dateTo, staffFilter])

  const tabs: { key: ReportTab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'daily', label: 'Daily Takings' },
    { key: 'monthly', label: 'Monthly' },
    { key: 'staff', label: 'Per Staff' },
  ]

  return (
    <div>
      <div className="page-header"><h1>Reports</h1><span className="badge badge-danger">Tier 3</span></div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem', alignItems: 'flex-end' }}>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>From</label>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>To</label>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
        </div>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>Staff</label>
          <select value={staffFilter ?? ''} onChange={e => setStaffFilter(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">All Staff</option>
            {staffList.map((s: any) => (
              <option key={s.id} value={s.user_id || s.id}>{s.display_name}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '0.25rem' }}>
          <button className="btn btn-ghost btn-sm" onClick={() => { setDateFrom(daysAgo(7)); setDateTo(todayStr()) }}>7d</button>
          <button className="btn btn-ghost btn-sm" onClick={() => { setDateFrom(daysAgo(30)); setDateTo(todayStr()) }}>30d</button>
          <button className="btn btn-ghost btn-sm" onClick={() => { setDateFrom(daysAgo(90)); setDateTo(todayStr()) }}>90d</button>
          <button className="btn btn-ghost btn-sm" onClick={() => { setDateFrom(daysAgo(365)); setDateTo(todayStr()) }}>1yr</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: '1.5rem' }}>
        {tabs.map(t => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </div>

      {loading ? (
        <div className="empty-state">Loading report…</div>
      ) : !data ? (
        <div className="empty-state">No data available</div>
      ) : (
        <>
          {tab === 'overview' && <OverviewReport data={data} />}
          {tab === 'daily' && <DailyReport data={data} />}
          {tab === 'monthly' && <MonthlyReport data={data} />}
          {tab === 'staff' && <StaffReport data={data} />}
        </>
      )}
    </div>
  )
}

function OverviewReport({ data }: { data: any }) {
  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{formatPrice(data.revenue_pence || 0)}</div>
          <div className="stat-label">Total Revenue</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{formatPrice(data.deposits_pence || 0)}</div>
          <div className="stat-label">Deposits Collected</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.total_bookings || 0}</div>
          <div className="stat-label">Total Bookings</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.completed || 0}</div>
          <div className="stat-label">Completed</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Booking Outcomes</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Metric</th><th>Count</th></tr></thead>
              <tbody>
                <tr><td>Completed / Confirmed</td><td style={{ fontWeight: 600 }}>{data.completed || 0}</td></tr>
                <tr><td><span style={{ color: 'var(--color-danger)' }}>No Shows</span></td><td style={{ fontWeight: 600, color: 'var(--color-danger)' }}>{data.no_shows || 0}</td></tr>
                <tr><td>Cancelled</td><td style={{ fontWeight: 600 }}>{data.cancelled || 0}</td></tr>
                <tr><td>Total</td><td style={{ fontWeight: 600 }}>{data.total_bookings || 0}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Key Metrics</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Metric</th><th>Value</th></tr></thead>
              <tbody>
                <tr><td>No-Show Rate</td><td style={{ fontWeight: 600, color: (data.no_show_rate || 0) > 10 ? 'var(--color-danger)' : 'var(--color-success)' }}>{data.no_show_rate || 0}%</td></tr>
                <tr><td>Avg Deposit %</td><td style={{ fontWeight: 600 }}>{data.avg_deposit_percentage || 0}%</td></tr>
                <tr><td>Revenue</td><td style={{ fontWeight: 600 }}>{formatPrice(data.revenue_pence || 0)}</td></tr>
                <tr><td>Deposits</td><td style={{ fontWeight: 600 }}>{formatPrice(data.deposits_pence || 0)}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function DailyReport({ data }: { data: any }) {
  const rows = data.rows || []
  const totalRevenue = rows.reduce((s: number, r: any) => s + (r.revenue_pence || 0), 0)
  const totalBookings = rows.reduce((s: number, r: any) => s + (r.bookings || 0), 0)
  const totalNoShows = rows.reduce((s: number, r: any) => s + (r.no_shows || 0), 0)

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card"><div className="stat-number">{formatPrice(totalRevenue)}</div><div className="stat-label">Period Revenue</div></div>
        <div className="stat-card"><div className="stat-number">{totalBookings}</div><div className="stat-label">Total Bookings</div></div>
        <div className="stat-card"><div className="stat-number">{totalNoShows}</div><div className="stat-label">No Shows</div></div>
        <div className="stat-card"><div className="stat-number">{rows.length}</div><div className="stat-label">Active Days</div></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Date</th><th style={{ textAlign: 'right' }}>Revenue</th><th style={{ textAlign: 'right' }}>Deposits</th><th style={{ textAlign: 'right' }}>Bookings</th><th style={{ textAlign: 'right' }}>No Shows</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>No data for this period</td></tr>
            ) : rows.map((r: any) => (
              <tr key={r.date}>
                <td>{r.date}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatPrice(r.revenue_pence)}</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(r.deposits_pence)}</td>
                <td style={{ textAlign: 'right' }}>{r.bookings}</td>
                <td style={{ textAlign: 'right', color: r.no_shows > 0 ? 'var(--color-danger)' : undefined }}>{r.no_shows}</td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot>
              <tr style={{ fontWeight: 700, borderTop: '2px solid var(--color-border)' }}>
                <td>Total</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(totalRevenue)}</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(rows.reduce((s: number, r: any) => s + (r.deposits_pence || 0), 0))}</td>
                <td style={{ textAlign: 'right' }}>{totalBookings}</td>
                <td style={{ textAlign: 'right', color: totalNoShows > 0 ? 'var(--color-danger)' : undefined }}>{totalNoShows}</td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  )
}

function MonthlyReport({ data }: { data: any }) {
  const rows = data.rows || []
  const totalRevenue = rows.reduce((s: number, r: any) => s + (r.revenue_pence || 0), 0)
  const totalBookings = rows.reduce((s: number, r: any) => s + (r.bookings || 0), 0)

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card"><div className="stat-number">{formatPrice(totalRevenue)}</div><div className="stat-label">Period Revenue</div></div>
        <div className="stat-card"><div className="stat-number">{totalBookings}</div><div className="stat-label">Total Bookings</div></div>
        <div className="stat-card"><div className="stat-number">{rows.length}</div><div className="stat-label">Months</div></div>
        <div className="stat-card"><div className="stat-number">{totalBookings > 0 ? formatPrice(Math.round(totalRevenue / rows.length)) : '£0.00'}</div><div className="stat-label">Avg Monthly</div></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Month</th><th style={{ textAlign: 'right' }}>Revenue</th><th style={{ textAlign: 'right' }}>Deposits</th><th style={{ textAlign: 'right' }}>Bookings</th><th style={{ textAlign: 'right' }}>No Shows</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>No data for this period</td></tr>
            ) : rows.map((r: any) => (
              <tr key={r.month}>
                <td>{r.month}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatPrice(r.revenue_pence)}</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(r.deposits_pence)}</td>
                <td style={{ textAlign: 'right' }}>{r.bookings}</td>
                <td style={{ textAlign: 'right', color: r.no_shows > 0 ? 'var(--color-danger)' : undefined }}>{r.no_shows}</td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot>
              <tr style={{ fontWeight: 700, borderTop: '2px solid var(--color-border)' }}>
                <td>Total</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(totalRevenue)}</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(rows.reduce((s: number, r: any) => s + (r.deposits_pence || 0), 0))}</td>
                <td style={{ textAlign: 'right' }}>{totalBookings}</td>
                <td style={{ textAlign: 'right' }}>{rows.reduce((s: number, r: any) => s + (r.no_shows || 0), 0)}</td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  )
}

function StaffReport({ data }: { data: any }) {
  const rows = data.rows || []
  const totalRevenue = rows.reduce((s: number, r: any) => s + (r.revenue_pence || 0), 0)
  const totalBookings = rows.reduce((s: number, r: any) => s + (r.bookings || 0), 0)

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card"><div className="stat-number">{formatPrice(totalRevenue)}</div><div className="stat-label">Total Revenue</div></div>
        <div className="stat-card"><div className="stat-number">{totalBookings}</div><div className="stat-label">Total Bookings</div></div>
        <div className="stat-card"><div className="stat-number">{rows.length}</div><div className="stat-label">Active Staff</div></div>
        <div className="stat-card"><div className="stat-number">{rows.length > 0 ? formatPrice(Math.round(totalRevenue / rows.length)) : '£0.00'}</div><div className="stat-label">Avg per Staff</div></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Staff Member</th><th style={{ textAlign: 'right' }}>Revenue</th><th style={{ textAlign: 'right' }}>Deposits</th><th style={{ textAlign: 'right' }}>Bookings</th><th style={{ textAlign: 'right' }}>No Shows</th><th style={{ textAlign: 'right' }}>No-Show %</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>No staff data — assign staff to bookings to see per-staff reports</td></tr>
            ) : rows.map((r: any) => {
              const total = r.bookings + (r.no_shows || 0)
              const nsRate = total > 0 ? Math.round((r.no_shows || 0) / total * 100) : 0
              return (
                <tr key={r.staff_id}>
                  <td style={{ fontWeight: 600 }}>{r.staff_name || 'Unassigned'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatPrice(r.revenue_pence)}</td>
                  <td style={{ textAlign: 'right' }}>{formatPrice(r.deposits_pence)}</td>
                  <td style={{ textAlign: 'right' }}>{r.bookings}</td>
                  <td style={{ textAlign: 'right', color: r.no_shows > 0 ? 'var(--color-danger)' : undefined }}>{r.no_shows || 0}</td>
                  <td style={{ textAlign: 'right', color: nsRate > 10 ? 'var(--color-danger)' : undefined }}>{nsRate}%</td>
                </tr>
              )
            })}
          </tbody>
          {rows.length > 0 && (
            <tfoot>
              <tr style={{ fontWeight: 700, borderTop: '2px solid var(--color-border)' }}>
                <td>Total</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(totalRevenue)}</td>
                <td style={{ textAlign: 'right' }}>{formatPrice(rows.reduce((s: number, r: any) => s + (r.deposits_pence || 0), 0))}</td>
                <td style={{ textAlign: 'right' }}>{totalBookings}</td>
                <td style={{ textAlign: 'right' }}>{rows.reduce((s: number, r: any) => s + (r.no_shows || 0), 0)}</td>
                <td></td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  )
}
