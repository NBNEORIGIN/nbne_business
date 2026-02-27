/* SORTED UX — Document Vault
 * Goal: "All your important documents in one place. Upload, categorise, track expiry."
 */
'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { getDocuments, getDocumentSummary, getDocumentCategories, createDocument, updateDocument, deleteDocument, downloadDocument } from '@/lib/api'

const STATUS_BADGE: Record<string, string> = {
  VALID: 'badge-success', EXPIRING: 'badge-warning', EXPIRED: 'badge-danger', MISSING: 'badge-neutral',
}
const STATUS_LABEL: Record<string, string> = {
  VALID: 'Valid', EXPIRING: 'Expiring Soon', EXPIRED: 'Expired', MISSING: 'Not Uploaded',
}
const ACCESS_BADGE: Record<string, string> = {
  owner: 'badge-danger', manager: 'badge-warning', staff: 'badge-info',
}

export default function AdminDocumentsPage() {
  const [docs, setDocs] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [categories, setCategories] = useState<string[]>([])
  const [activeCategory, setActiveCategory] = useState('')
  const [search, setSearch] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [editDoc, setEditDoc] = useState<any>(null)
  const [toast, setToast] = useState('')
  const [viewMode, setViewMode] = useState<'folders' | 'grid'>('folders')
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set())
  const fileRef = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    setLoading(true)
    const params: any = {}
    if (activeCategory) params.category = activeCategory
    if (search) params.search = search
    const [docsRes, sumRes, catRes] = await Promise.all([getDocuments(params), getDocumentSummary(), getDocumentCategories()])
    setDocs(docsRes.data || [])
    setSummary(sumRes.data || null)
    if (catRes.data) setCategories(catRes.data)
    setLoading(false)
  }, [activeCategory, search])

  useEffect(() => { load() }, [load])

  function showToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setUploading(true)
    const form = e.currentTarget
    const fd = new FormData(form)
    let res
    if (editDoc) {
      res = await updateDocument(editDoc.id, fd)
    } else {
      res = await createDocument(fd)
    }
    if (res.error) {
      showToast(`Error: ${res.error}`)
    } else {
      showToast(editDoc ? 'Document updated' : 'Document uploaded')
      setShowUpload(false)
      setEditDoc(null)
      load()
    }
    setUploading(false)
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this document permanently?')) return
    await deleteDocument(id)
    showToast('Document deleted')
    load()
  }

  function openEdit(doc: any) {
    setEditDoc(doc)
    setShowUpload(true)
  }

  function toggleFolder(key: string) {
    setCollapsedFolders(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  function getGroupedDocs() {
    const groups: Record<string, any[]> = {}
    for (const cat of categories) {
      groups[cat] = []
    }
    for (const doc of docs) {
      const key = doc.category || 'General'
      if (!groups[key]) groups[key] = []
      groups[key].push(doc)
    }
    return groups
  }

  function fmtDate(d: string | null) {
    if (!d) return '—'
    return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  if (loading && docs.length === 0) return <div className="empty-state">Loading documents…</div>

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', top: 20, right: 20, background: 'var(--color-primary)', color: '#fff', padding: '0.6rem 1.2rem', borderRadius: 10, fontSize: '0.85rem', fontWeight: 600, zIndex: 9999, boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}>{toast}</div>
      )}

      {/* Header */}
      <div className="page-header">
        <h1>Document Vault</h1>
      </div>
      <p className="staff-header-sub">UK legal requirements, policies, certificates &amp; compliance documents</p>

      {/* Summary Stats */}
      {summary && (
        <div className="status-strip">
          <div className="status-strip-item"><span className="status-strip-num">{summary.total}</span><span className="status-strip-label">Total</span></div>
          <div className="status-strip-item"><span className="status-strip-num" style={{ color: 'var(--color-success)' }}>{summary.valid}</span><span className="status-strip-label">Valid</span></div>
          <div className="status-strip-item"><span className="status-strip-num" style={{ color: summary.expiring_soon > 0 ? 'var(--color-warning)' : undefined }}>{summary.expiring_soon}</span><span className="status-strip-label">Expiring</span></div>
          <div className="status-strip-item"><span className="status-strip-num" style={{ color: summary.expired > 0 ? 'var(--color-danger)' : undefined }}>{summary.expired}</span><span className="status-strip-label">Expired</span></div>
          <div className="status-strip-item"><span className="status-strip-num" style={{ color: summary.missing > 0 ? 'var(--color-text-muted)' : undefined }}>{summary.missing}</span><span className="status-strip-label">Missing</span></div>
        </div>
      )}

      {/* Category Tabs + Search + View Toggle + Upload */}
      <div className="tab-subheader">
        <div className="tab-subheader-left" style={{ gap: 8, flexWrap: 'wrap' }}>
          <div className="filter-pills">
            <button className={`filter-pill ${activeCategory === '' ? 'active' : ''}`} onClick={() => setActiveCategory('')}>All</button>
            {categories.map(cat => (
              <button key={cat} className={`filter-pill ${activeCategory === cat ? 'active' : ''}`} onClick={() => setActiveCategory(cat)}>
                {cat}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <button className={`btn btn-sm ${viewMode === 'folders' ? 'btn-primary' : ''}`} onClick={() => setViewMode('folders')} title="Folder view">Folders</button>
            <button className={`btn btn-sm ${viewMode === 'grid' ? 'btn-primary' : ''}`} onClick={() => setViewMode('grid')} title="Grid view">Grid</button>
          </div>
          <input
            className="form-input"
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search documents…"
            style={{ maxWidth: 200, fontSize: '0.85rem' }}
          />
        </div>
        <div className="tab-subheader-right">
          <button className="btn btn-primary" onClick={() => { setEditDoc(null); setShowUpload(true) }}>+ Upload Document</button>
        </div>
      </div>

      {/* Document List */}
      {docs.length === 0 && !loading ? (
        <div className="empty-cta">
          <div className="empty-cta-title">No documents found</div>
          <div className="empty-cta-desc">
            {activeCategory || search ? 'Try a different filter or search term.' : 'Upload your first document to get started.'}
          </div>
        </div>
      ) : viewMode === 'folders' ? (
        /* ── Folder View ── */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(() => {
            const grouped = getGroupedDocs()
            // Build display list: all known categories + any extra from grouped docs
            const allCats = Array.from(new Set([...categories, ...Object.keys(grouped)]))
            return allCats.map(cat => {
              const catDocs = grouped[cat] || []
              if (activeCategory && activeCategory !== cat) return null
              if (catDocs.length === 0 && activeCategory) return null
              const isCollapsed = collapsedFolders.has(cat)
              return (
                <div key={cat} style={{ background: 'var(--color-bg-card, #fff)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                  {/* Folder header */}
                  <button onClick={() => toggleFolder(cat)} style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '0.65rem 1rem',
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text)', textAlign: 'left',
                  }}>
                    <span style={{ fontSize: '0.85rem', transition: 'transform 0.2s', transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>▼</span>
                    <span style={{ fontWeight: 700, fontSize: '0.88rem', flex: 1 }}>{cat}</span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>{catDocs.length} {catDocs.length === 1 ? 'doc' : 'docs'}</span>
                  </button>
                  {/* Folder contents */}
                  {!isCollapsed && (
                    <div style={{ borderTop: '1px solid var(--color-border)' }}>
                      {catDocs.length === 0 ? (
                        <div style={{ padding: '1rem', textAlign: 'center', fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>No documents in this category</div>
                      ) : (
                        <div className="table-wrap">
                          <table>
                            <thead><tr><th>Title</th><th>Status</th><th>Access</th><th>Expiry</th><th>Size</th><th>Uploaded</th><th></th></tr></thead>
                            <tbody>
                              {catDocs.map((doc: any) => {
                                const st = doc.status || 'VALID'
                                return (
                                  <tr key={doc.id} style={{ opacity: st === 'MISSING' ? 0.65 : 1 }}>
                                    <td>
                                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{doc.title}</div>
                                      {doc.description && <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.description}</div>}
                                      {doc.regulatory_ref && <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginTop: 1 }}>{doc.regulatory_ref}</div>}
                                    </td>
                                    <td><span className={`badge ${STATUS_BADGE[st] || 'badge-neutral'}`}>{STATUS_LABEL[st] || st}</span></td>
                                    <td><span className={`badge ${ACCESS_BADGE[doc.access_level] || 'badge-neutral'}`} style={{ fontSize: '0.7rem' }}>{doc.access_level}+</span></td>
                                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.82rem', color: doc.is_expired ? 'var(--color-danger)' : doc.is_expiring_soon ? 'var(--color-warning)' : 'var(--color-text-muted)' }}>
                                      {doc.expiry_date ? fmtDate(doc.expiry_date) : '—'}
                                    </td>
                                    <td style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{doc.file_size_display || '—'}</td>
                                    <td style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                                      {doc.uploaded_by_name && <span>{doc.uploaded_by_name}<br /></span>}
                                      {fmtDate(doc.created_at)}
                                    </td>
                                    <td style={{ whiteSpace: 'nowrap' }}>
                                      {doc.file_url && (
                                        <button className="btn btn-sm" style={{ marginRight: 4 }} onClick={() => downloadDocument(doc.id, doc.filename)}>Download</button>
                                      )}
                                      {doc.is_placeholder && !doc.file_url && (
                                        <button className="btn btn-sm btn-warning" onClick={() => openEdit(doc)} style={{ marginRight: 4 }}>Upload</button>
                                      )}
                                      <button className="btn btn-sm" onClick={() => openEdit(doc)} style={{ marginRight: 4 }}>Edit</button>
                                      <button className="btn btn-sm btn-danger" onClick={() => handleDelete(doc.id)}>Delete</button>
                                    </td>
                                  </tr>
                                )
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          })()}
        </div>
      ) : (
        /* ── Grid View ── */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
          {docs.map((doc: any) => {
            const st = doc.status || 'VALID'
            return (
              <div key={doc.id} style={{
                background: 'var(--color-bg-card, #fff)', borderRadius: 'var(--radius)', padding: '1rem',
                border: `1px solid ${st === 'EXPIRED' ? 'var(--color-danger)' : st === 'EXPIRING' ? 'var(--color-warning)' : 'var(--color-border)'}`,
                opacity: st === 'MISSING' ? 0.7 : 1,
              }}>
                {/* Title row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                  <h3 style={{ fontSize: '0.88rem', fontWeight: 700, margin: 0, lineHeight: 1.3, flex: 1, minWidth: 0, wordBreak: 'break-word' }}>{doc.title}</h3>
                  <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                    <button className="btn btn-sm" onClick={() => openEdit(doc)} title="Edit">Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(doc.id)} title="Delete">Del</button>
                  </div>
                </div>

                {doc.description && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', margin: '4px 0 0', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' }}>{doc.description}</p>
                )}

                {/* Badges */}
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 8 }}>
                  <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>{doc.category?.replace('_', ' ')}</span>
                  <span className={`badge ${STATUS_BADGE[st] || 'badge-neutral'}`} style={{ fontSize: '0.68rem' }}>{STATUS_LABEL[st] || st}</span>
                  <span className={`badge ${ACCESS_BADGE[doc.access_level] || 'badge-neutral'}`} style={{ fontSize: '0.68rem' }}>{doc.access_level}+</span>
                  {doc.file_size_display && <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', alignSelf: 'center' }}>{doc.file_size_display}</span>}
                </div>

                {doc.regulatory_ref && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: 6, fontStyle: 'italic' }}>{doc.regulatory_ref}</div>
                )}

                {/* Footer */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  <span>{doc.uploaded_by_name ? `${doc.uploaded_by_name}` : ''} {doc.created_at ? `— ${fmtDate(doc.created_at)}` : ''}</span>
                  {doc.expiry_date && (
                    <span style={{ color: doc.is_expired ? 'var(--color-danger)' : doc.is_expiring_soon ? 'var(--color-warning)' : 'var(--color-success)', fontWeight: 600 }}>
                      Exp: {fmtDate(doc.expiry_date)}
                    </span>
                  )}
                </div>

                {/* File link or upload prompt */}
                <div style={{ marginTop: 8 }}>
                  {doc.file_url ? (
                    <button className="btn btn-sm btn-primary" style={{ fontSize: '0.78rem' }} onClick={() => downloadDocument(doc.id, doc.filename)}>
                      Download
                    </button>
                  ) : doc.is_placeholder ? (
                    <button className="btn btn-sm btn-warning" onClick={() => openEdit(doc)} style={{ fontSize: '0.78rem' }}>
                      Upload this document
                    </button>
                  ) : null}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Upload / Edit Modal */}
      {showUpload && (
        <div className="modal-overlay" onClick={() => { setShowUpload(false); setEditDoc(null) }}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <h2 style={{ marginBottom: 16 }}>{editDoc ? 'Edit Document' : 'Upload Document'}</h2>
            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label className="form-label">Title *</label>
                <input className="form-input" name="title" defaultValue={editDoc?.title || ''} required />
              </div>
              <div>
                <label className="form-label">Description</label>
                <textarea className="form-input" name="description" defaultValue={editDoc?.description || ''} rows={2} style={{ resize: 'vertical' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Category</label>
                  <input className="form-input" name="category" list="doc-cat-list" defaultValue={editDoc?.category || 'General'} placeholder="Select or type a category" />
                  <datalist id="doc-cat-list">
                    {categories.map(c => <option key={c} value={c} />)}
                  </datalist>
                </div>
                <div>
                  <label className="form-label">Access Level</label>
                  <select className="form-input" name="access_level" defaultValue={editDoc?.access_level || 'staff'}>
                    <option value="owner">Owner Only</option>
                    <option value="manager">Manager+</option>
                    <option value="staff">All Staff</option>
                  </select>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Expiry Date</label>
                  <input className="form-input" name="expiry_date" type="date" defaultValue={editDoc?.expiry_date || ''} />
                </div>
                <div>
                  <label className="form-label">Regulatory Ref</label>
                  <input className="form-input" name="regulatory_ref" defaultValue={editDoc?.regulatory_ref || ''} placeholder="e.g. HASAWA 1974" />
                </div>
              </div>
              <div>
                <label className="form-label">File {editDoc?.file_url ? '(replace existing)' : ''}</label>
                <input ref={fileRef} className="form-input" name="file" type="file" style={{ padding: '0.4rem' }} accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.xls,.xlsx,.csv,.txt" />
                {editDoc?.filename && <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: 4 }}>Current file: {editDoc.filename}</div>}
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" className="btn" onClick={() => { setShowUpload(false); setEditDoc(null) }}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={uploading}>
                  {uploading ? 'Saving…' : editDoc ? 'Save Changes' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
