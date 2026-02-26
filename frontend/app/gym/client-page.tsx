'use client'

import { useState, useEffect } from 'react'
import DemoBanner, { DEMO_BANNER_HEIGHT } from '@/components/DemoBanner'
import { getPublicProducts, getMediaUrl } from '@/lib/api'

/* ── Design tokens ── */
const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const ACCENT = '#dc2626'        // energetic red
const ACCENT_LIGHT = '#f87171'
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_LIGHT = '#FAFAFA'
const BG_WARM = '#F5F3F0'

/* ── Unsplash images ── */
const HERO_IMG = 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1920&q=80&auto=format'
const GALLERY = [
  'https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1593079831268-3381b0db4a77?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1576678927484-cc907957088c?w=600&q=80&auto=format',
]

const TEAM = [
  { name: 'Jake Morrison', role: 'Head PT & HIIT Coach', img: 'https://images.unsplash.com/photo-1567013127542-490d757e51fc?w=400&q=80&auto=format', bio: 'Level 4 PT with 10 years experience. Specialises in strength & conditioning and HIIT training.' },
  { name: 'Sarah Okonkwo', role: 'Yoga & Pilates Instructor', img: 'https://images.unsplash.com/photo-1594381898411-846e7d193883?w=400&q=80&auto=format', bio: '500hr certified yoga teacher. Combines mindfulness with movement for total body wellness.' },
  { name: 'Ryan Patel', role: 'Spin & CrossFit Coach', img: 'https://images.unsplash.com/photo-1583468982228-19f19164aee2?w=400&q=80&auto=format', bio: 'Former competitive cyclist turned coach. His spin classes are legendary — bring a towel.' },
  { name: 'Lisa Nguyen', role: 'Sports Therapist', img: 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&q=80&auto=format', bio: 'BSc Sports Therapy. Expert in injury rehab, sports massage, and physiotherapy.' },
]

const FALLBACK_SERVICES = [
  { category: 'Memberships', items: [{ name: 'Monthly Membership', price: '£49.99/mo' }, { name: '6-Month Membership', price: '£269.99' }, { name: 'Annual Membership', price: '£479.99' }, { name: 'Student Monthly', price: '£29.99/mo' }] },
  { category: 'Personal Training', items: [{ name: '1:1 Personal Training', price: '£50' }, { name: 'PT Block (5 Sessions)', price: '£225' }, { name: 'PT Block (10 Sessions)', price: '£400' }, { name: 'Couples PT Session', price: '£75' }] },
  { category: 'Classes', items: [{ name: 'HIIT Class', price: '£12' }, { name: 'Yoga Flow', price: '£12' }, { name: 'Spin Class', price: '£12' }, { name: 'Boxing Fitness', price: '£14' }, { name: 'Pilates', price: '£12' }, { name: 'CrossFit WOD', price: '£15' }] },
  { category: 'Wellness', items: [{ name: 'Sports Massage (60 min)', price: '£55' }, { name: 'Physiotherapy (45 min)', price: '£75' }, { name: 'Sauna & Steam Room', price: '£15' }, { name: 'Swimming Lane Booking', price: '£8' }] },
]

const REVIEWS = [
  { name: 'Chris E.', text: 'Best gym I\'ve ever been a member of. The trainers actually care about your progress. Jake\'s HIIT class is insane — in the best way.', stars: 5 },
  { name: 'Amy J.', text: 'Sarah\'s yoga classes are the highlight of my week. The online booking makes it so easy to grab a spot. Love the whole vibe here.', stars: 5 },
  { name: 'Ben T.', text: 'Signed up for the 10-session PT block and it\'s been transformative. The facilities are spotless and the staff are all brilliant.', stars: 5 },
]

const HOURS = [
  { day: 'Monday', time: '06:00 - 22:00' },
  { day: 'Tuesday', time: '06:00 - 22:00' },
  { day: 'Wednesday', time: '06:00 - 22:00' },
  { day: 'Thursday', time: '06:00 - 22:00' },
  { day: 'Friday', time: '06:00 - 21:00' },
  { day: 'Saturday', time: '07:00 - 20:00' },
  { day: 'Sunday', time: '08:00 - 18:00' },
]

const CLASS_TIMETABLE = [
  { day: 'Mon', classes: ['HIIT 07:00', 'Yoga 12:00', 'Spin 18:00'] },
  { day: 'Tue', classes: ['CrossFit 07:00', 'Pilates 12:00', 'Boxing 18:30'] },
  { day: 'Wed', classes: ['HIIT 07:00', 'Yoga 12:00', 'Spin 18:00'] },
  { day: 'Thu', classes: ['CrossFit 07:00', 'Pilates 12:00', 'HIIT 18:30'] },
  { day: 'Fri', classes: ['Boxing 07:00', 'Yoga 12:00', 'Spin 17:30'] },
  { day: 'Sat', classes: ['HIIT 09:00', 'CrossFit 10:30', 'Yoga 12:00'] },
]

export default function FitHubPage() {
  const bizName = 'FitHub'
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)
  const [shopProducts, setShopProducts] = useState<any[]>([])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    getPublicProducts().then(res => {
      const list = Array.isArray(res.data) ? res.data : (res.data as any)?.results || []
      setShopProducts(list.filter((p: any) => p.active))
    }).catch(() => {})
  }, [])

  // Group shop products by category for the pricing section
  const shopCategories = shopProducts.length > 0
    ? Object.entries(
        shopProducts.reduce((acc: Record<string, any[]>, p: any) => {
          const cat = p.category || 'Other'
          if (!acc[cat]) acc[cat] = []
          acc[cat].push(p)
          return acc
        }, {})
      ).map(([category, items]) => ({ category, items }))
    : null

  return (
    <div style={{ minHeight: '100vh', background: '#fff', fontFamily: SANS, color: DARK }}>

      <DemoBanner />

      {/* ── Navigation ── */}
      <nav style={{
        position: 'fixed', top: DEMO_BANNER_HEIGHT, left: 0, right: 0, zIndex: 100,
        padding: scrolled ? '0.75rem 2rem' : '1.25rem 2rem',
        background: scrolled ? 'rgba(255,255,255,0.97)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(0,0,0,0.06)' : 'none',
        transition: 'all 0.3s ease',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <a href="/" style={{
          fontWeight: 800, fontSize: '1.5rem',
          color: scrolled ? ACCENT : '#fff', textDecoration: 'none',
          letterSpacing: '-0.02em', textTransform: 'uppercase',
        }}>
          {bizName}
        </a>

        {/* Desktop nav */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="fithub-desktop-nav">
          {[
            { label: 'Classes', href: '#classes' },
            { label: 'Pricing', href: '#pricing' },
            { label: 'Trainers', href: '#trainers' },
            { label: 'Shop', href: '/shop' },
            { label: 'Contact', href: '#contact' },
          ].map(link => (
            <a key={link.label} href={link.href} style={{
              color: scrolled ? MUTED : 'rgba(255,255,255,0.85)',
              textDecoration: 'none', fontSize: '0.88rem', fontWeight: 600,
              letterSpacing: '0.03em', textTransform: 'uppercase',
              transition: 'color 0.2s',
            }}>{link.label}</a>
          ))}
          <a href="/book" style={{
            background: ACCENT, color: '#fff', padding: '0.6rem 1.5rem',
            borderRadius: 4, textDecoration: 'none', fontWeight: 700,
            fontSize: '0.85rem', letterSpacing: '0.05em', textTransform: 'uppercase',
            transition: 'background 0.2s',
          }}>Join Now</a>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenu(!mobileMenu)}
          className="fithub-mobile-btn"
          style={{
            display: 'none', background: 'none', border: 'none', cursor: 'pointer',
            padding: 8, color: scrolled ? DARK : '#fff', fontSize: '1.5rem',
          }}
          aria-label="Menu"
        >
          {mobileMenu ? '\u2715' : '\u2630'}
        </button>
      </nav>

      {/* Mobile menu overlay */}
      {mobileMenu && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 99, background: 'rgba(255,255,255,0.98)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2rem',
        }}>
          {[
            { label: 'Classes', href: '#classes' },
            { label: 'Pricing', href: '#pricing' },
            { label: 'Trainers', href: '#trainers' },
            { label: 'Shop', href: '/shop' },
            { label: 'Contact', href: '#contact' },
            { label: 'Join Now', href: '/book' },
          ].map(link => (
            <a key={link.label} href={link.href} onClick={() => setMobileMenu(false)} style={{
              color: DARK, textDecoration: 'none', fontSize: '1.25rem', fontWeight: 600,
              letterSpacing: '0.05em', textTransform: 'uppercase',
            }}>{link.label}</a>
          ))}
        </div>
      )}

      {/* ── Hero ── */}
      <section style={{
        position: 'relative', minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        backgroundImage: `url(${HERO_IMG})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.35) 50%, rgba(0,0,0,0.6) 100%)',
        }} />
        <div style={{ position: 'relative', textAlign: 'center', padding: '2rem', maxWidth: 700 }}>
          <div style={{
            fontSize: '0.8rem', fontWeight: 700, color: ACCENT_LIGHT,
            textTransform: 'uppercase', letterSpacing: '0.25em', marginBottom: '1.5rem',
          }}>
            Gym &amp; Fitness
          </div>
          <h1 style={{
            fontWeight: 900, fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
            color: '#fff', lineHeight: 1.05, marginBottom: '1.5rem',
            letterSpacing: '-0.02em', textTransform: 'uppercase',
          }}>
            {bizName}
          </h1>
          <p style={{
            fontSize: 'clamp(1rem, 2.5vw, 1.3rem)',
            color: 'rgba(255,255,255,0.85)', fontWeight: 400,
            marginBottom: '2.5rem', lineHeight: 1.5,
          }}>
            Fitness, wellness &amp; recovery — all under one roof
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/book" style={{
              background: ACCENT, color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              transition: 'background 0.2s',
            }}>Book a Class</a>
            <a href="#pricing" style={{
              background: 'transparent', color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              border: '1px solid rgba(255,255,255,0.4)',
              transition: 'border-color 0.2s',
            }}>View Memberships</a>
          </div>
        </div>
        <div style={{
          position: 'absolute', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
          color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem', textAlign: 'center',
          letterSpacing: '0.15em', textTransform: 'uppercase',
        }}>
          <div style={{ width: 1, height: 40, background: 'rgba(255,255,255,0.3)', margin: '0 auto 0.5rem' }} />
          Scroll
        </div>
      </section>

      {/* ── Demo banner (prominent, right after hero) ── */}
      <section style={{ padding: '1.5rem 2rem', background: DARK, textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <p style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.7)', margin: 0 }}>
            This is a demo website built by <strong style={{ color: '#fff' }}>NBNE</strong>.
            Log in to explore the full admin panel behind it.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <a href="/login?redirect=/admin" style={{
              background: '#fff', color: DARK, padding: '0.55rem 1.5rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '0.82rem',
              letterSpacing: '0.03em', borderRadius: 4,
            }}>Try the Admin Demo</a>
            <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)' }}>
              owner@health-club-x.demo / admin123
            </span>
          </div>
        </div>
      </section>

      {/* ── Welcome strip ── */}
      <section style={{ padding: '5rem 2rem', background: BG_LIGHT, textAlign: 'center' }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{ width: 50, height: 3, background: ACCENT, margin: '0 auto 2rem' }} />
          <h2 style={{
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 800, color: DARK, lineHeight: 1.4, marginBottom: '1.5rem',
            textTransform: 'uppercase', letterSpacing: '-0.01em',
          }}>
            Your fitness journey starts here
          </h2>
          <p style={{
            fontSize: '1rem', color: MUTED, lineHeight: 1.8, maxWidth: 560, margin: '0 auto',
          }}>
            {bizName} is Birmingham&apos;s premier fitness destination. From high-intensity classes and
            personal training to sports massage and physiotherapy, we&apos;ve got everything you need to
            train harder, recover faster, and feel your best.
          </p>
        </div>
      </section>

      {/* ── Class Timetable ── */}
      <section id="classes" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>This week</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>Class Timetable</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
            {CLASS_TIMETABLE.map(day => (
              <div key={day.day} style={{
                background: BG_LIGHT, borderRadius: 8, padding: '1.25rem', textAlign: 'center',
              }}>
                <div style={{
                  fontWeight: 800, fontSize: '0.9rem', color: ACCENT,
                  textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem',
                }}>{day.day}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {day.classes.map(cls => (
                    <div key={cls} style={{
                      fontSize: '0.8rem', color: DARK, fontWeight: 500,
                      background: '#fff', padding: '0.4rem 0.5rem', borderRadius: 4,
                    }}>{cls}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
            <a href="/book" style={{
              display: 'inline-block', background: ACCENT, color: '#fff',
              padding: '0.85rem 2.5rem', textDecoration: 'none',
              fontWeight: 700, fontSize: '0.85rem', letterSpacing: '0.1em',
              textTransform: 'uppercase', borderRadius: 4,
            }}>Book a Class</a>
          </div>
        </div>
      </section>

      {/* ── Pricing / Services ── */}
      <section id="pricing" style={{ padding: '5rem 2rem', background: BG_LIGHT }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Invest in yourself</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>Memberships &amp; Pricing</h2>
          </div>

          {shopCategories ? (
            /* ── Live products from shop ── */
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '2rem' }}>
              {shopCategories.map(cat => (
                <div key={cat.category} style={{
                  background: '#fff', borderRadius: 8, padding: '2rem',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                }}>
                  <h3 style={{
                    fontWeight: 800, fontSize: '1.1rem',
                    color: ACCENT, marginBottom: '1.5rem',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>{cat.category}</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {cat.items.map((p: any) => (
                      <div key={p.id} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      }}>
                        <span style={{ fontSize: '0.9rem', color: DARK }}>{p.name}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0, marginLeft: '1rem' }}>
                          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: ACCENT }}>£{parseFloat(p.price).toFixed(2)}</span>
                          <a href={`/shop?highlight=${p.id}`} style={{
                            fontSize: '0.72rem', fontWeight: 700, color: '#fff', background: ACCENT,
                            padding: '0.3rem 0.65rem', borderRadius: 4, textDecoration: 'none',
                            textTransform: 'uppercase', letterSpacing: '0.05em',
                          }}>Buy</a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* ── Fallback: hardcoded pricing ── */
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '2rem' }}>
              {FALLBACK_SERVICES.map(cat => (
                <div key={cat.category} style={{
                  background: '#fff', borderRadius: 8, padding: '2rem',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                }}>
                  <h3 style={{
                    fontWeight: 800, fontSize: '1.1rem',
                    color: ACCENT, marginBottom: '1.5rem',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>{cat.category}</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {cat.items.map(item => (
                      <div key={item.name} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                      }}>
                        <span style={{ fontSize: '0.9rem', color: DARK }}>{item.name}</span>
                        <span style={{
                          fontSize: '0.9rem', fontWeight: 700, color: ACCENT,
                          flexShrink: 0, marginLeft: '1rem',
                        }}>{item.price}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <a href="/shop" style={{
              display: 'inline-block', background: DARK, color: '#fff',
              padding: '0.85rem 2.5rem', textDecoration: 'none',
              fontWeight: 700, fontSize: '0.85rem', letterSpacing: '0.1em',
              textTransform: 'uppercase', borderRadius: 4,
            }}>Browse Shop</a>
          </div>
        </div>
      </section>

      {/* ── Trainers ── */}
      <section id="trainers" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Expert coaches</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>Meet the Team</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '2rem',
          }}>
            {TEAM.map(member => (
              <div key={member.name} style={{ textAlign: 'center' }}>
                <div style={{
                  width: '100%', aspectRatio: '3/4', borderRadius: 8,
                  overflow: 'hidden', marginBottom: '1.25rem',
                }}>
                  <img
                    src={member.img}
                    alt={member.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    loading="lazy"
                  />
                </div>
                <h3 style={{
                  fontWeight: 800, fontSize: '1.1rem',
                  color: DARK, marginBottom: '0.25rem',
                }}>{member.name}</h3>
                <div style={{
                  fontSize: '0.8rem', fontWeight: 600, color: ACCENT,
                  textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.75rem',
                }}>{member.role}</div>
                <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6 }}>{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Gallery ── */}
      <section style={{ padding: '5rem 2rem', background: BG_LIGHT }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Our facility</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>Gallery</h2>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '0.75rem',
          }}>
            {GALLERY.map((img, i) => (
              <div key={i} style={{
                aspectRatio: i % 3 === 0 ? '4/5' : '1/1',
                borderRadius: 6, overflow: 'hidden',
                gridRow: i % 3 === 0 ? 'span 2' : undefined,
              }}>
                <img
                  src={img}
                  alt={`FitHub ${i + 1}`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.4s' }}
                  loading="lazy"
                  onMouseOver={e => (e.currentTarget.style.transform = 'scale(1.05)')}
                  onMouseOut={e => (e.currentTarget.style.transform = 'scale(1)')}
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Member reviews</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>What Members Say</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
          }}>
            {REVIEWS.map((r, i) => (
              <div key={i} style={{
                background: BG_LIGHT, borderRadius: 8, padding: '2rem',
              }}>
                <div style={{ color: ACCENT, fontSize: '1.1rem', marginBottom: '1rem', letterSpacing: '0.1em' }}>
                  {'★'.repeat(r.stars)}
                </div>
                <p style={{
                  fontSize: '0.95rem', color: '#4a4a4a', lineHeight: 1.7,
                  fontStyle: 'italic', marginBottom: '1.25rem',
                }}>
                  &ldquo;{r.text}&rdquo;
                </p>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: DARK }}>{r.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contact / Hours ── */}
      <section id="contact" style={{ padding: '5rem 2rem', background: BG_LIGHT }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Find us</div>
            <h2 style={{
              fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 800, color: DARK, textTransform: 'uppercase',
            }}>Visit Us</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '3rem',
          }}>
            <div>
              <h3 style={{
                fontWeight: 800, fontSize: '1.1rem',
                color: DARK, marginBottom: '1.25rem', textTransform: 'uppercase',
              }}>Contact</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.95rem', color: MUTED }}>
                <div>
                  <div style={{ fontWeight: 700, color: DARK, marginBottom: '0.25rem' }}>Address</div>
                  8 Riverside Park, Birmingham<br />B1 3CD
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: DARK, marginBottom: '0.25rem' }}>Phone</div>
                  <a href="tel:01234567890" style={{ color: ACCENT, textDecoration: 'none', fontWeight: 600 }}>0121 345 6789</a>
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: DARK, marginBottom: '0.25rem' }}>Email</div>
                  <a href="mailto:hello@fithub.co.uk" style={{ color: ACCENT, textDecoration: 'none', fontWeight: 600 }}>hello@fithub.co.uk</a>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{
                fontWeight: 800, fontSize: '1.1rem',
                color: DARK, marginBottom: '1.25rem', textTransform: 'uppercase',
              }}>Opening Hours</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {HOURS.map(h => (
                  <div key={h.day} style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: '0.95rem', paddingBottom: '0.5rem',
                    borderBottom: '1px solid #e8e8e8',
                  }}>
                    <span style={{ color: DARK, fontWeight: 500 }}>{h.day}</span>
                    <span style={{ color: MUTED, fontWeight: 600 }}>{h.time}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{
              background: '#fff', borderRadius: 8, padding: '2rem',
              display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
              textAlign: 'center',
            }}>
              <h3 style={{
                fontWeight: 800, fontSize: '1.2rem',
                color: DARK, marginBottom: '1rem', textTransform: 'uppercase',
              }}>Ready to Train?</h3>
              <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6, marginBottom: '1.5rem' }}>
                Book a class, sign up for a membership, or grab a PT session — all online, all instant.
              </p>
              <a href="/book" style={{
                display: 'inline-block', background: ACCENT, color: '#fff',
                padding: '0.85rem 2.5rem', textDecoration: 'none',
                fontWeight: 700, fontSize: '0.85rem', letterSpacing: '0.1em',
                textTransform: 'uppercase', borderRadius: 4,
              }}>Get Started</a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        padding: '3rem 2rem', background: '#111', textAlign: 'center',
        borderTop: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{
            fontWeight: 900, fontSize: '1.25rem',
            color: '#fff', marginBottom: '1rem', textTransform: 'uppercase',
            letterSpacing: '-0.01em',
          }}>{bizName}</div>
          <div style={{
            display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap',
            fontSize: '0.8rem', marginBottom: '1.5rem',
          }}>
            <a href="#classes" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Classes</a>
            <a href="#pricing" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Pricing</a>
            <a href="#trainers" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Trainers</a>
            <a href="#contact" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Contact</a>
            <a href="/book" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Book Online</a>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.25)' }}>
            &copy; {new Date().getFullYear()} {bizName}. All rights reserved. &nbsp;|&nbsp; Powered by NBNE
          </div>
        </div>
      </footer>

      {/* ── Responsive CSS ── */}
      <style>{`
        @media (max-width: 768px) {
          .fithub-desktop-nav { display: none !important; }
          .fithub-mobile-btn { display: block !important; }
        }
        @media (min-width: 769px) {
          .fithub-mobile-btn { display: none !important; }
        }
        html { scroll-behavior: smooth; }
        img { display: block; }
        * { box-sizing: border-box; margin: 0; }
      `}</style>
    </div>
  )
}
