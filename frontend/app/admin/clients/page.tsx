'use client'

import { useEffect, useState } from 'react'
import { getLeads } from '@/lib/api'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function AdminClientsPage() {
  const [allLeads, setAllLeads] = useState<any[]>([])
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLeads().then(r => { setAllLeads(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading leads…</div>

  const filtered = allLeads
    .filter(l => filter === 'ALL' || l.status === filter)
    .filter(l => !search || (l.name || '').toLowerCase().includes(search.toLowerCase()))

  const stats = {
    total: allLeads.length,
    new: allLeads.filter(l => l.status === 'NEW').length,
    converted: allLeads.filter(l => l.status === 'CONVERTED').length,
    pipeline: formatPrice(allLeads.filter(l => !['CONVERTED', 'LOST'].includes(l.status)).reduce((s: number, l: any) => s + (l.value_pence || 0), 0)),
  }

  return (
    <div>
      <div className="page-header"><h1>CRM — Leads</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="stats-grid">
        <div className="stat-card"><div className="stat-number">{stats.total}</div><div className="stat-label">Total Leads</div></div>
        <div className="stat-card"><div className="stat-number">{stats.new}</div><div className="stat-label">New</div></div>
        <div className="stat-card"><div className="stat-number">{stats.converted}</div><div className="stat-label">Converted</div></div>
        <div className="stat-card"><div className="stat-number">{stats.pipeline}</div><div className="stat-label">Pipeline Value</div></div>
      </div>
      <div className="filter-bar">
        <input placeholder="Search leads..." value={search} onChange={e => setSearch(e.target.value)} />
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="NEW">New</option>
          <option value="CONTACTED">Contacted</option>
          <option value="QUALIFIED">Qualified</option>
          <option value="CONVERTED">Converted</option>
          <option value="LOST">Lost</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Source</th><th>Value</th><th>Notes</th><th>Created</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.map(l => (
              <tr key={l.id}>
                <td><div style={{ fontWeight: 600 }}>{l.name}</div><div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{l.email}</div></td>
                <td>{l.source}</td>
                <td style={{ fontWeight: 600 }}>{formatPrice(l.value_pence)}</td>
                <td style={{ maxWidth: 200, fontSize: '0.85rem' }}>{l.notes}</td>
                <td style={{ fontSize: '0.85rem' }}>{new Date(l.created_at).toLocaleDateString()}</td>
                <td><span className={`badge ${l.status === 'CONVERTED' ? 'badge-success' : l.status === 'LOST' ? 'badge-danger' : l.status === 'NEW' ? 'badge-info' : 'badge-warning'}`}>{l.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
