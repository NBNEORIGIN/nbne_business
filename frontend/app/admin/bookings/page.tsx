'use client'

import { useEffect, useState } from 'react'
import { getBookings } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function AdminBookingsPage() {
  const [allBookings, setAllBookings] = useState<any[]>([])
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBookings().then(r => { setAllBookings(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading bookings…</div>

  const filtered = allBookings
    .filter(b => filter === 'ALL' || b.status === filter)
    .filter(b => !search || (b.customer_name || '').toLowerCase().includes(search.toLowerCase()) || (b.service_name || '').toLowerCase().includes(search.toLowerCase()))

  return (
    <div>
      <div className="page-header"><h1>Bookings</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="filter-bar">
        <input placeholder="Search customer or service..." value={search} onChange={e => setSearch(e.target.value)} />
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="PENDING">Pending</option>
          <option value="PENDING_PAYMENT">Pending Payment</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Customer</th><th>Service</th><th>Date</th><th>Time</th><th>Price</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.map(b => (
              <tr key={b.id}>
                <td>#{b.id}</td>
                <td><div style={{ fontWeight: 600 }}>{b.customer_name}</div><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{b.customer_email}</div></td>
                <td>{b.service_name}</td>
                <td>{b.slot_date}</td>
                <td>{b.slot_start} – {b.slot_end}</td>
                <td style={{ fontWeight: 600 }}>{formatPrice(b.price_pence)}</td>
                <td><span className={`badge ${b.status === 'CONFIRMED' ? 'badge-success' : b.status === 'CANCELLED' ? 'badge-danger' : b.status === 'COMPLETED' ? 'badge-info' : 'badge-warning'}`}>{b.status}</span></td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={7} className="empty-state">No bookings found</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
