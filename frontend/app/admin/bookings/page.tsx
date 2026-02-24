'use client'

import { useEffect, useState } from 'react'
import { getBookings, getBookableStaff, assignStaffToBooking, confirmBooking, completeBooking, markNoShow, deleteBooking } from '@/lib/api'
import BookingsCalendar from '@/components/BookingsCalendar'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

function statusBadge(s: string) {
  const cls = s === 'CONFIRMED' ? 'badge-success'
    : s === 'COMPLETED' ? 'badge-info'
    : s === 'CANCELLED' || s === 'NO_SHOW' ? 'badge-danger'
    : 'badge-warning'
  const label = s === 'NO_SHOW' ? 'No Show' : s === 'PENDING_PAYMENT' ? 'Awaiting Payment' : s
  return <span className={`badge ${cls}`}>{label}</span>
}

export default function AdminBookingsPage() {
  const [allBookings, setAllBookings] = useState<any[]>([])
  const [staffList, setStaffList] = useState<any[]>([])
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('calendar')

  useEffect(() => {
    getBookings().then(bRes => {
      setAllBookings(bRes.data || [])
      setLoading(false)
    }).catch(() => setLoading(false))
    getBookableStaff().then(sRes => {
      setStaffList(sRes.data || [])
    }).catch(() => {})
  }, [])

  if (loading) return <div className="empty-state">Loading bookings…</div>

  function updateBooking(updated: any) {
    setAllBookings(prev => prev.map(b => b.id === updated.id ? updated : b))
  }

  async function handleAssignStaff(bookingId: number, staffId: number | null) {
    const res = await assignStaffToBooking(bookingId, staffId)
    if (res.data) updateBooking(res.data)
    if (res.error) alert(res.error)
  }

  async function handleConfirm(bookingId: number) {
    const res = await confirmBooking(bookingId)
    if (res.data) updateBooking(res.data)
  }

  async function handleNoShow(bookingId: number) {
    const res = await markNoShow(bookingId)
    if (res.data) updateBooking(res.data)
  }

  async function handleComplete(bookingId: number) {
    const res = await completeBooking(bookingId)
    if (res.data) updateBooking(res.data)
  }

  async function handleDelete(bookingId: number) {
    if (!confirm(`Permanently delete booking #${bookingId}? This cannot be undone.`)) return
    const res = await deleteBooking(bookingId)
    if (res.data?.deleted) {
      setAllBookings(prev => prev.filter(b => b.id !== bookingId))
    }
  }

  const filtered = allBookings
    .filter(b => filter === 'ALL' || b.status === filter)
    .filter(b => !search || (b.customer_name || '').toLowerCase().includes(search.toLowerCase()) || (b.service_name || '').toLowerCase().includes(search.toLowerCase()))

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h1 style={{ margin: 0 }}>Bookings</h1>
          <span className="badge badge-danger">Tier 3</span>
        </div>
        <div style={{ display: 'flex', gap: 0, borderRadius: 6, overflow: 'hidden', border: '1px solid #e2e8f0' }}>
          <button
            onClick={() => setViewMode('calendar')}
            style={{
              padding: '0.4rem 0.85rem', border: 'none', fontSize: '0.8rem', fontWeight: 600,
              fontFamily: 'inherit', cursor: 'pointer',
              background: viewMode === 'calendar' ? '#2563eb' : '#fff',
              color: viewMode === 'calendar' ? '#fff' : '#334155',
            }}
          >📅 Calendar</button>
          <button
            onClick={() => setViewMode('list')}
            style={{
              padding: '0.4rem 0.85rem', border: 'none', borderLeft: '1px solid #e2e8f0', fontSize: '0.8rem', fontWeight: 600,
              fontFamily: 'inherit', cursor: 'pointer',
              background: viewMode === 'list' ? '#2563eb' : '#fff',
              color: viewMode === 'list' ? '#fff' : '#334155',
            }}
          >☰ List</button>
        </div>
      </div>

      {viewMode === 'calendar' ? (
        <BookingsCalendar
          bookings={filtered}
          staffList={staffList}
          onConfirm={handleConfirm}
          onComplete={handleComplete}
          onNoShow={handleNoShow}
          onDelete={handleDelete}
          onAssignStaff={handleAssignStaff}
        />
      ) : null}

      {viewMode === 'list' && <div className="filter-bar">
        <input placeholder="Search customer or service..." value={search} onChange={e => setSearch(e.target.value)} />
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="PENDING">Pending</option>
          <option value="PENDING_PAYMENT">Pending Payment</option>
          <option value="COMPLETED">Completed</option>
          <option value="NO_SHOW">No Show</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>
      }
      {viewMode === 'list' && <div className="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Customer</th><th>Service</th><th>Date / Time</th><th>Price</th><th>Deposit</th><th>Staff</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {filtered.map(b => (
              <tr key={b.id}>
                <td>#{b.id}</td>
                <td><div style={{ fontWeight: 600 }}>{b.customer_name}</div><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{b.customer_email}</div></td>
                <td>{b.service_name}</td>
                <td><div>{b.slot_date}</div><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{b.slot_start}{b.slot_end ? ` – ${b.slot_end}` : ''}</div></td>
                <td style={{ fontWeight: 600 }}>{formatPrice(b.price_pence)}</td>
                <td>{b.deposit_pence > 0 ? formatPrice(b.deposit_pence) : '—'}</td>
                <td>
                  <select
                    value={b.assigned_staff || ''}
                    onChange={e => handleAssignStaff(b.id, e.target.value ? Number(e.target.value) : null)}
                    style={{ fontSize: '0.8rem', padding: '0.25rem', minWidth: 100 }}
                  >
                    <option value="">Unassigned</option>
                    {staffList.map((s: any) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </td>
                <td>{statusBadge(b.status)}</td>
                <td className="actions-row" style={{ gap: '0.25rem' }}>
                  {b.status === 'PENDING' && <button className="btn btn-outline btn-sm" onClick={() => handleConfirm(b.id)}>Confirm</button>}
                  {b.status === 'CONFIRMED' && <button className="btn btn-outline btn-sm" onClick={() => handleComplete(b.id)}>Complete</button>}
                  {(b.status === 'CONFIRMED' || b.status === 'PENDING') && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => handleNoShow(b.id)}>No Show</button>}
                  <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', opacity: 0.7 }} onClick={() => handleDelete(b.id)} title="Delete booking permanently">Delete</button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={9} className="empty-state">No bookings found</td></tr>}
          </tbody>
        </table>
      </div>}
    </div>
  )
}
