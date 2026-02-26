'use client'

import { useState, useEffect } from 'react'
import { getPublicProducts, createShopCheckout, getMediaUrl } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

/* ── Design tokens ── */
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#1a1a1a'
const MUTED = '#6b7280'
const LIGHT_BG = '#f9fafb'

type ProductImage = { id: number; url: string; alt_text: string; sort_order: number }
type Product = {
  id: number; name: string; subtitle: string; description: string; category: string;
  price: string; compare_at_price: string | null; primary_image_url: string; images: ProductImage[];
  in_stock: boolean; track_stock: boolean; stock_quantity: number;
}
type CartItem = { product: Product; quantity: number }

export default function ShopPage() {
  const tenant = useTenant()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [cartOpen, setCartOpen] = useState(false)
  const [checkoutForm, setCheckoutForm] = useState({ name: '', email: '', phone: '' })
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [checkoutResult, setCheckoutResult] = useState<{ success: boolean; message: string } | null>(null)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [selectedImageIdx, setSelectedImageIdx] = useState(0)

  const accent = tenant?.colour_primary || '#2563eb'

  useEffect(() => {
    loadProducts()
  }, [])

  async function loadProducts() {
    setLoading(true)
    const res = await getPublicProducts()
    if (res.data && Array.isArray(res.data)) setProducts(res.data)
    setLoading(false)
  }

  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)))
  const filtered = category ? products.filter(p => p.category === category) : products
  const cartCount = cart.reduce((s, i) => s + i.quantity, 0)
  const cartTotal = cart.reduce((s, i) => s + Number(i.product.price) * 100 * i.quantity, 0)

  function addToCart(product: Product) {
    setCart(prev => {
      const existing = prev.find(i => i.product.id === product.id)
      if (existing) return prev.map(i => i.product.id === product.id ? { ...i, quantity: i.quantity + 1 } : i)
      return [...prev, { product, quantity: 1 }]
    })
    setCartOpen(true)
  }

  function updateQty(productId: number, delta: number) {
    setCart(prev => prev.map(i => {
      if (i.product.id !== productId) return i
      const newQty = Math.max(0, i.quantity + delta)
      return { ...i, quantity: newQty }
    }).filter(i => i.quantity > 0))
  }

  async function handleCheckout() {
    if (!checkoutForm.email.trim()) return
    setCheckoutLoading(true)
    setCheckoutResult(null)
    const res = await createShopCheckout({
      items: cart.map(i => ({ product_id: i.product.id, quantity: i.quantity })),
      customer_name: checkoutForm.name,
      customer_email: checkoutForm.email,
      customer_phone: checkoutForm.phone,
    })
    setCheckoutLoading(false)
    if (res.data?.checkout_url) {
      window.location.href = res.data.checkout_url
    } else if (res.data?.status === 'paid') {
      setCheckoutResult({ success: true, message: res.data.message || 'Order placed successfully!' })
      setCart([])
    } else {
      setCheckoutResult({ success: false, message: res.error || 'Checkout failed. Please try again.' })
    }
  }

  const inputStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 8,
    fontSize: '0.9rem', width: '100%', outline: 'none',
  }

  return (
    <div style={{ fontFamily: SANS, background: LIGHT_BG, minHeight: '100vh' }}>
      {/* ── Header ── */}
      <header style={{
        background: '#fff', borderBottom: '1px solid #e5e7eb', padding: '1rem 1.5rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: DARK, margin: 0 }}>
            {tenant?.business_name || 'Shop'}
          </h1>
          <p style={{ fontSize: '0.78rem', color: MUTED, margin: 0 }}>
            {tenant?.tagline || 'Browse our products'}
          </p>
        </div>
        <button onClick={() => setCartOpen(true)} style={{
          position: 'relative', background: accent, color: '#fff', border: 'none',
          padding: '0.55rem 1.25rem', borderRadius: 8, fontWeight: 700, cursor: 'pointer',
          fontSize: '0.85rem',
        }}>
          Cart {cartCount > 0 && <span style={{
            background: '#fff', color: accent, borderRadius: '50%', padding: '0.1rem 0.45rem',
            fontSize: '0.72rem', fontWeight: 800, marginLeft: '0.4rem',
          }}>{cartCount}</span>}
        </button>
      </header>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '1.5rem' }}>
        {/* ── Category filter ── */}
        {categories.length > 1 && (
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <button onClick={() => setCategory('')} style={{
              padding: '0.4rem 1rem', borderRadius: 20, border: !category ? 'none' : '1px solid #d1d5db',
              background: !category ? accent : '#fff', color: !category ? '#fff' : MUTED,
              fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
            }}>All</button>
            {categories.map(c => (
              <button key={c} onClick={() => setCategory(c)} style={{
                padding: '0.4rem 1rem', borderRadius: 20, border: category === c ? 'none' : '1px solid #d1d5db',
                background: category === c ? accent : '#fff', color: category === c ? '#fff' : MUTED,
                fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
              }}>{c}</button>
            ))}
          </div>
        )}

        {loading && <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>Loading products...</div>}

        {/* ── Product grid ── */}
        {!loading && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: '1.25rem',
          }}>
            {filtered.map(p => {
              const img = getMediaUrl(p.primary_image_url || '')
              const hasDiscount = p.compare_at_price && Number(p.compare_at_price) > Number(p.price)
              const outOfStock = p.track_stock && !p.in_stock
              return (
                <div key={p.id} style={{
                  background: '#fff', borderRadius: 12, overflow: 'hidden',
                  border: '1px solid #e5e7eb', transition: 'box-shadow 0.2s, transform 0.2s',
                  cursor: 'pointer', display: 'flex', flexDirection: 'column',
                }} onClick={() => { setSelectedProduct(p); setSelectedImageIdx(0) }}
                  onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 8px 30px rgba(0,0,0,0.08)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.transform = '' }}>
                  {/* Image */}
                  <div style={{
                    height: 220, background: '#f3f4f6', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', overflow: 'hidden', position: 'relative',
                  }}>
                    {img ? <img src={img} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> :
                      <span style={{ fontSize: '3rem' }}>📦</span>}
                    {hasDiscount && (
                      <span style={{
                        position: 'absolute', top: 10, left: 10, background: '#dc2626', color: '#fff',
                        padding: '0.2rem 0.5rem', borderRadius: 6, fontSize: '0.7rem', fontWeight: 700,
                      }}>SALE</span>
                    )}
                    {outOfStock && (
                      <div style={{
                        position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>Out of Stock</span>
                      </div>
                    )}
                  </div>
                  {/* Info */}
                  <div style={{ padding: '1rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
                    {p.category && <div style={{ fontSize: '0.7rem', color: MUTED, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem' }}>{p.category}</div>}
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, color: DARK, margin: '0 0 0.15rem' }}>{p.name}</h3>
                    {p.subtitle && <p style={{ fontSize: '0.82rem', color: MUTED, margin: '0 0 0.5rem' }}>{p.subtitle}</p>}
                    <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.5rem' }}>
                      <div>
                        <span style={{ fontWeight: 800, fontSize: '1.1rem', color: DARK }}>£{Number(p.price).toFixed(2)}</span>
                        {hasDiscount && <span style={{ fontSize: '0.8rem', color: '#94a3b8', textDecoration: 'line-through', marginLeft: '0.4rem' }}>£{Number(p.compare_at_price).toFixed(2)}</span>}
                      </div>
                      {!outOfStock && (
                        <button onClick={e => { e.stopPropagation(); addToCart(p) }} style={{
                          background: accent, color: '#fff', border: 'none', padding: '0.45rem 0.9rem',
                          borderRadius: 8, fontWeight: 700, cursor: 'pointer', fontSize: '0.78rem',
                        }}>Add to Cart</button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '4rem' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🏪</div>
            <div style={{ fontWeight: 600, color: '#475569' }}>No products available</div>
          </div>
        )}
      </div>

      {/* ── Product Detail Modal ── */}
      {selectedProduct && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
        }} onClick={() => setSelectedProduct(null)}>
          <div style={{
            background: '#fff', borderRadius: 16, maxWidth: 700, width: '100%',
            maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'grid', gridTemplateColumns: selectedProduct.images?.length > 0 ? '1fr 1fr' : '1fr', gap: 0 }}>
              {/* Image gallery */}
              <div style={{ background: '#f3f4f6', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ borderRadius: 10, overflow: 'hidden', aspectRatio: '1/1' }}>
                  {(() => {
                    const imgs = selectedProduct.images || []
                    const activeImg = getMediaUrl(imgs[selectedImageIdx]?.url || selectedProduct.primary_image_url || '')
                    return activeImg ? <img src={activeImg} alt={selectedProduct.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> :
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '4rem' }}>📦</div>
                  })()}
                </div>
                {selectedProduct.images && selectedProduct.images.length > 1 && (
                  <div style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto' }}>
                    {selectedProduct.images.map((img, i) => (
                      <img key={img.id} src={getMediaUrl(img.url)} alt="" onClick={() => setSelectedImageIdx(i)}
                        style={{
                          width: 56, height: 56, objectFit: 'cover', borderRadius: 6, cursor: 'pointer',
                          border: i === selectedImageIdx ? `2px solid ${accent}` : '2px solid transparent',
                          opacity: i === selectedImageIdx ? 1 : 0.6,
                        }} />
                    ))}
                  </div>
                )}
              </div>
              {/* Details */}
              <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                <button onClick={() => setSelectedProduct(null)} style={{
                  alignSelf: 'flex-end', background: 'none', border: 'none',
                  fontSize: '1.5rem', cursor: 'pointer', color: '#94a3b8',
                }}>&times;</button>
                {selectedProduct.category && <div style={{ fontSize: '0.72rem', color: MUTED, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{selectedProduct.category}</div>}
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: DARK, margin: '0.25rem 0 0.15rem' }}>{selectedProduct.name}</h2>
                {selectedProduct.subtitle && <p style={{ fontSize: '0.9rem', color: MUTED, margin: '0 0 0.75rem' }}>{selectedProduct.subtitle}</p>}
                <div style={{ marginBottom: '1rem' }}>
                  <span style={{ fontWeight: 800, fontSize: '1.4rem', color: DARK }}>£{Number(selectedProduct.price).toFixed(2)}</span>
                  {selectedProduct.compare_at_price && Number(selectedProduct.compare_at_price) > Number(selectedProduct.price) && (
                    <span style={{ fontSize: '0.9rem', color: '#94a3b8', textDecoration: 'line-through', marginLeft: '0.5rem' }}>£{Number(selectedProduct.compare_at_price).toFixed(2)}</span>
                  )}
                </div>
                {selectedProduct.description && (
                  <p style={{ fontSize: '0.88rem', color: '#4b5563', lineHeight: 1.6, margin: '0 0 1rem' }}>{selectedProduct.description}</p>
                )}
                {selectedProduct.track_stock && (
                  <div style={{
                    fontSize: '0.82rem', fontWeight: 600, marginBottom: '1rem',
                    color: selectedProduct.in_stock ? '#059669' : '#dc2626',
                  }}>
                    {selectedProduct.in_stock ? `In stock (${selectedProduct.stock_quantity} available)` : 'Out of stock'}
                  </div>
                )}
                <div style={{ marginTop: 'auto' }}>
                  {(!selectedProduct.track_stock || selectedProduct.in_stock) ? (
                    <button onClick={() => { addToCart(selectedProduct); setSelectedProduct(null) }} style={{
                      width: '100%', background: accent, color: '#fff', border: 'none',
                      padding: '0.75rem', borderRadius: 10, fontWeight: 700, cursor: 'pointer', fontSize: '0.95rem',
                    }}>Add to Cart</button>
                  ) : (
                    <button disabled style={{
                      width: '100%', background: '#e5e7eb', color: '#9ca3af', border: 'none',
                      padding: '0.75rem', borderRadius: 10, fontWeight: 700, cursor: 'not-allowed', fontSize: '0.95rem',
                    }}>Out of Stock</button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Cart Drawer ── */}
      {cartOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 300, display: 'flex',
        }}>
          <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)' }} onClick={() => setCartOpen(false)} />
          <div style={{
            width: 420, maxWidth: '100vw', background: '#fff', height: '100vh',
            display: 'flex', flexDirection: 'column', boxShadow: '-8px 0 30px rgba(0,0,0,0.1)',
          }}>
            {/* Cart header */}
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Your Cart ({cartCount})</h2>
              <button onClick={() => setCartOpen(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#94a3b8' }}>&times;</button>
            </div>

            {/* Cart items */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 1.5rem' }}>
              {cart.length === 0 && (
                <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🛒</div>
                  <div style={{ fontWeight: 500 }}>Your cart is empty</div>
                </div>
              )}
              {cart.map(item => (
                <div key={item.product.id} style={{
                  display: 'flex', gap: '0.75rem', padding: '0.75rem 0',
                  borderBottom: '1px solid #f3f4f6',
                }}>
                  <div style={{ width: 56, height: 56, borderRadius: 8, background: '#f3f4f6', flexShrink: 0, overflow: 'hidden' }}>
                    {getMediaUrl(item.product.primary_image_url) ?
                      <img src={getMediaUrl(item.product.primary_image_url)} alt="" style={{ width: 56, height: 56, objectFit: 'cover' }} /> :
                      <div style={{ width: 56, height: 56, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>📦</div>}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.88rem', color: DARK }}>{item.product.name}</div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: DARK }}>£{Number(item.product.price).toFixed(2)}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.3rem' }}>
                      <button onClick={() => updateQty(item.product.id, -1)} style={{
                        width: 26, height: 26, borderRadius: 6, border: '1px solid #d1d5db', background: '#fff',
                        cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>−</button>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, minWidth: 20, textAlign: 'center' }}>{item.quantity}</span>
                      <button onClick={() => updateQty(item.product.id, 1)} style={{
                        width: 26, height: 26, borderRadius: 6, border: '1px solid #d1d5db', background: '#fff',
                        cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>+</button>
                    </div>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: DARK, alignSelf: 'center' }}>
                    £{(Number(item.product.price) * item.quantity).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>

            {/* Checkout section */}
            {cart.length > 0 && (
              <div style={{ borderTop: '1px solid #e5e7eb', padding: '1.25rem 1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span style={{ fontWeight: 600, color: MUTED }}>Total</span>
                  <span style={{ fontWeight: 800, fontSize: '1.15rem', color: DARK }}>£{(cartTotal / 100).toFixed(2)}</span>
                </div>

                {checkoutResult && (
                  <div style={{
                    padding: '0.6rem 0.75rem', borderRadius: 8, marginBottom: '0.75rem', fontSize: '0.82rem', fontWeight: 500,
                    background: checkoutResult.success ? '#dcfce7' : '#fef2f2',
                    color: checkoutResult.success ? '#166534' : '#dc2626',
                  }}>{checkoutResult.message}</div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <input placeholder="Your name" value={checkoutForm.name} onChange={e => setCheckoutForm({ ...checkoutForm, name: e.target.value })} style={inputStyle} />
                  <input placeholder="Email address *" type="email" value={checkoutForm.email} onChange={e => setCheckoutForm({ ...checkoutForm, email: e.target.value })} style={inputStyle} />
                  <input placeholder="Phone (optional)" value={checkoutForm.phone} onChange={e => setCheckoutForm({ ...checkoutForm, phone: e.target.value })} style={inputStyle} />
                </div>

                <button onClick={handleCheckout} disabled={checkoutLoading || !checkoutForm.email.trim()} style={{
                  width: '100%', background: checkoutLoading ? '#93c5fd' : accent, color: '#fff',
                  border: 'none', padding: '0.75rem', borderRadius: 10, fontWeight: 700,
                  cursor: checkoutLoading ? 'not-allowed' : 'pointer', fontSize: '0.95rem',
                }}>{checkoutLoading ? 'Processing...' : `Pay £${(cartTotal / 100).toFixed(2)}`}</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
