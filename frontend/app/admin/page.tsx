'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getDashboardToday, logBusinessEvent, getTodayResolved, parseAssistantCommand, getPayrollSummary, getLeaveRequests, reviewLeave, getTrainingReminders } from '@/lib/api'

interface DashboardAction {
  label: string
  reason: string
  link: string
  rank: number
  staff_id?: number
}

interface DashboardEvent {
  event_type: string
  severity: string
  summary: string
  detail: string
  why_it_matters?: string
  actions: DashboardAction[]
  entity_type: string
  entity_id: number | null
  timestamp: string
}

interface DashboardData {
  state: 'sorted' | 'active'
  message: string
  events: DashboardEvent[]
  summary: { total: number; critical: number; high: number; warning: number; info: number }
}

interface ResolvedEvent {
  id: number
  event_type: string
  event_type_display: string
  action_label: string
  action_detail: string
  source_event_type: string
  performed_by: string
  created_at: string
}

// Map source event types to BusinessEvent types for logging
const ACTION_EVENT_MAP: Record<string, string> = {
  staff_sick: 'COVER_REQUESTED',
  booking_unassigned: 'BOOKING_ASSIGNED',
  booking_cancelled: 'BOOKING_CANCELLED',
  deposit_missing: 'PAYMENT_REQUESTED',
  leave_pending: 'LEAVE_APPROVED',
  compliance_expiry: 'COMPLIANCE_COMPLETED',
  incident_open: 'INCIDENT_RESOLVED',
}

// Priority ordering: structural > unassigned > revenue > admin
const PRIORITY_ORDER: Record<string, number> = {
  staff_sick: 1,
  booking_unassigned: 2,
  deposit_missing: 3,
  booking_cancelled: 4,
  leave_pending: 5,
  compliance_expiry: 6,
  incident_open: 7,
}

// Priority border colour
function priorityColor(eventType: string): string {
  if (['staff_sick', 'booking_unassigned'].includes(eventType)) return '#ef4444'
  if (['deposit_missing', 'booking_cancelled'].includes(eventType)) return '#f59e0b'
  return '#d1d5db'
}

// Merge detail + why_it_matters into single tight sentence
function situationText(evt: DashboardEvent): string {
  const why = evt.why_it_matters || ''
  if (!why) return evt.detail
  // If detail already contains the why info, just return detail
  if (evt.detail.toLowerCase().includes(why.toLowerCase().slice(0, 20))) return evt.detail
  return `${evt.detail.replace(/\.\s*$/, '')} \u2014 ${why.replace(/\.\s*$/, '').toLowerCase()}.`
}

// Formatted date: "Today — Mon 16 Feb"
function formattedDate(): string {
  const d = new Date()
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `Today \u2014 ${days[d.getDay()]} ${d.getDate()} ${months[d.getMonth()]}`
}

// Demo snapshot data (will be replaced by API when available)
const DEMO_STAFF = [
  { name: 'Sam', hours: '09:00 \u2013 17:00', off: false },
  { name: 'Jordan', hours: '10:00 \u2013 18:00', off: false },
  { name: 'Alex', hours: '09:00 \u2013 15:00', off: false },
  { name: 'Morgan', hours: '11:00 \u2013 19:00', off: false },
  { name: 'Taylor', hours: '09:00 \u2013 17:00', off: false },
  { name: 'Chloe', hours: 'Sick', off: true },
]

// Demo timeline density (09:00–18:00, 36 quarter-hour blocks)
function buildTimelineDensity(): number[] {
  const slots = [
    [9,0,9,45],[9,15,10,0],[10,0,11,0],[10,30,11,30],
    [11,0,12,0],[11,30,12,30],[12,0,13,0],
    [13,0,14,0],[13,30,14,30],[14,0,15,0],[14,0,14,45],
    [15,0,16,0],[15,30,16,30],[16,0,17,0],
    [16,30,17,30],[17,0,18,0],[17,0,17,45],[17,30,18,0],
  ]
  const blocks = 36
  const density = new Array(blocks).fill(0)
  slots.forEach(([sh, sm, eh, em]) => {
    const startBlock = Math.max(0, Math.floor(((sh - 9) * 60 + sm) / 15))
    const endBlock = Math.min(blocks, Math.ceil(((eh - 9) * 60 + em) / 15))
    for (let i = startBlock; i < endBlock; i++) density[i]++
  })
  return density
}

