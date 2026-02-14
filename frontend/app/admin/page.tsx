'use client'

import { useEffect, useState } from 'react'
import { getDashboardToday } from '@/lib/api'

interface DashboardAction {
  label: string
  reason: string
  link: string
  rank: number
}

interface DashboardEvent {
  event_type: string
  severity: string
  summary: string
  detail: string
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

const SEV_BORDER: Record<string, string> = {
  critical: '#ef4444',
  high: '#f59e0b',
  warning: '#d1d5db',
  info: '#d1d5db',
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState<Record<string, string>>({})
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  useEffect(() => {
    getDashboardToday().then((res) => {
      if (res.error) {
        setError(res.error)
      } else {
        setData(res.data)
      }
      setLoading(false)
    })
  }, [])

  const evtKey = (evt: DashboardEvent) => `${evt.event_type}-${evt.entity_id}`

  const handleAction = (evt: DashboardEvent, label: string) => {
    const key = evtKey(evt)
    setResolving((prev) => ({ ...prev, [key]: label }))
    setTimeout(() => {
      setDismissed((prev) => new Set(prev).add(key))
      setResolving((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }, 1500)
  }

  if (loading) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Loading…
    </div>
  )
  if (error) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Dashboard unavailable.
    </div>
  )
  if (!data) return null

  const visibleEvents = data.events.filter(
    (e: DashboardEvent) => !dismissed.has(evtKey(e))
  )
  const isSorted = data.state === 'sorted' || visibleEvents.length === 0

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.2rem' }}>
          Today
        </h1>
        <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>
          {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </div>
      </div>

      {/* ── Sorted state ── */}
      {isSorted ? (
        <div style={{
          padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8,
          border: '1px solid #e5e7eb', backgroundColor: '#fafafa',
        }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 500, color: '#374151' }}>
            All issues resolved. Sorted.
          </div>
        </div>
      ) : (
        <>
          {/* ── Column headers ── */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem',
            padding: '0 0 0.5rem 12px',
            borderBottom: '1px solid #e5e7eb', marginBottom: '0.5rem',
          }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              What happened
            </div>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Action
            </div>
            <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Alternatives
            </div>
          </div>

          {/* ── Issue rows ── */}
          {visibleEvents.map((evt: DashboardEvent, i: number) => {
            const key = evtKey(evt)
            const isResolving = key in resolving
            const borderColor = SEV_BORDER[evt.severity] || '#d1d5db'
            const primary = evt.actions[0]
            const secondary = evt.actions.slice(1)

            return (
              <div
                key={`${key}-${i}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: '1rem',
                  alignItems: 'center',
                  padding: '0.75rem 1rem 0.75rem 0',
                  borderBottom: '1px solid #f3f4f6',
                  borderLeft: `3px solid ${borderColor}`,
                  paddingLeft: '12px',
                  backgroundColor: '#fff',
                  opacity: isResolving ? 0.5 : 1,
                  transition: 'opacity 0.3s ease',
                }}
              >
                {/* Col 1 — What happened */}
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#111827', lineHeight: 1.3 }}>
                    {evt.summary}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.15rem' }}>
                    {evt.detail}
                  </div>
                </div>

                {/* Col 2 — Primary action / feedback */}
                <div>
                  {isResolving ? (
                    <div style={{ fontSize: '0.85rem', color: '#374151', fontWeight: 500 }}>
                      {resolving[key]} — awaiting response
                    </div>
                  ) : primary ? (
                    <div>
                      <button
                        onClick={() => handleAction(evt, primary.label)}
                        style={{
                          padding: '0.45rem 1rem',
                          borderRadius: 5,
                          border: 'none',
                          backgroundColor: '#111827',
                          color: '#fff',
                          fontSize: '0.85rem',
                          fontWeight: 500,
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {primary.label}
                      </button>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                        {primary.reason}
                      </div>
                    </div>
                  ) : null}
                </div>

                {/* Col 3 — Alternatives */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {!isResolving && secondary.map((action: DashboardAction, j: number) => (
                    <button
                      key={j}
                      onClick={() => handleAction(evt, action.label)}
                      style={{
                        padding: '0.3rem 0.65rem',
                        borderRadius: 4,
                        border: '1px solid #d1d5db',
                        backgroundColor: '#fff',
                        color: '#374151',
                        fontSize: '0.78rem',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </>
      )}
    </div>
  )
}
