'use client'

import { useMemo, useState } from 'react'

interface Booking {
  id: number
  customer_name: string
  service_name: string
  staff_name: string | null
  assigned_staff: number | null
  slot_date: string
  slot_start: string
  slot_end: string
  status: string
  price_pence: number
  deposit_pence: number
}

interface Props {
  bookings: Booking[]
  staffList: any[]
  onConfirm: (id: number) => void
  onComplete: (id: number) => void
  onNoShow: (id: number) => void
  onDelete: (id: number) => void
  onAssignStaff: (bookingId: number, staffId: number | null) => void
}

// Staff colour palette — cycles through for each unique staff member
const STAFF_COLOURS = [
  { bg: '#dbeafe', border: '#93c5fd', text: '#1d4ed8' },
  { bg: '#fef3c7', border: '#fcd34d', text: '#b45309' },
  { bg: '#dcfce7', border: '#86efac', text: '#166534' },
  { bg: '#fce7f3', border: '#f9a8d4', text: '#be185d' },
  { bg: '#e0e7ff', border: '#a5b4fc', text: '#4338ca' },
  { bg: '#fef9c3', border: '#fde047', text: '#854d0e' },
  { bg: '#f1f5f9', border: '#cbd5e1', text: '#334155' },
  { bg: '#ede9fe', border: '#c4b5fd', text: '#6d28d9' },
]

const UNASSIGNED_COLOUR = { bg: '#fee2e2', border: '#fca5a5', text: '#991b1b' }

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const HOUR_START = 7
const HOUR_END = 21
const CELL_HEIGHT = 60 // px per hour

