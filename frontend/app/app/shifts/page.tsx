'use client'

import { useEffect, useState } from 'react'
import { getMyShifts } from '@/lib/api'

export default function ShiftsPage() {
  const [shifts, setShifts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyShifts().then(r => { setShifts(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading shifts…</div>

  return (
    <div>
      <div className="page-header"><h1>My Shifts</h1><span className="badge badge-success">Tier 2</span></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Staff</th><th>Start</th><th>End</th><th>Hours</th><th>Location</th><th>Notes</th></tr></thead>
          <tbody>
            {shifts.map((s: any) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.date}</td>
                <td>{s.staff_name}</td>
                <td>{s.start_time}</td>
                <td>{s.end_time}</td>
                <td>{s.duration_hours ? `${s.duration_hours}h` : '—'}</td>
                <td>{s.location}</td>
                <td style={{ color: 'var(--color-text-muted)' }}>{s.notes || '—'}</td>
              </tr>
            ))}
            {shifts.length === 0 && <tr><td colSpan={7} className="empty-state">No upcoming shifts</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
