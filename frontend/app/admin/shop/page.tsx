'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  getProducts, createProduct, updateProduct, deleteProduct,
  uploadProductImages, deleteProductImage, reorderProductImages,
  getOrders, updateOrder, getMediaUrl,
} from '@/lib/api'

/* ── Types ── */
type ProductImage = { id: number; url: string; alt_text: string; sort_order: number }
type Product = {
  id: number; name: string; subtitle: string; description: string; category: string;
  price: string; compare_at_price: string | null; image_url: string;
  primary_image_url: string; images: ProductImage[];
  stock_quantity: number; track_stock: boolean; in_stock: boolean;
  sort_order: number; active: boolean;
}
type Order = {
  id: number; customer_name: string; customer_email: string; customer_phone: string;
  status: string; total_pence: number;
  items: { id: number; product_name: string; quantity: number; unit_price_pence: number }[];
  created_at: string;
}

/* ── Constants ── */
const STATUS_COLOURS: Record<string, string> = {
  pending: '#f59e0b', paid: '#10b981', processing: '#3b82f6',
  shipped: '#6366f1', completed: '#059669', cancelled: '#ef4444', refunded: '#6b7280',
}
const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending', paid: 'Paid', processing: 'Processing',
  shipped: 'Shipped', completed: 'Completed', cancelled: 'Cancelled', refunded: 'Refunded',
}
const EMPTY: Partial<Product> = {
  name: '', subtitle: '', description: '', category: '', price: '0.00',
  compare_at_price: null, image_url: '', stock_quantity: 0,
  track_stock: false, sort_order: 0, active: true, images: [],
}

/* ── Shared styles ── */
const inputStyle: React.CSSProperties = {
  padding: '0.55rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8,
  fontSize: '0.875rem', width: '100%', outline: 'none', transition: 'border 0.15s',
  background: '#fff',
}
const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569',
  marginBottom: '0.25rem', textTransform: 'uppercase' as const, letterSpacing: '0.03em',
}
const thStyle: React.CSSProperties = {
  padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600,
  fontSize: '0.7rem', textTransform: 'uppercase' as const, letterSpacing: '0.04em',
}

