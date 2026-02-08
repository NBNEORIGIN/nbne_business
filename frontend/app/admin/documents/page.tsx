'use client'

import { DEMO_DOCUMENTS } from '@/lib/demo-data'

export default function AdminDocumentsPage() {
  return (
    <div>
      <div className="page-header"><h1>Document Vault</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="doc-grid">
        {DEMO_DOCUMENTS.map(doc => (
          <div key={doc.id} className="card doc-card">
            <h3>{doc.title}</h3>
            <div className="doc-meta">
              <span className="badge badge-neutral">{doc.category}</span>
              <span className={`badge ${doc.tier_access === 'manager' ? 'badge-danger' : 'badge-info'}`}>Access: {doc.tier_access}+</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{doc.file_size}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
              Uploaded by {doc.uploaded_by} — {new Date(doc.uploaded_at).toLocaleDateString()}
            </div>
            {doc.expiry_date && (
              <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Expires: <span className={new Date(doc.expiry_date) < new Date() ? 'badge badge-danger' : 'badge badge-success'}>{doc.expiry_date}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
