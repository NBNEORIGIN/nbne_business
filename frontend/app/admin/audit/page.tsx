'use client'

import { useEffect, useState } from 'react'
import { getAuditLog } from '@/lib/api'

export default function AdminAuditPage() {
  const [entries, setEntries] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAuditLog({ limit: 100 }).then(r => { setEntries(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading audit log…</div>

  return (
    <div>
      <div className="page-header"><h1>Audit Log</h1><span className="badge badge-danger">Tier 3 Only</span></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th><th>IP</th></tr></thead>
          <tbody>
            {entries.map((a: any) => (
              <tr key={a.id}>
                <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{new Date(a.timestamp).toLocaleString()}</td>
                <td style={{ fontWeight: 600 }}>{a.user_name || 'System'}</td>
                <td><span className="badge badge-neutral">{a.action}</span></td>
                <td style={{ fontSize: '0.85rem' }}>{a.entity_type}{a.entity_id ? ` #${a.entity_id}` : ''}</td>
                <td style={{ maxWidth: 300, fontSize: '0.85rem' }}>{a.detail || '—'}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{a.ip_address}</td>
              </tr>
            ))}
            {entries.length === 0 && <tr><td colSpan={6} className="empty-state">No audit entries</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
