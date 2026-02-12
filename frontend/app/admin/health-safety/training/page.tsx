'use client'

import { useState, useEffect, useCallback } from 'react'
import { getTrainingList } from '@/lib/api'

type Filter = '' | 'expired' | 'expiring_soon' | 'valid'

function statusBadge(s: string) {
  const map: Record<string, string> = {
    valid: 'badge-success', expiring_soon: 'badge-warning', expired: 'badge-danger',
  }
  return map[s] || 'badge-info'
}

export default function StaffTrainingPage() {
  const [records, setRecords] = useState<any[]>([])
  const [filter, setFilter] = useState<Filter>('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getTrainingList()
    if (res.data) setRecords(res.data)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = filter ? records.filter(r => r.status === filter) : records

  const counts = {
    all: records.length,
    expired: records.filter(r => r.status === 'expired').length,
    expiring_soon: records.filter(r => r.status === 'expiring_soon').length,
    valid: records.filter(r => r.status === 'valid').length,
  }

  // Group by staff member for matrix view
  const byStaff: Record<string, any[]> = {}
  filtered.forEach(r => {
    const name = r.user_name || 'Unknown'
    if (!byStaff[name]) byStaff[name] = []
    byStaff[name].push(r)
  })

  const FILTERS: { key: Filter; label: string; count: number; activeClass?: string }[] = [
    { key: '', label: 'All', count: counts.all },
    { key: 'expired', label: 'Expired', count: counts.expired, activeClass: 'active-danger' },
    { key: 'expiring_soon', label: 'Expiring Soon', count: counts.expiring_soon, activeClass: 'active-warning' },
    { key: 'valid', label: 'Valid', count: counts.valid, activeClass: 'active-success' },
  ]

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>

  return (
    <div>
      <h2 style={{ marginBottom: '0.25rem' }}>Staff Training</h2>
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
        Training certificates and qualifications by staff member.
      </p>

      <div className="tag-filters">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`tag-filter ${filter === f.key ? (f.activeClass || 'active') : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      {Object.keys(byStaff).length === 0 ? (
        <div className="empty-state">No training records found</div>
      ) : (
        Object.entries(byStaff).map(([name, recs]) => (
          <div key={name} style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {name}
              {recs.some(r => r.status === 'expired') && <span className="badge badge-danger">Action needed</span>}
            </h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Training</th>
                    <th>Provider</th>
                    <th>Certificate #</th>
                    <th>Issued</th>
                    <th>Expires</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recs.map(r => (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 600 }}>
                        {(r.training_type || '').replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                        {r.title && r.title !== r.training_type && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>{r.title}</div>
                        )}
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>{r.provider || '—'}</td>
                      <td style={{ fontSize: '0.85rem' }}>{r.certificate_number || '—'}</td>
                      <td style={{ fontSize: '0.85rem' }}>{r.issue_date}</td>
                      <td style={{ fontSize: '0.85rem', fontWeight: r.status === 'expired' ? 700 : 400 }}>
                        {r.expiry_date || 'N/A'}
                      </td>
                      <td>
                        <span className={`badge ${statusBadge(r.status)}`}>
                          {(r.status || '').replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
