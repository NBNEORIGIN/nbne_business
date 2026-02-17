'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { getLeaveCalendar, getLeaveRequests, createLeaveRequest, reviewLeave, deleteLeaveRequest } from '@/lib/api'

interface LeaveCalendarProps {
  staff: any[]
  currentUserRole: string
  currentUserStaffId: number | null
  onRefresh?: () => void
}

type CalView = 'month' | 'week' | 'day'

// --- Helpers ---
function fmtDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function startOfWeek(d: Date): Date {
  const r = new Date(d)
  const day = r.getDay()
  r.setDate(r.getDate() - (day === 0 ? 6 : day - 1)) // Monday start
  return r
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0)
}

function isSameDay(a: Date, b: Date): boolean {
  return fmtDate(a) === fmtDate(b)
}

function isInRange(day: Date, start: string, end: string): boolean {
  const ds = fmtDate(day)
  return ds >= start && ds <= end
}

function britishDate(d: Date): string {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${days[d.getDay()]} ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`
}

function monthLabel(d: Date): string {
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
  return `${months[d.getMonth()]} ${d.getFullYear()}`
}

const LEAVE_COLOURS: Record<string, { bg: string; border: string; text: string }> = {
  APPROVED: { bg: '#dcfce7', border: '#16a34a', text: '#15803d' },
  PENDING: { bg: '#fef9c3', border: '#eab308', text: '#a16207' },
}

const TYPE_LABELS: Record<string, string> = {
  ANNUAL: 'Annual Leave',
  SICK: 'Sick Leave',
  UNPAID: 'Unpaid Leave',
  OTHER: 'Other',
}

export default function LeaveCalendar({ staff, currentUserRole, currentUserStaffId, onRefresh }: LeaveCalendarProps) {
  const [calView, setCalView] = useState<CalView>('month')
  const [refDate, setRefDate] = useState(new Date())
  const [calLeave, setCalLeave] = useState<any[]>([])
  const [allLeave, setAllLeave] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Selection state for requesting leave
  const [selectedDates, setSelectedDates] = useState<Set<string>>(new Set())
  const [selecting, setSelecting] = useState(false)

  // Request modal
  const [showRequestModal, setShowRequestModal] = useState(false)
  const [reqForm, setReqForm] = useState({ leave_type: 'ANNUAL', reason: '', staff: '' })
  const [reqSaving, setReqSaving] = useState(false)
  const [reqError, setReqError] = useState('')

  // Hover tooltip
  const [hoverDay, setHoverDay] = useState<string | null>(null)
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 })

  // Delete handler
  const handleDelete = async (leaveId: number) => {
    if (!confirm('Delete this leave request?')) return
    const res = await deleteLeaveRequest(leaveId)
    if (res.error) { alert(res.error); return }
    const from = fmtDate(viewStart)
    const to = fmtDate(viewEnd)
    const [calRes, allRes] = await Promise.all([
      getLeaveCalendar({ date_from: from, date_to: to }),
      getLeaveRequests(),
    ])
    setCalLeave(calRes.data || [])
    setAllLeave(allRes.data || [])
    if (onRefresh) onRefresh()
  }

  const isManager = currentUserRole === 'owner' || currentUserRole === 'manager'

  // Compute date range for current view
  const { viewStart, viewEnd } = useMemo(() => {
    if (calView === 'day') {
      return { viewStart: new Date(refDate), viewEnd: new Date(refDate) }
    } else if (calView === 'week') {
      const s = startOfWeek(refDate)
      return { viewStart: s, viewEnd: addDays(s, 6) }
    } else {
      // Month view: show full weeks that cover the month
      const ms = startOfMonth(refDate)
      const me = endOfMonth(refDate)
      const s = startOfWeek(ms)
      const e = addDays(startOfWeek(addDays(me, 6)), 6) // end of last week
      return { viewStart: s, viewEnd: e }
    }
  }, [calView, refDate])

  // Load calendar data when range changes
  useEffect(() => {
    setLoading(true)
    const from = fmtDate(viewStart)
    const to = fmtDate(viewEnd)
    Promise.all([
      getLeaveCalendar({ date_from: from, date_to: to }),
      getLeaveRequests(),
    ]).then(([calRes, allRes]) => {
      setCalLeave(calRes.data || [])
      setAllLeave(allRes.data || [])
      setLoading(false)
    })
  }, [viewStart, viewEnd])

  // Navigation
  const navigate = (dir: -1 | 1) => {
    if (calView === 'day') setRefDate(addDays(refDate, dir))
    else if (calView === 'week') setRefDate(addDays(refDate, dir * 7))
    else setRefDate(new Date(refDate.getFullYear(), refDate.getMonth() + dir, 1))
  }

  const goToday = () => setRefDate(new Date())

  // Get leave entries for a specific day
  const leaveForDay = (day: Date): any[] => {
    const ds = fmtDate(day)
    return calLeave.filter(l => ds >= l.start_date && ds <= l.end_date)
  }

  // Toggle date selection
  const toggleDate = (day: Date) => {
    const ds = fmtDate(day)
    const today = fmtDate(new Date())
    if (ds < today) return // can't select past dates
    setSelectedDates(prev => {
      const next = new Set(prev)
      if (next.has(ds)) next.delete(ds)
      else next.add(ds)
      return next
    })
  }

  // Open request modal
  const openRequestModal = () => {
    if (selectedDates.size === 0) return
    const sorted = Array.from(selectedDates).sort()
    setReqForm({
      leave_type: 'ANNUAL',
      reason: '',
      staff: isManager ? '' : String(currentUserStaffId || ''),
    })
    setReqError('')
    setShowRequestModal(true)
  }

  // Submit leave request
  const submitRequest = async () => {
    const sorted = Array.from(selectedDates).sort()
    if (sorted.length === 0) return
    const staffId = isManager && reqForm.staff ? Number(reqForm.staff) : currentUserStaffId
    if (!staffId) { setReqError('Please select a staff member.'); return }
    setReqSaving(true)
    setReqError('')
    const res = await createLeaveRequest({
      staff: staffId,
      leave_type: reqForm.leave_type,
      start_date: sorted[0],
      end_date: sorted[sorted.length - 1],
      reason: reqForm.reason,
    })
    if (res.error) {
      setReqError(res.error)
      setReqSaving(false)
      return
    }
    setReqSaving(false)
    setShowRequestModal(false)
    setSelectedDates(new Set())
    // Reload
    const from = fmtDate(viewStart)
    const to = fmtDate(viewEnd)
    const [calRes, allRes] = await Promise.all([
      getLeaveCalendar({ date_from: from, date_to: to }),
      getLeaveRequests(),
    ])
    setCalLeave(calRes.data || [])
    setAllLeave(allRes.data || [])
    if (onRefresh) onRefresh()
  }

  // Approve / Decline
  const handleReview = async (leaveId: number, decision: 'APPROVED' | 'REJECTED') => {
    const res = await reviewLeave(leaveId, decision)
    if (res.error) { alert(res.error); return }
    // Reload
    const from = fmtDate(viewStart)
    const to = fmtDate(viewEnd)
    const [calRes, allRes] = await Promise.all([
      getLeaveCalendar({ date_from: from, date_to: to }),
      getLeaveRequests(),
    ])
    setCalLeave(calRes.data || [])
    setAllLeave(allRes.data || [])
    if (onRefresh) onRefresh()
  }

  // Hover handler
  const handleDayHover = (e: React.MouseEvent, day: Date) => {
    const entries = leaveForDay(day)
    if (entries.length === 0) { setHoverDay(null); return }
    setHoverDay(fmtDate(day))
    setHoverPos({ x: e.clientX, y: e.clientY })
  }

  // Build calendar grid days
  const calendarDays = useMemo(() => {
    const days: Date[] = []
    let current = new Date(viewStart)
    const end = new Date(viewEnd)
    while (current <= end) {
      days.push(new Date(current))
      current = addDays(current, 1)
    }
    return days
  }, [viewStart, viewEnd])

  // Pending leave for review panel
  const pendingLeave = allLeave.filter(l => l.status === 'PENDING')

  const todayStr = fmtDate(new Date())
  const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div>
      {/* Controls bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['month', 'week', 'day'] as CalView[]).map(v => (
            <button key={v} className={`btn btn-sm ${calView === v ? 'btn-primary' : ''}`} onClick={() => setCalView(v)} style={{ textTransform: 'capitalize' }}>{v}</button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          <button className="btn btn-sm" onClick={() => navigate(-1)}>&larr;</button>
          <button className="btn btn-sm" onClick={goToday}>Today</button>
          <button className="btn btn-sm" onClick={() => navigate(1)}>&rarr;</button>
        </div>
        <span style={{ fontWeight: 600, fontSize: '1rem', marginLeft: 8 }}>
          {calView === 'month' ? monthLabel(refDate) : calView === 'week' ? `${britishDate(viewStart)} — ${britishDate(viewEnd)}` : britishDate(refDate)}
        </span>
        <div style={{ flex: 1 }} />
        {selectedDates.size > 0 && (
          <button className="btn btn-primary" onClick={openRequestModal}>
            Request Leave ({selectedDates.size} day{selectedDates.size !== 1 ? 's' : ''})
          </button>
        )}
        {selectedDates.size > 0 && (
          <button className="btn btn-sm" onClick={() => setSelectedDates(new Set())}>Clear</button>
        )}
      </div>

      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 12 }}>
        Click dates to select them, then press &ldquo;Request Leave&rdquo;. Coloured days show existing bookings — hover to see who.
      </p>

      {/* Calendar grid */}
      {calView === 'month' || calView === 'week' ? (
        <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', overflow: 'hidden', marginBottom: 16 }}>
          {/* Day headers */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: '1px solid var(--color-border)' }}>
            {DAY_NAMES.map(d => (
              <div key={d} style={{ padding: '6px 8px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textAlign: 'center', background: 'var(--color-bg-muted)' }}>{d}</div>
            ))}
          </div>
          {/* Weeks */}
          {(() => {
            const weeks: Date[][] = []
            for (let i = 0; i < calendarDays.length; i += 7) {
              weeks.push(calendarDays.slice(i, i + 7))
            }
            return weeks.map((week, wi) => (
              <div key={wi} style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: wi < weeks.length - 1 ? '1px solid var(--color-border)' : 'none' }}>
                {week.map(day => {
                  const ds = fmtDate(day)
                  const entries = leaveForDay(day)
                  const isToday = ds === todayStr
                  const isPast = ds < todayStr
                  const isSelected = selectedDates.has(ds)
                  const isCurrentMonth = calView === 'month' ? day.getMonth() === refDate.getMonth() : true
                  const hasApproved = entries.some(e => e.status === 'APPROVED')
                  const hasPending = entries.some(e => e.status === 'PENDING')

                  let bgColor = 'transparent'
                  if (isSelected) bgColor = '#dbeafe'
                  else if (hasApproved) bgColor = LEAVE_COLOURS.APPROVED.bg
                  else if (hasPending) bgColor = LEAVE_COLOURS.PENDING.bg

                  return (
                    <div
                      key={ds}
                      onClick={() => !isPast && toggleDate(day)}
                      onMouseEnter={e => handleDayHover(e, day)}
                      onMouseMove={e => { if (entries.length > 0) setHoverPos({ x: e.clientX, y: e.clientY }) }}
                      onMouseLeave={() => setHoverDay(null)}
                      style={{
                        minHeight: calView === 'week' ? 80 : 56,
                        padding: '4px 6px',
                        cursor: isPast ? 'default' : 'pointer',
                        opacity: isCurrentMonth ? 1 : 0.35,
                        backgroundColor: bgColor,
                        borderRight: '1px solid var(--color-border)',
                        position: 'relative',
                        transition: 'background-color 0.15s',
                      }}
                    >
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: isToday ? 700 : 400,
                        color: isToday ? 'var(--color-primary)' : isPast ? 'var(--color-text-muted)' : 'var(--color-text)',
                        marginBottom: 2,
                      }}>
                        {day.getDate()}
                      </div>
                      {/* Leave chips */}
                      {entries.slice(0, 3).map((entry, ei) => {
                        const colours = LEAVE_COLOURS[entry.status] || LEAVE_COLOURS.PENDING
                        return (
                          <div key={ei} style={{
                            fontSize: '0.65rem',
                            lineHeight: 1.2,
                            padding: '1px 4px',
                            borderRadius: 3,
                            marginBottom: 1,
                            backgroundColor: colours.bg,
                            color: colours.text,
                            borderLeft: `2px solid ${colours.border}`,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}>
                            {entry.staff_name?.split(' ')[0]}
                          </div>
                        )
                      })}
                      {entries.length > 3 && (
                        <div style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>+{entries.length - 3} more</div>
                      )}
                    </div>
                  )
                })}
              </div>
            ))
          })()}
        </div>
      ) : (
        /* Day view */
        <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 16, marginBottom: 16 }}>
          <h3 style={{ marginBottom: 12 }}>{britishDate(refDate)}</h3>
          {(() => {
            const entries = leaveForDay(refDate)
            if (entries.length === 0) return <div className="empty-state">No leave booked for this day</div>
            return entries.map((entry: any, i: number) => {
              const colours = LEAVE_COLOURS[entry.status] || LEAVE_COLOURS.PENDING
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 12px', marginBottom: 8,
                  borderRadius: 'var(--radius)', backgroundColor: colours.bg,
                  borderLeft: `3px solid ${colours.border}`,
                }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{entry.staff_name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                      {TYPE_LABELS[entry.leave_type] || entry.leave_type} &middot; {entry.start_date} to {entry.end_date} ({entry.duration_days} day{entry.duration_days !== 1 ? 's' : ''})
                    </div>
                    {entry.reason && <div style={{ fontSize: '0.82rem', marginTop: 4 }}>{entry.reason}</div>}
                  </div>
                  <span className={`badge ${entry.status === 'APPROVED' ? 'badge-success' : 'badge-warning'}`}>{entry.status}</span>
                </div>
              )
            })
          })()}
          <div style={{ marginTop: 12 }}>
            <button className="btn btn-sm" onClick={() => { toggleDate(refDate) }}>
              {selectedDates.has(fmtDate(refDate)) ? 'Deselect this day' : 'Select this day for leave'}
            </button>
          </div>
        </div>
      )}

      {/* Hover tooltip */}
      {hoverDay && (() => {
        const entries = calLeave.filter(l => hoverDay >= l.start_date && hoverDay <= l.end_date)
        if (entries.length === 0) return null
        return (
          <div style={{
            position: 'fixed',
            left: hoverPos.x + 12,
            top: hoverPos.y - 10,
            zIndex: 1000,
            backgroundColor: '#1e293b',
            color: '#f8fafc',
            padding: '8px 12px',
            borderRadius: 6,
            fontSize: '0.82rem',
            maxWidth: 260,
            pointerEvents: 'none',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Leave on this day:</div>
            {entries.map((e: any, i: number) => (
              <div key={i} style={{ marginBottom: 2 }}>
                <span style={{ fontWeight: 500 }}>{e.staff_name}</span>
                <span style={{ opacity: 0.7, marginLeft: 6 }}>
                  {TYPE_LABELS[e.leave_type] || e.leave_type}
                  {' '}&middot;{' '}
                  <span style={{ color: e.status === 'APPROVED' ? '#86efac' : '#fde68a' }}>{e.status}</span>
                </span>
              </div>
            ))}
          </div>
        )
      })()}

      {/* Pending leave review panel (managers/owners only) */}
      {isManager && pendingLeave.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 8, fontSize: '1rem' }}>Pending Leave Requests</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Staff</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {pendingLeave.map((l: any) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600 }}>{l.staff_name}</td>
                    <td>{TYPE_LABELS[l.leave_type] || l.leave_type}</td>
                    <td>{l.start_date}</td>
                    <td>{l.end_date}</td>
                    <td>{l.duration_days}</td>
                    <td style={{ maxWidth: 200, fontSize: '0.85rem' }}>{l.reason || '—'}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <button className="btn btn-sm btn-primary" onClick={() => handleReview(l.id, 'APPROVED')} style={{ marginRight: 6 }}>Approve</button>
                      <button className="btn btn-sm btn-danger" onClick={() => handleReview(l.id, 'REJECTED')}>Decline</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* All leave list */}
      <div>
        <h3 style={{ marginBottom: 8, fontSize: '1rem' }}>All Leave Requests</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Staff</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th>{isManager && <th>Actions</th>}</tr>
            </thead>
            <tbody>
              {allLeave.map((l: any) => (
                <tr key={l.id}>
                  <td style={{ fontWeight: 600 }}>{l.staff_name}</td>
                  <td>{TYPE_LABELS[l.leave_type] || l.leave_type}</td>
                  <td>{l.start_date}</td>
                  <td>{l.end_date}</td>
                  <td>{l.duration_days}</td>
                  <td style={{ maxWidth: 200, fontSize: '0.85rem' }}>{l.reason || '—'}</td>
                  <td>
                    <span className={`badge ${l.status === 'APPROVED' ? 'badge-success' : l.status === 'PENDING' ? 'badge-warning' : 'badge-danger'}`}>
                      {l.status}
                    </span>
                  </td>
                  {isManager && (
                    <td>
                      <button className="btn btn-sm btn-danger" onClick={() => handleDelete(l.id)}>Delete</button>
                    </td>
                  )}
                </tr>
              ))}
              {allLeave.length === 0 && <tr><td colSpan={isManager ? 8 : 7} className="empty-state">No leave requests yet</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {/* Request Leave Modal */}
      {showRequestModal && (
        <div className="modal-overlay" onClick={() => setShowRequestModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
            <h2 style={{ marginBottom: 12 }}>Request Leave</h2>
            {reqError && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{reqError}</div>}
            <div style={{ background: 'var(--color-primary-light)', borderRadius: 'var(--radius)', padding: '12px 16px', marginBottom: 16, fontSize: '0.9rem' }}>
              <strong>Selected dates:</strong> {Array.from(selectedDates).sort().join(', ')}
              <br />
              <strong>Total:</strong> {selectedDates.size} day{selectedDates.size !== 1 ? 's' : ''}
            </div>
            <div style={{ display: 'grid', gap: 12 }}>
              {isManager && (
                <div>
                  <label className="form-label">Staff Member *</label>
                  <select className="form-input" value={reqForm.staff} onChange={e => setReqForm({ ...reqForm, staff: e.target.value })}>
                    <option value="">Select staff…</option>
                    {staff.map((s: any) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label className="form-label">Leave Type</label>
                <select className="form-input" value={reqForm.leave_type} onChange={e => setReqForm({ ...reqForm, leave_type: e.target.value })}>
                  <option value="ANNUAL">Annual Leave</option>
                  <option value="SICK">Sick Leave</option>
                  <option value="UNPAID">Unpaid Leave</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label className="form-label">Reason (optional)</label>
                <input className="form-input" value={reqForm.reason} onChange={e => setReqForm({ ...reqForm, reason: e.target.value })} placeholder="e.g. Family holiday" />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowRequestModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={submitRequest} disabled={reqSaving}>{reqSaving ? 'Submitting…' : 'Request Leave'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
