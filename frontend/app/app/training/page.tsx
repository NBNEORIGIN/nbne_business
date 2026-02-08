'use client'

import { useEffect, useState } from 'react'
import { getTrainingRecords } from '@/lib/api'

export default function TrainingPage() {
  const [records, setRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getTrainingRecords().then(r => { setRecords(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading training records…</div>

  return (
    <div>
      <div className="page-header"><h1>Training Records</h1><span className="badge badge-success">Tier 2</span></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Staff</th><th>Course</th><th>Provider</th><th>Completed</th><th>Expiry</th><th>Status</th></tr></thead>
          <tbody>
            {records.map((t: any) => (
              <tr key={t.id}>
                <td style={{ fontWeight: 600 }}>{t.staff_name}</td>
                <td>{t.title}</td>
                <td>{t.provider}</td>
                <td>{t.completed_date}</td>
                <td>{t.expiry_date || 'N/A'}</td>
                <td><span className={`badge ${t.is_expired ? 'badge-danger' : 'badge-success'}`}>{t.is_expired ? 'EXPIRED' : 'VALID'}</span></td>
              </tr>
            ))}
            {records.length === 0 && <tr><td colSpan={6} className="empty-state">No training records</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
