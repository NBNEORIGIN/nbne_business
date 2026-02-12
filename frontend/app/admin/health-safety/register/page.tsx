'use client'

import { useState, useEffect, useCallback } from 'react'
import { getComplianceItems, completeComplianceItem } from '@/lib/api'

function statusBadge(s: string) {
  const map: Record<string, string> = {
    compliant: 'badge-success', due_soon: 'badge-warning',
    overdue: 'badge-danger', not_started: 'badge-info',
  }
  return map[s] || 'badge-info'
}

type Filter = '' | 'overdue' | 'due_soon' | 'compliant' | 'not_started' | 'legal'

export default function ComplianceRegisterPage() {
  const [items, setItems] = useState<any[]>([])
  const [filter, setFilter] = useState<Filter>('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getComplianceItems()
    if (res.data) setItems(res.data)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function handleComplete(id: number) {
    await completeComplianceItem(id)
    load()
  }

  const filtered = items.filter(item => {
    if (!filter) return true
    if (filter === 'legal') return item.legal_requirement
    return item.status === filter
  })

  const counts = {
    all: items.length,
    overdue: items.filter(i => i.status === 'overdue').length,
    due_soon: items.filter(i => i.status === 'due_soon').length,
    compliant: items.filter(i => i.status === 'compliant').length,
    not_started: items.filter(i => i.status === 'not_started').length,
    legal: items.filter(i => i.legal_requirement).length,
  }

  const FILTERS: { key: Filter; label: string; count: number; activeClass?: string }[] = [
    { key: '', label: 'All', count: counts.all },
    { key: 'overdue', label: 'Overdue', count: counts.overdue, activeClass: 'active-danger' },
    { key: 'due_soon', label: 'Due Soon', count: counts.due_soon, activeClass: 'active-warning' },
    { key: 'compliant', label: 'Compliant', count: counts.compliant, activeClass: 'active-success' },
    { key: 'not_started', label: 'Not Started', count: counts.not_started },
    { key: 'legal', label: 'Legal Only', count: counts.legal },
  ]

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h2 style={{ margin: 0 }}>Compliance Register</h2>
        <a href="/api/compliance/export/" target="_blank" className="btn btn-sm btn-outline">
          Export CSV
        </a>
      </div>
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
        All recurring compliance items — PAT, fire, wiring, gas, insurance, training and more.
      </p>

      {/* Tag Filters */}
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

      {filtered.length === 0 ? (
        <div className="empty-state">No items match this filter</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Category</th>
                <th>Frequency</th>
                <th>Last Done</th>
                <th>Next Due</th>
                <th>Assigned To</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(item => (
                <tr key={item.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{item.title}</div>
                    {item.legal_requirement && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)' }}>Legal requirement</span>
                    )}
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{item.category_name}</td>
                  <td style={{ fontSize: '0.85rem' }}>{(item.frequency_type || '').replace(/_/g, ' ')}</td>
                  <td style={{ fontSize: '0.85rem' }}>{item.last_completed_date || '—'}</td>
                  <td style={{ fontSize: '0.85rem', fontWeight: item.status === 'overdue' ? 700 : 400 }}>
                    {item.next_due_date || '—'}
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{item.responsible_user_name || '—'}</td>
                  <td>
                    <span className={`badge ${statusBadge(item.status)}`}>
                      {(item.status || '').replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td>
                    {item.status !== 'compliant' && (
                      <button className="btn btn-sm btn-primary" onClick={() => handleComplete(item.id)}>
                        Done
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
