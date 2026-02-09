'use client'

import { useEffect, useState } from 'react'
import { getTimesheetSummary } from '@/lib/api'

export default function AdminSchedulePage() {
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('weekly')
  const [refDate, setRefDate] = useState(() => new Date().toISOString().split('T')[0])
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const load = async (p?: string, d?: string) => {
    setLoading(true)
    const res = await getTimesheetSummary({ period: p || period, date: d || refDate })
    setData(res.data || null)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const changePeriod = (p: 'daily' | 'weekly' | 'monthly') => {
    setPeriod(p)
    load(p, refDate)
  }

  const navigate = (dir: -1 | 1) => {
    const d = new Date(refDate)
    if (period === 'daily') d.setDate(d.getDate() + dir)
    else if (period === 'weekly') d.setDate(d.getDate() + dir * 7)
    else d.setMonth(d.getMonth() + dir)
    const newDate = d.toISOString().split('T')[0]
    setRefDate(newDate)
    load(period, newDate)
  }

  const grandTotals = data?.staff_summaries?.reduce((acc: any, s: any) => ({
    scheduled: acc.scheduled + (s.scheduled_hours || 0),
    actual: acc.actual + (s.actual_hours || 0),
    worked: acc.worked + (s.days_worked || 0),
    absent: acc.absent + (s.days_absent || 0),
    sick: acc.sick + (s.days_sick || 0),
    holiday: acc.holiday + (s.days_holiday || 0),
  }), { scheduled: 0, actual: 0, worked: 0, absent: 0, sick: 0, holiday: 0 })

  return (
    <div>
      <div className="page-header"><h1>Timesheet Dashboard</h1><span className="badge badge-danger">Tier 3</span></div>

      {/* Period selector + navigation */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="tabs" style={{ marginBottom: 0 }}>
          {(['daily', 'weekly', 'monthly'] as const).map(p => (
            <button key={p} className={`tab ${period === p ? 'active' : ''}`} onClick={() => changePeriod(p)}>{p.charAt(0).toUpperCase() + p.slice(1)}</button>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="btn btn-sm" onClick={() => navigate(-1)}>&larr;</button>
          <input type="date" className="form-input" value={refDate} onChange={e => { setRefDate(e.target.value); load(period, e.target.value) }} style={{ width: 160 }} />
          <button className="btn btn-sm" onClick={() => navigate(1)}>&rarr;</button>
        </div>
        {data && <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>{data.date_from} to {data.date_to}</span>}
      </div>

      {loading && <div className="empty-state">Loading…</div>}

      {!loading && data && (
        <>
          {/* Summary cards */}
          {grandTotals && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-primary)' }}>{grandTotals.scheduled.toFixed(1)}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Scheduled Hours</div>
              </div>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-success)' }}>{grandTotals.actual.toFixed(1)}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Actual Hours</div>
              </div>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: (grandTotals.actual - grandTotals.scheduled) < 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>{(grandTotals.actual - grandTotals.scheduled) > 0 ? '+' : ''}{(grandTotals.actual - grandTotals.scheduled).toFixed(1)}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Variance</div>
              </div>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{grandTotals.worked}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Days Worked</div>
              </div>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-danger)' }}>{grandTotals.absent + grandTotals.sick}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Absent / Sick</div>
              </div>
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--color-info)' }}>{grandTotals.holiday}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Holiday</div>
              </div>
            </div>
          )}

          {/* Per-staff breakdown */}
          {data.staff_summaries?.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Staff</th>
                    <th>Sched. Hrs</th>
                    <th>Actual Hrs</th>
                    <th>Variance</th>
                    <th>Days Worked</th>
                    <th>Absent</th>
                    <th>Sick</th>
                    <th>Holiday</th>
                  </tr>
                </thead>
                <tbody>
                  {data.staff_summaries.map((s: any) => (
                    <tr key={s.staff_id}>
                      <td style={{ fontWeight: 600 }}>{s.staff_name}</td>
                      <td>{s.scheduled_hours.toFixed(1)}h</td>
                      <td>{s.actual_hours.toFixed(1)}h</td>
                      <td style={{ color: s.variance_hours < 0 ? 'var(--color-danger)' : s.variance_hours > 0 ? 'var(--color-success)' : 'inherit', fontWeight: s.variance_hours !== 0 ? 600 : 400 }}>
                        {s.variance_hours !== 0 ? `${s.variance_hours > 0 ? '+' : ''}${s.variance_hours.toFixed(1)}h` : '—'}
                      </td>
                      <td>{s.days_worked}</td>
                      <td>{s.days_absent || '—'}</td>
                      <td>{s.days_sick || '—'}</td>
                      <td>{s.days_holiday || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No timesheet data for this period. Go to Staff &rarr; Working Hours to set schedules, then generate timesheets.</div>
          )}

          {/* Detailed entries per staff (expandable) */}
          {data.staff_summaries?.map((s: any) => (
            s.entries?.length > 0 && (
              <details key={s.staff_id} style={{ marginTop: 16 }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600, padding: '0.5rem 0' }}>{s.staff_name} — {s.entries.length} entries</summary>
                <div className="table-wrap" style={{ marginTop: 8 }}>
                  <table>
                    <thead><tr><th>Date</th><th>Sched.</th><th>Actual</th><th>Hrs</th><th>Status</th><th>Notes</th></tr></thead>
                    <tbody>
                      {s.entries.map((e: any) => (
                        <tr key={e.id}>
                          <td style={{ fontWeight: 600 }}>{e.date}</td>
                          <td>{e.scheduled_start?.slice(0, 5) || '—'}–{e.scheduled_end?.slice(0, 5) || '—'}</td>
                          <td>{e.actual_start?.slice(0, 5) || '—'}–{e.actual_end?.slice(0, 5) || '—'}</td>
                          <td>{e.actual_hours ? `${Number(e.actual_hours).toFixed(1)}h` : `${Number(e.scheduled_hours).toFixed(1)}h`}</td>
                          <td><span className={`badge ${e.status === 'WORKED' ? 'badge-success' : e.status === 'ABSENT' || e.status === 'SICK' ? 'badge-danger' : e.status === 'LATE' || e.status === 'LEFT_EARLY' ? 'badge-warning' : 'badge-neutral'}`}>{e.status_display || e.status}</span></td>
                          <td style={{ color: 'var(--color-text-muted)', maxWidth: 200 }}>{e.notes || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )
          ))}
        </>
      )}
    </div>
  )
}