function getMonday(d: Date): Date {
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const mon = new Date(d)
  mon.setDate(diff)
  mon.setHours(0, 0, 0, 0)
  return mon
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function formatShortDate(d: Date): string {
  return d.getDate().toString()
}

function formatMonthYear(d: Date): string {
  return d.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
}

function formatPrice(pence: number): string {
  return '£' + (pence / 100).toFixed(0)
}

function timeToMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

export default function BookingsCalendar({ bookings, staffList, onConfirm, onComplete, onNoShow, onDelete, onAssignStaff }: Props) {
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null)

  const monday = useMemo(() => {
    const today = new Date()
    const mon = getMonday(today)
    return addDays(mon, weekOffset * 7)
  }, [weekOffset])

  const weekDates = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => addDays(monday, i))
  }, [monday])

  // Build staff colour map
  const staffColourMap = useMemo(() => {
    const map = new Map<string, typeof STAFF_COLOURS[0]>()
    const uniqueStaff = Array.from(new Set(bookings.map(b => b.staff_name).filter(Boolean) as string[]))
    uniqueStaff.forEach((name, i) => {
      map.set(name!, STAFF_COLOURS[i % STAFF_COLOURS.length])
    })
    return map
  }, [bookings])

  // Filter bookings for this week
  const weekBookings = useMemo(() => {
    const weekDateStrs = weekDates.map(d => formatDate(d))
    return bookings.filter(b =>
      weekDateStrs.includes(b.slot_date) &&
      !['CANCELLED', 'NO_SHOW'].includes(b.status)
    )
  }, [bookings, weekDates])

  // Group by day
  const bookingsByDay = useMemo(() => {
    const map = new Map<string, Booking[]>()
    weekDates.forEach(d => map.set(formatDate(d), []))
    weekBookings.forEach(b => {
      const arr = map.get(b.slot_date)
      if (arr) arr.push(b)
    })
    return map
  }, [weekBookings, weekDates])

  const hours = Array.from({ length: HOUR_END - HOUR_START }, (_, i) => HOUR_START + i)
  const gridHeight = hours.length * CELL_HEIGHT

  function getBlockStyle(b: Booking): React.CSSProperties {
    const startMin = timeToMinutes(b.slot_start || '09:00')
    const endMin = timeToMinutes(b.slot_end || b.slot_start || '09:00') || startMin + 30
    const topOffset = ((startMin - HOUR_START * 60) / 60) * CELL_HEIGHT
    const height = Math.max(((endMin - startMin) / 60) * CELL_HEIGHT, 24)
    const colour = b.staff_name ? (staffColourMap.get(b.staff_name) || STAFF_COLOURS[0]) : UNASSIGNED_COLOUR

    return {
      position: 'absolute',
      top: topOffset,
      left: 4,
      right: 4,
      height,
      background: colour.bg,
      borderLeft: `3px solid ${colour.border}`,
      borderRadius: 6,
      padding: '3px 6px',
      fontSize: '0.7rem',
      lineHeight: 1.3,
      color: colour.text,
      cursor: 'pointer',
      overflow: 'hidden',
      zIndex: 2,
      transition: 'box-shadow 0.15s',
    }
  }

  const isThisWeek = weekOffset === 0
  const todayStr = formatDate(new Date())

  return (
    <div>
      {/* Week navigation */}
      <div style={styles.weekNav}>
        <button style={styles.navBtn} onClick={() => setWeekOffset(w => w - 1)}>← Prev</button>
        <div style={styles.weekLabel}>
          <span style={{ fontWeight: 700 }}>
            {formatMonthYear(monday)}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            {monday.getDate()} – {addDays(monday, 6).getDate()} {addDays(monday, 6).toLocaleDateString('en-GB', { month: 'short' })}
          </span>
          {!isThisWeek && (
            <button style={{ ...styles.navBtn, fontSize: '0.75rem', padding: '0.2rem 0.6rem' }} onClick={() => setWeekOffset(0)}>
              Today
            </button>
          )}
        </div>
        <button style={styles.navBtn} onClick={() => setWeekOffset(w => w + 1)}>Next →</button>
      </div>

      {/* Calendar grid */}
      <div style={styles.calendarWrap}>
        <div style={styles.calendarGrid}>
          {/* Time column */}
          <div style={styles.timeColumn}>
            <div style={styles.dayHeader}></div>
            {hours.map(h => (
              <div key={h} style={{ ...styles.timeLabel, height: CELL_HEIGHT }}>
                {`${h.toString().padStart(2, '0')}:00`}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {weekDates.map((date, dayIdx) => {
            const dateStr = formatDate(date)
            const isToday = dateStr === todayStr
            const dayBookings = bookingsByDay.get(dateStr) || []

            return (
              <div key={dayIdx} style={{ ...styles.dayColumn, flex: 1 }}>
                <div style={{
                  ...styles.dayHeader,
                  background: isToday ? '#2563eb' : '#f8fafc',
                  color: isToday ? '#fff' : '#334155',
                }}>
                  <div style={{ fontWeight: 600, fontSize: '0.8rem' }}>{DAYS[dayIdx]}</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>{formatShortDate(date)}</div>
                </div>
                <div style={{ position: 'relative', height: gridHeight }}>
                  {/* Hour grid lines */}
                  {hours.map(h => (
                    <div key={h} style={{
                      position: 'absolute',
                      top: (h - HOUR_START) * CELL_HEIGHT,
                      left: 0,
                      right: 0,
                      height: CELL_HEIGHT,
                      borderBottom: '1px solid #f1f5f9',
                      borderRight: dayIdx < 6 ? '1px solid #f1f5f9' : 'none',
                    }} />
                  ))}
                  {/* Booking blocks */}
                  {dayBookings.map(b => (
                    <div
                      key={b.id}
                      style={getBlockStyle(b)}
                      onClick={() => setSelectedBooking(b)}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)' }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.boxShadow = 'none' }}
                    >
                      <div style={{ fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {b.service_name}
                      </div>
                      <div style={{ opacity: 0.8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {b.staff_name || 'Unassigned'} — {b.slot_start}
                      </div>
                      {b.deposit_pence > 0 && (
                        <div style={{ opacity: 0.7, fontSize: '0.65rem' }}>
                          {formatPrice(b.deposit_pence)} deposit paid
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Booking detail popover */}
      {selectedBooking && (
        <div style={styles.popoverOverlay} onClick={() => setSelectedBooking(null)}>
          <div style={styles.popover} onClick={e => e.stopPropagation()}>
            <div style={styles.popoverHeader}>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>{selectedBooking.service_name}</h3>
              <button style={styles.popoverClose} onClick={() => setSelectedBooking(null)}>✕</button>
            </div>
            <div style={styles.popoverBody}>
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Customer</span>
                <span style={{ fontWeight: 600 }}>{selectedBooking.customer_name}</span>
              </div>
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Time</span>
                <span>{selectedBooking.slot_start} – {selectedBooking.slot_end || '?'}</span>
              </div>
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Date</span>
                <span>{selectedBooking.slot_date}</span>
              </div>
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Price</span>
                <span style={{ fontWeight: 600 }}>{formatPrice(selectedBooking.price_pence)}</span>
              </div>
              {selectedBooking.deposit_pence > 0 && (
                <div style={styles.popoverRow}>
                  <span style={styles.popoverLabel}>Deposit</span>
                  <span>{formatPrice(selectedBooking.deposit_pence)} paid</span>
                </div>
              )}
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Staff</span>
                <select
                  value={selectedBooking.assigned_staff || ''}
                  onChange={e => {
                    onAssignStaff(selectedBooking.id, e.target.value ? Number(e.target.value) : null)
                    setSelectedBooking(null)
                  }}
                  style={{ fontSize: '0.85rem', padding: '0.25rem 0.5rem', borderRadius: 4, border: '1px solid #e2e8f0' }}
                >
                  <option value="">Unassigned</option>
                  {staffList.map((s: any) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div style={styles.popoverRow}>
                <span style={styles.popoverLabel}>Status</span>
                <span className={`badge ${selectedBooking.status === 'CONFIRMED' ? 'badge-success' : selectedBooking.status === 'COMPLETED' ? 'badge-info' : 'badge-warning'}`}>
                  {selectedBooking.status}
                </span>
              </div>
            </div>
            <div style={styles.popoverActions}>
              {selectedBooking.status === 'PENDING' && (
                <button className="btn btn-outline btn-sm" onClick={() => { onConfirm(selectedBooking.id); setSelectedBooking(null) }}>Confirm</button>
              )}
              {selectedBooking.status === 'CONFIRMED' && (
                <button className="btn btn-outline btn-sm" onClick={() => { onComplete(selectedBooking.id); setSelectedBooking(null) }}>Complete</button>
              )}
              {['CONFIRMED', 'PENDING'].includes(selectedBooking.status) && (
                <button className="btn btn-ghost btn-sm" style={{ color: '#dc2626' }} onClick={() => { onNoShow(selectedBooking.id); setSelectedBooking(null) }}>No Show</button>
              )}
              <button className="btn btn-ghost btn-sm" style={{ color: '#dc2626', opacity: 0.7 }} onClick={() => { onDelete(selectedBooking.id); setSelectedBooking(null) }}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Staff legend */}
      <div style={styles.legend}>
        {Array.from(staffColourMap.entries()).map(([name, colour]) => (
          <div key={name} style={styles.legendItem}>
            <div style={{ width: 12, height: 12, borderRadius: 3, background: colour.bg, border: `2px solid ${colour.border}` }} />
            <span style={{ fontSize: '0.75rem', color: '#475569' }}>{name}</span>
          </div>
        ))}
        {bookings.some(b => !b.staff_name) && (
          <div style={styles.legendItem}>
            <div style={{ width: 12, height: 12, borderRadius: 3, background: UNASSIGNED_COLOUR.bg, border: `2px solid ${UNASSIGNED_COLOUR.border}` }} />
            <span style={{ fontSize: '0.75rem', color: '#991b1b' }}>Unassigned</span>
          </div>
        )}
      </div>
    </div>
  )
}


const styles: Record<string, React.CSSProperties> = {
  weekNav: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    marginBottom: '0.5rem',
  },
  navBtn: {
    padding: '0.4rem 0.85rem',
    borderRadius: 6,
    border: '1px solid #e2e8f0',
    background: '#fff',
    fontSize: '0.82rem',
    fontWeight: 600,
    color: '#334155',
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
  weekLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  calendarWrap: {
    overflowX: 'auto' as const,
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    background: '#fff',
  },
  calendarGrid: {
    display: 'flex',
    minWidth: 800,
  },
  timeColumn: {
    width: 56,
    flexShrink: 0,
    borderRight: '1px solid #e2e8f0',
  },
  timeLabel: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'flex-end',
    paddingRight: 8,
    paddingTop: 2,
    fontSize: '0.7rem',
    color: '#94a3b8',
    fontWeight: 500,
  },
  dayColumn: {
    position: 'relative' as const,
    minWidth: 100,
  },
  dayHeader: {
    textAlign: 'center' as const,
    padding: '0.5rem 0.25rem',
    borderBottom: '1px solid #e2e8f0',
    position: 'sticky' as const,
    top: 0,
    zIndex: 5,
    background: '#f8fafc',
  },
  legend: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '0.75rem',
    padding: '0.75rem 0',
    marginTop: '0.25rem',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.35rem',
  },
  popoverOverlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  popover: {
    background: '#fff',
    borderRadius: 12,
    boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
    width: 380,
    maxWidth: '90vw',
    overflow: 'hidden',
  },
  popoverHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.85rem 1rem',
    borderBottom: '1px solid #f1f5f9',
    background: '#f8fafc',
  },
  popoverClose: {
    background: 'none',
    border: 'none',
    fontSize: '1.1rem',
    cursor: 'pointer',
    color: '#64748b',
    padding: '0.2rem 0.4rem',
  },
  popoverBody: {
    padding: '0.75rem 1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  popoverRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.85rem',
  },
  popoverLabel: {
    color: '#64748b',
    fontSize: '0.8rem',
  },
  popoverActions: {
    display: 'flex',
    gap: '0.5rem',
    padding: '0.75rem 1rem',
    borderTop: '1px solid #f1f5f9',
    flexWrap: 'wrap' as const,
  },
}