/* ── Main component ── */
export default function ShopPage() {
  const [tab, setTab] = useState<'products' | 'orders'>('products')
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<Partial<Product> | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [pRes, oRes] = await Promise.all([getProducts({ all: true }), getOrders()])
      if (pRes.data && Array.isArray(pRes.data)) setProducts(pRes.data)
      if (oRes.data && Array.isArray(oRes.data)) setOrders(oRes.data)
    } catch { /* noop */ }
    setLoading(false)
  }

  /* ── Product save (create or update) ── */
  async function handleSave() {
    if (!editing?.name?.trim()) { setError('Product name is required'); return }
    if (!editing.price || Number(editing.price) < 0) { setError('Price must be 0 or more'); return }
    setError('')
    setSaving(true)
    try {
      const payload = {
        name: editing.name,
        subtitle: editing.subtitle || '',
        description: editing.description || '',
        category: editing.category || '',
        price: editing.price,
        compare_at_price: editing.compare_at_price || null,
        stock_quantity: editing.stock_quantity || 0,
        track_stock: editing.track_stock || false,
        sort_order: editing.sort_order || 0,
        active: editing.active !== false,
      }
      let productId = editing.id
      if (productId) {
        const res = await updateProduct(productId, payload)
        if (res.error) { setError(res.error); setSaving(false); return }
      } else {
        const res = await createProduct(payload)
        if (res.error) { setError(res.error); setSaving(false); return }
        productId = res.data?.id
      }
      // Upload pending images
      if (productId && pendingFiles.length > 0) {
        setUploading(true)
        const upRes = await uploadProductImages(productId, pendingFiles)
        if (upRes.error) setError(`Product saved but image upload failed: ${upRes.error}`)
        setUploading(false)
      }
      setPendingFiles([])
      setEditing(null)
      await loadData()
    } catch (e: any) {
      setError(e.message || 'Save failed')
    }
    setSaving(false)
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this product? This cannot be undone.')) return
    await deleteProduct(id)
    await loadData()
  }

  async function handleDeleteImage(productId: number, imageId: number) {
    await deleteProductImage(productId, imageId)
    await loadData()
    // Update editing state if open
    if (editing?.id === productId) {
      setEditing(prev => prev ? {
        ...prev,
        images: (prev.images || []).filter(i => i.id !== imageId)
      } : null)
    }
  }

  async function handleOrderStatus(id: number, status: string) {
    await updateOrder(id, { status })
    await loadData()
  }

  /* ── Drag & drop handlers ── */
  const onDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragOver(true) }, [])
  const onDragLeave = useCallback(() => setDragOver(false), [])
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
    if (files.length) setPendingFiles(prev => [...prev, ...files])
  }, [])
  const onFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(f => f.type.startsWith('image/'))
    if (files.length) setPendingFiles(prev => [...prev, ...files])
    if (fileRef.current) fileRef.current.value = ''
  }, [])

  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)))

  function openEdit(p?: Product) {
    setError('')
    setPendingFiles([])
    setEditing(p ? { ...p } : { ...EMPTY })
  }

  return (
    <div style={{ maxWidth: 1200 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, color: '#0f172a' }}>Shop</h1>
          <p style={{ color: '#64748b', margin: '0.15rem 0 0', fontSize: '0.85rem' }}>Manage products, images, stock and orders.</p>
        </div>
        {tab === 'products' && (
          <button onClick={() => openEdit()} style={{
            padding: '0.6rem 1.25rem', borderRadius: 8, border: 'none',
            background: '#2563eb', color: '#fff', fontWeight: 700, cursor: 'pointer',
            fontSize: '0.85rem', boxShadow: '0 1px 3px rgba(37,99,235,0.3)',
          }}>+ Add Product</button>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1.25rem', borderBottom: '2px solid #f1f5f9' }}>
        {(['products', 'orders'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '0.6rem 1.25rem', border: 'none', fontWeight: 600,
            background: 'none', color: tab === t ? '#2563eb' : '#94a3b8',
            cursor: 'pointer', fontSize: '0.85rem', textTransform: 'capitalize',
            borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent',
            marginBottom: -2, transition: 'all 0.15s',
          }}>{t} ({t === 'products' ? products.length : orders.length})</button>
        ))}
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>Loading...</div>}

      {/* ═══════ PRODUCT FORM MODAL ═══════ */}
      {editing && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
          padding: '2rem 1rem', overflowY: 'auto',
        }} onClick={e => { if (e.target === e.currentTarget) { setEditing(null); setPendingFiles([]) } }}>
          <div style={{
            background: '#fff', borderRadius: 16, width: '100%', maxWidth: 620,
            boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
          }}>
            {/* Header */}
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>
                {editing.id ? 'Edit Product' : 'New Product'}
              </h2>
              <button onClick={() => { setEditing(null); setPendingFiles([]) }} style={{
                background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: '#94a3b8', padding: '0.25rem',
              }}>&times;</button>
            </div>

            <div style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {error && (
                <div style={{ background: '#fef2f2', color: '#dc2626', padding: '0.6rem 0.75rem', borderRadius: 8, fontSize: '0.82rem', fontWeight: 500 }}>{error}</div>
              )}

              {/* Name + Subtitle */}
              <div>
                <label style={labelStyle}>Product Name *</label>
                <input placeholder="e.g. First Aid Kit — 50 Person" value={editing.name || ''} onChange={e => setEditing({ ...editing, name: e.target.value })}
                  style={inputStyle} autoFocus />
              </div>
              <div>
                <label style={labelStyle}>Subtitle</label>
                <input placeholder="Short tagline, e.g. BS 8599-1:2019 Compliant" value={editing.subtitle || ''} onChange={e => setEditing({ ...editing, subtitle: e.target.value })}
                  style={inputStyle} />
              </div>

              {/* Description */}
              <div>
                <label style={labelStyle}>Description</label>
                <textarea placeholder="Full product description..." value={editing.description || ''} onChange={e => setEditing({ ...editing, description: e.target.value })}
                  rows={4} style={{ ...inputStyle, resize: 'vertical' as const }} />
              </div>

              {/* Category + Pricing */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={labelStyle}>Category</label>
                  <input placeholder="e.g. First Aid" value={editing.category || ''} onChange={e => setEditing({ ...editing, category: e.target.value })}
                    list="cat-list" style={inputStyle} />
                  <datalist id="cat-list">{categories.map(c => <option key={c} value={c} />)}</datalist>
                </div>
                <div>
                  <label style={labelStyle}>Price (£) *</label>
                  <input type="number" step="0.01" min="0" value={editing.price || ''} onChange={e => setEditing({ ...editing, price: e.target.value })}
                    style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Compare at (£)</label>
                  <input type="number" step="0.01" min="0" placeholder="Was..." value={editing.compare_at_price || ''} onChange={e => setEditing({ ...editing, compare_at_price: e.target.value || null })}
                    style={inputStyle} />
                </div>
              </div>

              {/* ── IMAGES ── */}
              <div>
                <label style={labelStyle}>Images</label>
                {/* Existing images */}
                {editing.images && editing.images.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                    {editing.images.map(img => (
                      <div key={img.id} style={{ position: 'relative', width: 80, height: 80 }}>
                        <img src={getMediaUrl(img.url)} alt={img.alt_text} style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 8, border: '1px solid #e2e8f0' }} />
                        <button onClick={() => editing.id && handleDeleteImage(editing.id, img.id)} style={{
                          position: 'absolute', top: -6, right: -6, width: 20, height: 20, borderRadius: '50%',
                          background: '#ef4444', color: '#fff', border: 'none', fontSize: '0.7rem', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1,
                        }}>&times;</button>
                      </div>
                    ))}
                  </div>
                )}
                {/* Pending file previews */}
                {pendingFiles.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                    {pendingFiles.map((f, i) => (
                      <div key={i} style={{ position: 'relative', width: 80, height: 80 }}>
                        <img src={URL.createObjectURL(f)} alt="" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 8, border: '2px dashed #93c5fd' }} />
                        <button onClick={() => setPendingFiles(prev => prev.filter((_, j) => j !== i))} style={{
                          position: 'absolute', top: -6, right: -6, width: 20, height: 20, borderRadius: '50%',
                          background: '#94a3b8', color: '#fff', border: 'none', fontSize: '0.7rem', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1,
                        }}>&times;</button>
                      </div>
                    ))}
                  </div>
                )}
                {/* Drop zone */}
                <div
                  onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
                  onClick={() => fileRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragOver ? '#2563eb' : '#d1d5db'}`,
                    borderRadius: 10, padding: '1.25rem', textAlign: 'center', cursor: 'pointer',
                    background: dragOver ? '#eff6ff' : '#fafafa', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
                    {dragOver ? '📥' : '📷'}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 500 }}>
                    Drag & drop images here, or <span style={{ color: '#2563eb', textDecoration: 'underline' }}>browse</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.2rem' }}>JPG, PNG, WebP — multiple files supported</div>
                </div>
                <input ref={fileRef} type="file" accept="image/*" multiple onChange={onFileSelect} style={{ display: 'none' }} />
              </div>

              {/* Stock */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={editing.track_stock || false} onChange={e => setEditing({ ...editing, track_stock: e.target.checked })}
                    style={{ width: 16, height: 16 }} />
                  <span style={{ fontWeight: 500 }}>Track stock levels</span>
                </label>
                {editing.track_stock && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <label style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>Qty:</label>
                    <input type="number" min="0" value={editing.stock_quantity || 0} onChange={e => setEditing({ ...editing, stock_quantity: parseInt(e.target.value) || 0 })}
                      style={{ ...inputStyle, width: 80 }} />
                  </div>
                )}
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', cursor: 'pointer', marginLeft: 'auto' }}>
                  <input type="checkbox" checked={editing.active !== false} onChange={e => setEditing({ ...editing, active: e.target.checked })}
                    style={{ width: 16, height: 16 }} />
                  <span style={{ fontWeight: 500 }}>Published</span>
                </label>
              </div>
            </div>

            {/* Footer */}
            <div style={{
              padding: '1rem 1.5rem', borderTop: '1px solid #f1f5f9', background: '#fafafa',
              display: 'flex', gap: '0.5rem', justifyContent: 'flex-end',
            }}>
              <button onClick={() => { setEditing(null); setPendingFiles([]) }} style={{
                padding: '0.55rem 1.25rem', border: '1px solid #d1d5db', borderRadius: 8,
                background: '#fff', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 500,
              }}>Cancel</button>
              <button onClick={handleSave} disabled={saving || uploading} style={{
                padding: '0.55rem 1.5rem', borderRadius: 8, border: 'none',
                background: (saving || uploading) ? '#93c5fd' : '#2563eb', color: '#fff',
                fontWeight: 700, cursor: (saving || uploading) ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem', boxShadow: '0 1px 3px rgba(37,99,235,0.3)',
              }}>{uploading ? 'Uploading images...' : saving ? 'Saving...' : 'Save Product'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ PRODUCTS TAB ═══════ */}
      {tab === 'products' && !loading && (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                <th style={thStyle}>Product</th>
                <th style={thStyle}>Category</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Price</th>
                <th style={{ ...thStyle, textAlign: 'center' }}>Stock</th>
                <th style={{ ...thStyle, textAlign: 'center' }}>Status</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map(p => {
                const thumb = getMediaUrl(p.primary_image_url || p.image_url || '')
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9', transition: 'background 0.1s' }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#f8fafc')}
                    onMouseLeave={e => (e.currentTarget.style.background = '')}>
                    <td style={{ padding: '0.65rem 0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: 48, height: 48, borderRadius: 8, background: '#f1f5f9',
                          flexShrink: 0, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          {thumb ? <img src={thumb} alt="" style={{ width: 48, height: 48, objectFit: 'cover' }} /> :
                            <span style={{ fontSize: '1.2rem' }}>📦</span>}
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 600, color: '#0f172a' }}>{p.name}</div>
                          {p.subtitle && <div style={{ fontSize: '0.78rem', color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>{p.subtitle}</div>}
                          {p.images?.length > 0 && <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{p.images.length} image{p.images.length !== 1 ? 's' : ''}</div>}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '0.65rem 0.75rem' }}>
                      {p.category ? <span style={{ background: '#f1f5f9', padding: '0.15rem 0.5rem', borderRadius: 6, fontSize: '0.78rem', color: '#475569', fontWeight: 500 }}>{p.category}</span> : <span style={{ color: '#cbd5e1' }}>—</span>}
                    </td>
                    <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>
                      <span style={{ fontWeight: 700, color: '#0f172a' }}>£{Number(p.price).toFixed(2)}</span>
                      {p.compare_at_price && Number(p.compare_at_price) > Number(p.price) && (
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', textDecoration: 'line-through' }}>£{Number(p.compare_at_price).toFixed(2)}</div>
                      )}
                    </td>
                    <td style={{ padding: '0.65rem 0.75rem', textAlign: 'center' }}>
                      {p.track_stock ? (
                        <span style={{
                          fontWeight: 700, fontSize: '0.82rem',
                          color: p.stock_quantity <= 0 ? '#dc2626' : p.stock_quantity <= 5 ? '#f59e0b' : '#059669',
                        }}>
                          {p.stock_quantity}
                          {p.stock_quantity <= 0 && <div style={{ fontSize: '0.65rem', fontWeight: 500 }}>Out of stock</div>}
                          {p.stock_quantity > 0 && p.stock_quantity <= 5 && <div style={{ fontSize: '0.65rem', fontWeight: 500 }}>Low</div>}
                        </span>
                      ) : <span style={{ color: '#cbd5e1', fontSize: '1.1rem' }}>—</span>}
                    </td>
                    <td style={{ padding: '0.65rem 0.75rem', textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 20,
                        fontSize: '0.72rem', fontWeight: 700,
                        background: p.active ? '#dcfce7' : '#f1f5f9',
                        color: p.active ? '#166534' : '#94a3b8',
                      }}>{p.active ? 'Active' : 'Draft'}</span>
                    </td>
                    <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                        <button onClick={() => openEdit(p)} style={{
                          padding: '0.3rem 0.7rem', borderRadius: 6, border: '1px solid #e2e8f0',
                          background: '#fff', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, color: '#475569',
                        }}>Edit</button>
                        <button onClick={() => handleDelete(p.id)} style={{
                          padding: '0.3rem 0.7rem', borderRadius: 6, border: 'none',
                          background: '#fef2f2', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, color: '#dc2626',
                        }}>Delete</button>
                      </div>
                    </td>
                  </tr>
                )
              })}
              {products.length === 0 && (
                <tr><td colSpan={6} style={{ padding: '3rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📦</div>
                  <div style={{ fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>No products yet</div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Click "+ Add Product" to create your first product.</div>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ═══════ ORDERS TAB ═══════ */}
      {tab === 'orders' && !loading && (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                <th style={thStyle}>Order</th>
                <th style={thStyle}>Customer</th>
                <th style={thStyle}>Items</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Total</th>
                <th style={{ ...thStyle, textAlign: 'center' }}>Status</th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Update</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.65rem 0.75rem' }}>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>#{o.id}</div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{new Date(o.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</div>
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem' }}>
                    <div style={{ fontWeight: 600 }}>{o.customer_name || '—'}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{o.customer_email}</div>
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem', fontSize: '0.8rem', color: '#64748b', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>
                    {o.items?.map(i => `${i.quantity}× ${i.product_name}`).join(', ') || '—'}
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right', fontWeight: 700 }}>£{(o.total_pence / 100).toFixed(2)}</td>
                  <td style={{ padding: '0.65rem 0.75rem', textAlign: 'center' }}>
                    <span style={{
                      display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 20, fontSize: '0.72rem', fontWeight: 700,
                      background: `${STATUS_COLOURS[o.status] || '#94a3b8'}18`,
                      color: STATUS_COLOURS[o.status] || '#94a3b8',
                    }}>{STATUS_LABELS[o.status] || o.status}</span>
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem', textAlign: 'right' }}>
                    <select value={o.status} onChange={e => handleOrderStatus(o.id, e.target.value)}
                      style={{ padding: '0.3rem 0.5rem', borderRadius: 6, border: '1px solid #e2e8f0', fontSize: '0.78rem', cursor: 'pointer', background: '#fff' }}>
                      {Object.entries(STATUS_LABELS).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr><td colSpan={6} style={{ padding: '3rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🛒</div>
                  <div style={{ fontWeight: 600, color: '#475569' }}>No orders yet</div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Orders will appear here once customers start purchasing.</div>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
