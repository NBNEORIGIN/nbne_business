'use client'

import { useEffect, useState } from 'react'
import { getDocuments } from '@/lib/api'

export default function StaffDocumentsPage() {
  const [docs, setDocs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDocuments().then(r => { setDocs(r.data || []); setLoading(false) })
  }, [])

  if (loading) return <div className="empty-state">Loading documents…</div>

  return (
    <div>
      <div className="page-header"><h1>Documents</h1><span className="badge badge-success">Tier 2</span></div>
      <div className="doc-grid">
        {docs.map((doc: any) => (
          <div key={doc.id} className="card doc-card">
            <h3>{doc.title}</h3>
            <div className="doc-meta">
              <span className="badge badge-neutral">{doc.category}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{doc.file_size}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
              Uploaded by {doc.uploaded_by_name} — {new Date(doc.created_at).toLocaleDateString()}
            </div>
            {doc.expiry_date && (
              <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Expires: <span className={doc.is_expired ? 'badge badge-danger' : 'badge badge-success'}>{doc.expiry_date}</span>
              </div>
            )}
          </div>
        ))}
        {docs.length === 0 && <div className="empty-state">No documents available</div>}
      </div>
    </div>
  )
}
