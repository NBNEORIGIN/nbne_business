'use client'

import { useState } from 'react'
import { DEMO_SCHEDULE } from '@/lib/demo-data'
import type { ScheduleDay } from '@/lib/types'

export default function AdminSchedulePage() {
  const [schedule, setSchedule] = useState<ScheduleDay[]>([...DEMO_SCHEDULE])
  const [editing, setEditing] = useState<ScheduleDay | null>(null)

  function saveEdit() {
    if (!editing) return
    setSchedule(prev => prev.map(d => d.day === editing.day ? editing : d))
    setEditing(null)
  }

  return (
    <div>
      <div className="page-header"><h1>Opening Hours</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Day</th><th>Open</th><th>Close</th><th>Slot Duration</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {schedule.map(d => (
              <tr key={d.day}>
                <td style={{ fontWeight: 600 }}>{d.day}</td>
                <td>{d.closed ? '—' : d.open}</td>
                <td>{d.closed ? '—' : d.close}</td>
                <td>{d.slot_duration_minutes} min</td>
                <td><span className={`badge ${d.closed ? 'badge-neutral' : 'badge-success'}`}>{d.closed ? 'Closed' : 'Open'}</span></td>
                <td><button className="btn btn-outline btn-sm" onClick={() => setEditing({ ...d })}>Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: '1rem' }}>Edit — {editing.day}</h2>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input type="checkbox" checked={!editing.closed} onChange={e => setEditing({ ...editing, closed: !e.target.checked })} /> Open this day
              </label>
              {!editing.closed && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div><label>Open</label><input type="time" value={editing.open} onChange={e => setEditing({ ...editing, open: e.target.value })} /></div>
                    <div><label>Close</label><input type="time" value={editing.close} onChange={e => setEditing({ ...editing, close: e.target.value })} /></div>
                  </div>
                  <div><label>Slot Duration (min)</label><input type="number" value={editing.slot_duration_minutes} onChange={e => setEditing({ ...editing, slot_duration_minutes: +e.target.value })} /></div>
                </>
              )}
              <div className="actions-row" style={{ justifyContent: 'flex-end' }}>
                <button className="btn btn-outline" onClick={() => setEditing(null)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveEdit}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