export default function AdminDashboard() {
  const router = useRouter()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState<Record<string, string>>({})
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())
  const [resolvedEvents, setResolvedEvents] = useState<ResolvedEvent[]>([])
  const [view, setView] = useState<'active' | 'sorted'>('active')

  // Command bar state
  const [cmdText, setCmdText] = useState('')
  const [cmdResult, setCmdResult] = useState<any>(null)
  const [cmdLoading, setCmdLoading] = useState(false)
  const [cmdFeedback, setCmdFeedback] = useState<string | null>(null)

  // Toast
  const [toast, setToast] = useState<string | null>(null)

  // Snapshot
  const [staffPanelOpen, setStaffPanelOpen] = useState(false)
  const [snapStaffIn] = useState(5)
  const [snapStaffOff] = useState(1)

  // Payroll
  const [payroll, setPayroll] = useState<any>(null)

  // Pending leave
  const [pendingLeave, setPendingLeave] = useState<any[]>([])
  const [leaveReviewing, setLeaveReviewing] = useState<Record<number, boolean>>({})

  // Training reminders
  const [trainingAlerts, setTrainingAlerts] = useState<any[]>([])

  const showToast = useCallback((msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }, [])

  useEffect(() => {
    Promise.all([
      getDashboardToday().catch(() => ({ error: 'fetch failed', data: null })),
      getTodayResolved().catch(() => ({ error: 'fetch failed', data: null })),
      getPayrollSummary().catch(() => ({ error: 'fetch failed', data: null })),
      getLeaveRequests({ status: 'PENDING' }).catch(() => ({ error: 'fetch failed', data: null })),
      getTrainingReminders().catch(() => ({ error: 'fetch failed', data: null })),
    ]).then(([dashRes, resolvedRes, payrollRes, leaveRes, trainingRes]) => {
      if (dashRes.error || !dashRes.data) {
        setData({ state: 'sorted', message: 'All sorted.', events: [], summary: { total: 0, critical: 0, high: 0, warning: 0, info: 0 } })
      } else {
        setData(dashRes.data)
      }
      if (!resolvedRes.error && resolvedRes.data) {
        setResolvedEvents(resolvedRes.data.events || [])
      }
      if (!payrollRes.error && payrollRes.data) {
        setPayroll(payrollRes.data)
      }
      if (!leaveRes.error && leaveRes.data) {
        setPendingLeave(leaveRes.data)
      }
      if (!trainingRes.error && trainingRes.data) {
        setTrainingAlerts(trainingRes.data)
      }
      setLoading(false)
    })
  }, [])

  const handleLeaveReview = async (leaveId: number, decision: 'APPROVED' | 'REJECTED') => {
    setLeaveReviewing(prev => ({ ...prev, [leaveId]: true }))
    const res = await reviewLeave(leaveId, decision)
    if (res.error) { alert(res.error); setLeaveReviewing(prev => ({ ...prev, [leaveId]: false })); return }
    setPendingLeave(prev => prev.filter(l => l.id !== leaveId))
    setLeaveReviewing(prev => { const n = { ...prev }; delete n[leaveId]; return n })
    showToast(`Leave ${decision === 'APPROVED' ? 'approved' : 'declined'}`)
  }

  const evtKey = (evt: DashboardEvent) => `${evt.event_type}-${evt.entity_id}`

  const handleAction = async (evt: DashboardEvent, action: DashboardAction) => {
    const key = evtKey(evt)
    setResolving((prev) => ({ ...prev, [key]: action.label }))

    const eventType = ACTION_EVENT_MAP[evt.event_type] || 'OWNER_OVERRIDE'
    await logBusinessEvent({
      event_type: eventType,
      action_label: action.label,
      source_event_type: evt.event_type,
      source_entity_type: evt.entity_type,
      source_entity_id: evt.entity_id,
      action_detail: action.reason,
      payload: action.staff_id ? { cover_staff_id: action.staff_id } : {},
    })

    setTimeout(async () => {
      setDismissed((prev) => new Set(prev).add(key))
      setResolving((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
      showToast(`\u2192 ${action.label}`)
      const res = await getTodayResolved()
      if (!res.error && res.data) {
        setResolvedEvents(res.data.events || [])
      }
    }, 800)
  }

  const handleCommand = async () => {
    if (!cmdText.trim()) return
    setCmdLoading(true)
    setCmdResult(null)
    setCmdFeedback(null)
    const res = await parseAssistantCommand(cmdText)
    setCmdLoading(false)
    if (!res.error && res.data) {
      setCmdResult(res.data)
    } else {
      setCmdResult({ parsed: false, message: 'Could not process command.' })
    }
  }

  // Staff command → tab navigation map
  const STAFF_CMD_NAV: Record<string, string> = {
    'add_shift': '/admin/staff?tab=shifts',
    'generate_timesheets': '/admin/staff?tab=timesheets',
    'export_timesheets': '/admin/staff?tab=timesheets',
    'add_staff': '/admin/staff?tab=profiles',
    'check_training': '/admin/staff?tab=training',
    'set_hours': '/admin/staff?tab=hours',
    'log_late': '/admin/staff?tab=timesheets',
    'log_sick': '/admin/staff?tab=leave',
    'request_cover': '/admin/staff?tab=shifts',
    'approve_leave': '/admin/staff?tab=leave',
    'decline_leave': '/admin/staff?tab=leave',
  }

  const handleCommandConfirm = async () => {
    if (!cmdResult?.intent) return
    const intent = cmdResult.intent
    await logBusinessEvent({
      event_type: intent.event_type,
      action_label: intent.original_text,
      action_detail: intent.description,
      payload: { ...intent.entities, source: 'assistant_command' },
    })
    const feedback = intent.description || 'Action confirmed.'
    setCmdResult(null)
    setCmdText('')
    setCmdFeedback(feedback)
    setTimeout(() => setCmdFeedback(null), 3000)
    const res = await getTodayResolved()
    if (!res.error && res.data) {
      setResolvedEvents(res.data.events || [])
    }
    // Navigate to relevant Staff tab if this is a staff command
    const navTarget = STAFF_CMD_NAV[intent.action]
    if (navTarget) {
      setTimeout(() => router.push(navTarget), 800)
    }
  }

  if (loading) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Loading\u2026
    </div>
  )
  if (error) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Dashboard unavailable.
    </div>
  )
  if (!data) return null

  const visibleEvents = data.events
    .filter((e) => !dismissed.has(evtKey(e)))
    .sort((a, b) => (PRIORITY_ORDER[a.event_type] || 99) - (PRIORITY_ORDER[b.event_type] || 99))
    .slice(0, 5)
  const activeCount = visibleEvents.length
  const allSorted = data.state === 'sorted' || activeCount === 0
  const sortedCount = resolvedEvents.length

  // Impact calculations
  const revenueAtRisk = visibleEvents.reduce((sum, e) => {
    if (e.event_type === 'deposit_missing') return sum + 85
    return sum
  }, 0)
  const bookingsAffected = visibleEvents.reduce((sum, e) => {
    if (e.event_type === 'staff_sick') return sum + 4
    if (e.event_type === 'booking_unassigned') return sum + 1
    return sum
  }, 0)

  const tog = (on: boolean): React.CSSProperties => ({
    padding: '0.3rem 0.85rem', borderRadius: 5,
    border: '1px solid #d1d5db',
    backgroundColor: on ? '#111827' : '#fff',
    color: on ? '#fff' : '#6b7280',
    fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
  })

  const density = buildTimelineDensity()

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', position: 'relative' }}>

      {/* ── Command area ── */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{
          display: 'flex', gap: '0.5rem',
          padding: '0.6rem 0.75rem', borderRadius: 8,
          border: '1px solid #e5e7eb', backgroundColor: '#fff',
        }}>
          <input
            type="text"
            value={cmdText}
            onChange={(e) => setCmdText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
            placeholder="Type what happened or what you want to do\u2026"
            style={{
              flex: 1, border: 'none', outline: 'none', fontSize: '0.9rem',
              color: '#111827', backgroundColor: 'transparent',
            }}
          />
          <button
            onClick={handleCommand}
            disabled={cmdLoading || !cmdText.trim()}
            style={{
              padding: '0.35rem 0.75rem', borderRadius: 5, border: 'none',
              backgroundColor: '#111827', color: '#fff',
              fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
              opacity: cmdLoading || !cmdText.trim() ? 0.4 : 1,
            }}
          >
            {cmdLoading ? '\u2026' : 'Go'}
          </button>
        </div>

        {/* Compact assistant strip */}
        {cmdResult && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.6rem',
            padding: '0.4rem 0.75rem', marginTop: '0.35rem',
            fontSize: '0.85rem', color: '#374151',
          }}>
            <span style={{ flex: 1 }}>
              {cmdResult.parsed ? cmdResult.confirmation_message : cmdResult.message}
            </span>
            {cmdResult.parsed && (
              <>
                <button
                  onClick={handleCommandConfirm}
                  style={{
                    padding: '0.25rem 0.65rem', borderRadius: 4, border: 'none',
                    backgroundColor: '#111827', color: '#fff',
                    fontSize: '0.78rem', fontWeight: 500, cursor: 'pointer',
                  }}
                >
                  {cmdResult.intent?.event_type === 'STAFF_SICK' ? 'Confirm absence' : 'Confirm'}
                </button>
                <button
                  onClick={() => { setCmdResult(null); setCmdText('') }}
                  style={{
                    fontSize: '0.78rem', color: '#9ca3af', cursor: 'pointer',
                    border: 'none', background: 'none',
                  }}
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        )}

        {/* Post-confirm feedback */}
        {cmdFeedback && (
          <div style={{
            padding: '0.4rem 0.75rem', marginTop: '0.35rem',
            fontSize: '0.85rem', color: '#059669', fontWeight: 500,
          }}>
            {cmdFeedback}
          </div>
        )}
      </div>

      {/* ── Operational Snapshot ── */}
      <div style={{
        display: 'flex', alignItems: 'stretch',
        border: '1px solid #e5e7eb', borderRadius: 8, backgroundColor: '#fff',
        marginBottom: staffPanelOpen ? 0 : '1rem', overflow: 'hidden',
      }}>
        {[
          { label: 'Staff In', value: String(snapStaffIn), cls: '', click: true },
          { label: 'Staff Off', value: String(snapStaffOff), cls: snapStaffOff > 0 ? 'danger' : '', click: true },
          { label: 'Bookings', value: '18', sub: '(78%)', cls: '' },
          { label: 'Revenue Today', value: '\u00A31,240', cls: '' },
          { label: 'Gaps', value: '3', sub: 'empty slots', cls: 'warn' },
        ].map((cell, i) => (
          <div
            key={i}
            onClick={cell.click ? () => setStaffPanelOpen(!staffPanelOpen) : undefined}
            style={{
              flex: 1, padding: '0.55rem 0.75rem', textAlign: 'center',
              borderRight: i < 4 ? '1px solid #f3f4f6' : 'none',
              cursor: cell.click ? 'pointer' : 'default',
            }}
          >
            <div style={{
              fontSize: '0.65rem', fontWeight: 600, color: '#9ca3af',
              textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.15rem',
            }}>
              {cell.label}
            </div>
            <div style={{
              fontSize: '1.05rem', fontWeight: 700, lineHeight: 1.2,
              color: cell.cls === 'danger' ? '#ef4444' : cell.cls === 'warn' ? '#f59e0b' : '#111827',
            }}>
              {cell.value}
              {cell.sub && (
                <span style={{ fontSize: '0.72rem', fontWeight: 400, color: '#9ca3af', marginLeft: '0.2rem' }}>
                  {cell.sub}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Staff expand panel */}
      {staffPanelOpen && (
        <div style={{
          padding: '0.5rem 0.75rem',
          border: '1px solid #e5e7eb', borderTop: 'none',
          borderRadius: '0 0 8px 8px', backgroundColor: '#fafafa',
          marginBottom: '1rem',
        }}>
          {DEMO_STAFF.map((s, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between',
              fontSize: '0.82rem', padding: '0.2rem 0',
              color: s.off ? '#ef4444' : '#374151',
            }}>
              <span>{s.name}</span>
              <span style={{ fontSize: '0.78rem', color: s.off ? '#ef4444' : '#9ca3af' }}>{s.hours}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Mini Timeline 09:00–18:00 ── */}
      <div style={{
        display: 'flex', height: 18, borderRadius: 4, overflow: 'hidden',
        marginBottom: '0.15rem', backgroundColor: '#f3f4f6',
      }}>
        {density.map((d, i) => (
          <div key={i} style={{
            width: `${(100 / 36).toFixed(2)}%`, height: '100%',
            backgroundColor: d > 0 ? '#1e293b' : '#e5e7eb',
            opacity: d > 0 ? Math.min(1, 0.3 + d * 0.25) : 1,
          }} />
        ))}
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '0.65rem', color: '#9ca3af', marginBottom: '0.75rem',
      }}>
        {['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00'].map(t => (
          <span key={t}>{t}</span>
        ))}
      </div>

      {/* ── Payroll This Month ── */}
      {payroll && payroll.staff_count > 0 && (
        <div style={{
          border: '1px solid #e5e7eb', borderRadius: 8, backgroundColor: '#fff',
          padding: '0.65rem 0.85rem', marginBottom: '0.75rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Hours This Month — {payroll.month_display}
            </div>
            <a href="/admin/staff" style={{ fontSize: '0.75rem', color: '#6b7280', textDecoration: 'underline', textUnderlineOffset: '2px' }}>
              View timesheets →
            </a>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            {(payroll.staff_summaries || []).map((s: any) => (
              <div key={s.staff_id} style={{ minWidth: 90 }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#111827' }}>{s.staff_name}</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#111827' }}>
                  {s.actual_hours > 0 ? `${s.actual_hours}h` : `${s.scheduled_hours}h`}
                  {s.actual_hours > 0 && s.variance_hours !== 0 && (
                    <span style={{ fontSize: '0.75rem', fontWeight: 500, marginLeft: '0.25rem', color: s.variance_hours < 0 ? '#ef4444' : '#16a34a' }}>
                      ({s.variance_hours > 0 ? '+' : ''}{s.variance_hours}h)
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{s.days_worked} days worked</div>
              </div>
            ))}
            <div style={{ minWidth: 90, borderLeft: '1px solid #f3f4f6', paddingLeft: '1rem' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#9ca3af' }}>Total</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#111827' }}>
                {payroll.grand_actual_hours > 0 ? `${payroll.grand_actual_hours}h` : `${payroll.grand_scheduled_hours}h`}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{payroll.staff_count} staff</div>
            </div>
          </div>
        </div>
      )}

      {/* ── Pending Leave Requests ── */}
      {pendingLeave.length > 0 && (
        <div style={{
          border: '1px solid #e5e7eb', borderRadius: 8, backgroundColor: '#fff',
          padding: '0.65rem 0.85rem', marginBottom: '0.75rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Leave Requests Awaiting Review
            </div>
            <a href="/admin/staff" style={{ fontSize: '0.75rem', color: '#6b7280', textDecoration: 'underline', textUnderlineOffset: '2px' }}>
              View calendar \u2192
            </a>
          </div>
          {pendingLeave.map((l: any) => (
            <div key={l.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0.5rem 0', borderBottom: '1px solid #f3f4f6',
              opacity: leaveReviewing[l.id] ? 0.4 : 1,
              transition: 'opacity 0.3s',
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#111827' }}>{l.staff_name}</div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  {l.leave_type === 'ANNUAL' ? 'Annual Leave' : l.leave_type === 'SICK' ? 'Sick Leave' : l.leave_type === 'UNPAID' ? 'Unpaid' : l.leave_type}
                  {' \u00B7 '}{l.start_date} to {l.end_date} ({l.duration_days} day{l.duration_days !== 1 ? 's' : ''})
                </div>
                {l.reason && <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: 2 }}>{l.reason}</div>}
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', marginLeft: '1rem' }}>
                <button
                  onClick={() => handleLeaveReview(l.id, 'APPROVED')}
                  disabled={!!leaveReviewing[l.id]}
                  style={{
                    padding: '0.3rem 0.7rem', borderRadius: 5, border: 'none',
                    backgroundColor: '#16a34a', color: '#fff',
                    fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
                  }}
                >
                  Approve
                </button>
                <button
                  onClick={() => handleLeaveReview(l.id, 'REJECTED')}
                  disabled={!!leaveReviewing[l.id]}
                  style={{
                    padding: '0.3rem 0.7rem', borderRadius: 5, border: '1px solid #e5e7eb',
                    backgroundColor: '#fff', color: '#dc2626',
                    fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
                  }}
                >
                  Decline
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Training Alerts ── */}
      {trainingAlerts.length > 0 && (
        <div style={{
          border: '1px solid #e5e7eb', borderRadius: 8, backgroundColor: '#fff',
          padding: '0.65rem 0.85rem', marginBottom: '0.75rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Training Alerts
            </div>
            <a href="/admin/staff" style={{ fontSize: '0.75rem', color: '#6b7280', textDecoration: 'underline', textUnderlineOffset: '2px' }}>
              View training →
            </a>
          </div>
          {trainingAlerts.slice(0, 5).map((t: any) => {
            const isExpired = t.alert_type === 'expired'
            return (
              <div key={t.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.4rem 0', borderBottom: '1px solid #f3f4f6',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#111827' }}>{t.staff_name}</div>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                    {t.title}
                    {t.is_mandatory && <span style={{ marginLeft: 6, fontSize: '0.7rem', color: '#dc2626', fontWeight: 600 }}>MANDATORY</span>}
                  </div>
                </div>
                <div style={{
                  padding: '0.2rem 0.6rem', borderRadius: 4, fontSize: '0.78rem', fontWeight: 600,
                  backgroundColor: isExpired ? '#fee2e2' : '#fef9c3',
                  color: isExpired ? '#dc2626' : '#a16207',
                }}>
                  {isExpired
                    ? `Expired ${t.days_until_expiry !== null ? Math.abs(t.days_until_expiry) + 'd ago' : ''}`
                    : `Expires in ${t.days_until_expiry}d`
                  }
                </div>
              </div>
            )
          })}
          {trainingAlerts.length > 5 && (
            <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: '0.3rem' }}>
              +{trainingAlerts.length - 5} more alerts
            </div>
          )}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.1rem' }}>
            {formattedDate()}
          </h1>
          <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
            {allSorted
              ? 'All sorted. You\u2019re good.'
              : `${activeCount} thing${activeCount !== 1 ? 's' : ''} need${activeCount === 1 ? 's' : ''} sorting.`
            }
          </div>
          {!allSorted && (revenueAtRisk > 0 || bookingsAffected > 0) && (
            <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.15rem' }}>
              {[
                revenueAtRisk > 0 ? `\u00A3${revenueAtRisk} revenue at risk` : '',
                bookingsAffected > 0 ? `${bookingsAffected} booking${bookingsAffected !== 1 ? 's' : ''} affected` : '',
              ].filter(Boolean).join(' \u00B7 ')}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.35rem', marginTop: '0.35rem' }}>
          <button onClick={() => setView('active')} style={tog(view === 'active')}>Active</button>
          <button onClick={() => setView('sorted')} style={tog(view === 'sorted')}>
            Sorted{sortedCount > 0 ? ` (${sortedCount})` : ''}
          </button>
        </div>
      </div>

      {/* ── Sorted view ── */}
      {view === 'sorted' ? (
        sortedCount === 0 ? (
          <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
            <div style={{ fontSize: '0.95rem', color: '#6b7280' }}>Nothing resolved yet today.</div>
          </div>
        ) : (
          <div>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 140px 100px 80px', gap: '0.75rem',
              padding: '0 0 0.4rem 0', borderBottom: '1px solid #e5e7eb',
            }}>
              {['Action taken', 'Who', 'Type', 'Time'].map((h) => (
                <div key={h} style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</div>
              ))}
            </div>
            {resolvedEvents.map((r) => {
              const time = new Date(r.created_at)
              return (
                <div key={r.id} style={{
                  display: 'grid', gridTemplateColumns: '1fr 140px 100px 80px', gap: '0.75rem',
                  padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6', alignItems: 'baseline',
                }}>
                  <div style={{ fontSize: '0.88rem', color: '#059669', fontWeight: 500 }}>{r.action_label}</div>
                  <div style={{ fontSize: '0.82rem', color: '#6b7280' }}>{r.performed_by}</div>
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{r.event_type_display}</div>
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{time.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              )
            })}
          </div>
        )

      /* ── Active: all clear ── */
      ) : allSorted ? (
        <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
          <div style={{ fontSize: '0.95rem', color: '#374151', fontWeight: 500 }}>All sorted. You&rsquo;re good.</div>
        </div>

      /* ── Active: 3-column rows with priority borders ── */
      ) : (
        <div>
          <div style={{
            display: 'grid', gridTemplateColumns: '2.5fr 1fr 1fr', gap: '0.75rem',
            padding: '0 0 0.4rem 0.75rem', borderBottom: '1px solid #e5e7eb',
          }}>
            {['Situation', 'Action', 'Options'].map((h) => (
              <div key={h} style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</div>
            ))}
          </div>

          {visibleEvents.map((evt, i) => {
            const key = evtKey(evt)
            const isResolving = key in resolving
            const primary = evt.actions[0]
            const secondary = evt.actions.slice(1)

            return (
              <div
                key={`${key}-${i}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '2.5fr 1fr 1fr',
                  gap: '0.75rem',
                  padding: '0.6rem 0 0.6rem 0.75rem',
                  borderBottom: '1px solid #f3f4f6',
                  borderLeft: `3px solid ${priorityColor(evt.event_type)}`,
                  alignItems: 'center',
                  opacity: isResolving ? 0.35 : 1,
                  transition: 'opacity 0.4s ease',
                }}
              >
                {isResolving ? (
                  <div style={{ gridColumn: '1 / -1', fontSize: '0.85rem', color: '#374151' }}>
                    {resolving[key]}
                  </div>
                ) : (
                  <>
                    {/* Situation (merged what + why) */}
                    <div style={{ fontSize: '0.88rem', color: '#111827', lineHeight: 1.4 }}>
                      {situationText(evt)}
                    </div>

                    {/* Primary action with arrow */}
                    <div>
                      {primary && (
                        <button
                          onClick={() => handleAction(evt, primary)}
                          style={{
                            padding: '0.3rem 0.7rem', borderRadius: 5, border: 'none',
                            backgroundColor: '#111827', color: '#fff',
                            fontSize: '0.82rem', fontWeight: 500, cursor: 'pointer',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          &rarr; {primary.label}
                        </button>
                      )}
                    </div>

                    {/* Secondary options */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                      {secondary.map((a, j) => (
                        <span
                          key={j}
                          onClick={() => handleAction(evt, a)}
                          style={{
                            fontSize: '0.78rem', color: '#6b7280', cursor: 'pointer',
                            textDecoration: 'underline', textUnderlineOffset: '2px',
                          }}
                        >
                          {a.label}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
          padding: '0.5rem 1.25rem', borderRadius: 6,
          backgroundColor: '#111827', color: '#fff',
          fontSize: '0.82rem', fontWeight: 500, zIndex: 100,
        }}>
          {toast}
        </div>
      )}
    </div>
  )
}
