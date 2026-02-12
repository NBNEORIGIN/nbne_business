'use client'

import { useState, useEffect, useCallback } from 'react'
import { getComplianceDocuments, getRams } from '@/lib/api'

type Filter = '' | 'current' | 'expired' | 'policy' | 'certificate' | 'insurance' | 'rams'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<any[]>([])
  const [rams, setRams] = useState<any[]>([])
  const [filter, setFilter] = useState<Filter>('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const [d, r] = await Promise.all([getComplianceDocuments(), getRams()])
    if (d.data) setDocs(d.data)
    if (r.data) setRams(r.data)
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  // Merge docs + RAMS into unified list
  const allDocs = [
    ...docs.map(d => ({ ...d, source: 'vault' as const })),
    ...rams.map(r => ({
      id: `rams-${r.id}`,
      title: r.title,
      document_type: 'rams',
      version: '—',
      is_current: r.status === 'ACTIVE',
      is_expired: r.status === 'EXPIRED',
      expiry_date: r.expiry_date,
      uploaded_by_name: r.created_by_name,
      description: r.description || '',
      reference_number: r.reference_number,
      source: 'rams' as const,
    })),
  ]

  const filtered = allDocs.filter(d => {
    if (!filter) return true
    if (filter === 'current') return d.is_current && !d.is_expired
    if (filter === 'expired') return d.is_expired
    if (filter === 'rams') return d.source === 'rams'
    return d.document_type === filter
  })

  const counts = {
    all: allDocs.length,
    current: allDocs.filter(d => d.is_current && !d.is_expired).length,
    expired: allDocs.filter(d => d.is_expired).length,
    policy: allDocs.filter(d => d.document_type === 'policy').length,
    certificate: allDocs.filter(d => d.document_type === 'certificate').length,
    insurance: allDocs.filter(d => d.document_type === 'insurance').length,
    rams: rams.length,
  }

  const FILTERS: { key: Filter; label: string; count: number; activeClass?: string }[] = [
    { key: '', label: 'All', count: counts.all },
    { key: 'current', label: 'Current', count: counts.current, activeClass: 'active-success' },
    { key: 'expired', label: 'Expired', count: counts.expired, activeClass: 'active-danger' },
    { key: 'policy', label: 'Policies', count: counts.policy },
    { key: 'certificate', label: 'Certificates', count: counts.certificate },
    { key: 'insurance', label: 'Insurance', count: counts.insurance },
    { key: 'rams', label: 'RAMS', count: counts.rams },
  ]

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>

  return (
    <div>
      <h2 style={{ marginBottom: '0.25rem' }}>Documents</h2>
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
        Policies, certificates, insurance documents and RAMS — all in one place.
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

      {filtered.length === 0 ? (
        <div className="empty-state">No documents match this filter</div>
      ) : (
        <div className="doc-grid">
          {filtered.map(doc => (
            <div key={doc.id} className="card doc-card">
              <h3>{doc.title}</h3>
              <div className="doc-meta">
                <span className={`badge ${doc.is_expired ? 'badge-danger' : 'badge-success'}`}>
                  {doc.is_expired ? 'Expired' : 'Current'}
                </span>
                {doc.version && doc.version !== '—' && <span className="badge badge-info">v{doc.version}</span>}
                <span className="badge badge-neutral">
                  {(doc.document_type || '').replace(/_/g, ' ')}
                </span>
              </div>
              {doc.expiry_date && (
                <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: doc.is_expired ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>
                  {doc.is_expired ? 'Expired' : 'Expires'}: {doc.expiry_date}
                </div>
              )}
              {doc.uploaded_by_name && (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  {doc.uploaded_by_name}
                </div>
              )}
              {doc.reference_number && (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  Ref: {doc.reference_number}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
