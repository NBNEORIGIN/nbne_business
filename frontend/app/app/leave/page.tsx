'use client'

import { useEffect, useState } from 'react'
import { getLeaveRequests } from '@/lib/api'

export default function LeavePage() {
  const [leave, setLeave] = useState<any[]>([])
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLeaveRequests().then(r => { setLeave(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading leave requests…</div>

  const filtered = filter === 'ALL' ? leave : leave.filter(l => l.status === filter)

  return (
    <div>
      <div className="page-header"><h1>Leave Requests</h1><span className="badge badge-success">Tier 2</span></div>
      <div className="filter-bar">
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Staff</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.map(l => (
              <tr key={l.id}>
                <td style={{ fontWeight: 600 }}>{l.staff_name}</td>
                <td>{l.leave_type}</td>
                <td>{l.start_date}</td>
                <td>{l.end_date}</td>
                <td>{l.duration_days}</td>
                <td style={{ maxWidth: 200 }}>{l.reason}</td>
                <td><span className={`badge ${l.status === 'APPROVED' ? 'badge-success' : l.status === 'PENDING' ? 'badge-warning' : 'badge-danger'}`}>{l.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
