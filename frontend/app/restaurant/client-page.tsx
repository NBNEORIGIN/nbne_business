'use client'

import { useState, useEffect } from 'react'
import DemoBanner, { DEMO_BANNER_HEIGHT } from '@/components/DemoBanner'

/* ── Design tokens ── */
const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const ACCENT = '#059669'        // elegant green
const ACCENT_LIGHT = '#34d399'
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF9F6'
const BG_WARM = '#F0EDE8'

/* ── Unsplash images ── */
const HERO_IMG = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&q=80&auto=format'
const ABOUT_IMG = 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80&auto=format'
const GALLERY = [
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1551218808-94e220e084d2?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1550966871-3ed3cdb51f3a?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1424847651672-bf20a4b0982b?w=600&q=80&auto=format',
]

const TEAM = [
  { name: 'Marco Rossi', role: 'Head Chef & Owner', img: 'https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=400&q=80&auto=format', bio: '15 years in fine dining. Trained in Rome and London. Passionate about seasonal British-Italian cuisine.' },
  { name: 'Elena Marchetti', role: 'Front of House Manager', img: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&q=80&auto=format', bio: 'Sommelier-trained with an eye for detail. Elena ensures every guest feels like a VIP.' },
  { name: 'Chef Luca De Luca', role: 'Sous Chef', img: 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400&q=80&auto=format', bio: 'Specialises in pastry and desserts. His tiramisu is legendary.' },
]

const MENU = [
  { category: 'Table Reservations', items: [{ name: 'Table for 2', price: 'Free' }, { name: 'Table for 4', price: 'Free' }, { name: 'Table for 6', price: 'Free' }, { name: 'Table for 8+', price: 'Free' }] },
  { category: 'Experiences', items: [{ name: 'Afternoon Tea for 2', price: '£55' }, { name: 'Afternoon Tea for 4', price: '£110' }, { name: "Chef's Table (6 Course)", price: '£150' }, { name: 'Sunday Roast', price: '£28pp' }] },
  { category: 'Events', items: [{ name: 'Private Dining (up to 12)', price: '£500' }, { name: 'Corporate Lunch', price: '£45pp' }, { name: 'Corporate Dinner & Drinks', price: '£85pp' }, { name: 'Wedding Reception', price: 'from £3,500' }] },
]

const REVIEWS = [
  { name: 'Sophie T.', text: 'The most beautiful restaurant in Manchester. The tasting menu was extraordinary — every course was a work of art. We\'ll be back for our anniversary.', stars: 5 },
  { name: 'David M.', text: 'Booked the private dining room for a corporate event. Seamless from start to finish. The deposit system made it easy to confirm numbers.', stars: 5 },
  { name: 'Rachel G.', text: 'Sunday roast here is unbeatable. The online booking is so convenient — no more calling and waiting on hold. Love it.', stars: 5 },
]

const HOURS = [
  { day: 'Monday', time: 'Closed' },
  { day: 'Tuesday', time: '12:00 - 22:00' },
  { day: 'Wednesday', time: '12:00 - 22:00' },
  { day: 'Thursday', time: '12:00 - 22:00' },
  { day: 'Friday', time: '12:00 - 23:00' },
  { day: 'Saturday', time: '11:00 - 23:00' },
  { day: 'Sunday', time: '11:00 - 16:00' },
]

export default function TavolaPage() {
  const bizName = 'Tavola'
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

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
          fontFamily: SERIF, fontWeight: 600, fontSize: '1.5rem',
          color: scrolled ? DARK : '#fff', textDecoration: 'none',
          letterSpacing: '0.02em',
        }}>
          {bizName}
        </a>

        {/* Desktop nav */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="tavola-desktop-nav">
          {[
            { label: 'Menu', href: '#menu' },
            { label: 'About', href: '#about' },
            { label: 'Gallery', href: '#gallery' },
            { label: 'Contact', href: '#contact' },
          ].map(link => (
            <a key={link.label} href={link.href} style={{
              color: scrolled ? MUTED : 'rgba(255,255,255,0.85)',
              textDecoration: 'none', fontSize: '0.88rem', fontWeight: 500,
              letterSpacing: '0.03em', textTransform: 'uppercase',
              transition: 'color 0.2s',
            }}>{link.label}</a>
          ))}
          <a href="/book" style={{
            background: ACCENT, color: '#fff', padding: '0.6rem 1.5rem',
            borderRadius: 4, textDecoration: 'none', fontWeight: 600,
            fontSize: '0.85rem', letterSpacing: '0.05em', textTransform: 'uppercase',
            transition: 'background 0.2s',
          }}>Reserve a Table</a>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenu(!mobileMenu)}
          className="tavola-mobile-btn"
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
            { label: 'Menu', href: '#menu' },
            { label: 'About', href: '#about' },
            { label: 'Gallery', href: '#gallery' },
            { label: 'Contact', href: '#contact' },
            { label: 'Reserve a Table', href: '/book' },
          ].map(link => (
            <a key={link.label} href={link.href} onClick={() => setMobileMenu(false)} style={{
              color: DARK, textDecoration: 'none', fontSize: '1.25rem', fontWeight: 500,
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
          background: 'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0.55) 100%)',
        }} />
        <div style={{ position: 'relative', textAlign: 'center', padding: '2rem', maxWidth: 700 }}>
          <div style={{
            fontSize: '0.8rem', fontWeight: 500, color: ACCENT_LIGHT,
            textTransform: 'uppercase', letterSpacing: '0.25em', marginBottom: '1.5rem',
          }}>
            Fine Dining &amp; Events
          </div>
          <h1 style={{
            fontFamily: SERIF, fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
            fontWeight: 500, color: '#fff', lineHeight: 1.1, marginBottom: '1.5rem',
            letterSpacing: '-0.01em',
          }}>
            {bizName}
          </h1>
          <p style={{
            fontFamily: "'Cormorant Garamond', Georgia, serif",
            fontSize: 'clamp(1.1rem, 2.5vw, 1.4rem)',
            color: 'rgba(255,255,255,0.85)', fontWeight: 300,
            fontStyle: 'italic', marginBottom: '2.5rem', lineHeight: 1.5,
          }}>
            Seasonal British-Italian cuisine in the heart of Manchester
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/book" style={{
              background: ACCENT, color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              transition: 'background 0.2s',
            }}>Reserve a Table</a>
            <a href="#menu" style={{
              background: 'transparent', color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 500, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              border: '1px solid rgba(255,255,255,0.4)',
              transition: 'border-color 0.2s',
            }}>View Menu</a>
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
              owner@restaurant-x.demo / admin123
            </span>
          </div>
        </div>
      </section>

      {/* ── Welcome strip ── */}
      <section style={{ padding: '5rem 2rem', background: BG_CREAM, textAlign: 'center' }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{ width: 50, height: 1, background: ACCENT, margin: '0 auto 2rem' }} />
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 500, color: DARK, lineHeight: 1.4, marginBottom: '1.5rem',
          }}>
            A dining experience to remember
          </h2>
          <p style={{
            fontSize: '1rem', color: MUTED, lineHeight: 1.8, maxWidth: 560, margin: '0 auto',
          }}>
            {bizName} brings together the finest seasonal ingredients with Italian culinary tradition.
            Whether it&apos;s an intimate dinner for two, a lavish afternoon tea, or a corporate event
            in our private dining room, every detail is crafted to make your visit exceptional.
          </p>
        </div>
      </section>

      {/* ── Menu / Services ── */}
      <section id="menu" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Book online</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>Reservations &amp; Experiences</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '3rem' }}>
            {MENU.map(cat => (
              <div key={cat.category}>
                <h3 style={{
                  fontFamily: SERIF, fontSize: '1.35rem', fontWeight: 500,
                  color: DARK, marginBottom: '1.5rem',
                  paddingBottom: '0.75rem', borderBottom: `1px solid ${BG_WARM}`,
                }}>{cat.category}</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {cat.items.map(item => (
                    <div key={item.name} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                    }}>
                      <span style={{ fontSize: '0.95rem', color: DARK }}>{item.name}</span>
                      <span style={{
                        fontSize: '0.95rem', fontWeight: 600, color: ACCENT,
                        flexShrink: 0, marginLeft: '1rem',
                      }}>{item.price}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <a href="/book" style={{
              display: 'inline-block', background: DARK, color: '#fff',
              padding: '0.85rem 2.5rem', textDecoration: 'none',
              fontWeight: 600, fontSize: '0.85rem', letterSpacing: '0.1em',
              textTransform: 'uppercase', transition: 'background 0.2s',
            }}>Book Online</a>
          </div>
        </div>
      </section>

      {/* ── About / Team ── */}
      <section id="about" style={{ padding: '5rem 2rem', background: BG_CREAM }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Our people</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>Meet the Team</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2.5rem',
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
                  fontFamily: SERIF, fontSize: '1.2rem', fontWeight: 500,
                  color: DARK, marginBottom: '0.25rem',
                }}>{member.name}</h3>
                <div style={{
                  fontSize: '0.8rem', fontWeight: 500, color: ACCENT,
                  textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.75rem',
                }}>{member.role}</div>
                <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6 }}>{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Gallery ── */}
      <section id="gallery" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Our space</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
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
                  alt={`Tavola ${i + 1}`}
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
      <section style={{ padding: '5rem 2rem', background: BG_WARM }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Guest reviews</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>What Our Guests Say</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
          }}>
            {REVIEWS.map((r, i) => (
              <div key={i} style={{
                background: '#fff', borderRadius: 8, padding: '2rem',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
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
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: DARK }}>{r.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Contact / Hours ── */}
      <section id="contact" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>Find us</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>Visit Us</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '3rem',
          }}>
            <div>
              <h3 style={{
                fontFamily: SERIF, fontSize: '1.2rem', fontWeight: 500,
                color: DARK, marginBottom: '1.25rem',
              }}>Contact</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.95rem', color: MUTED }}>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Address</div>
                  45 Market Square, Manchester<br />M1 2AB
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Phone</div>
                  <a href="tel:01234567890" style={{ color: ACCENT, textDecoration: 'none' }}>0161 234 5678</a>
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Email</div>
                  <a href="mailto:hello@tavola.co.uk" style={{ color: ACCENT, textDecoration: 'none' }}>hello@tavola.co.uk</a>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{
                fontFamily: SERIF, fontSize: '1.2rem', fontWeight: 500,
                color: DARK, marginBottom: '1.25rem',
              }}>Opening Hours</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {HOURS.map(h => (
                  <div key={h.day} style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: '0.95rem', paddingBottom: '0.5rem',
                    borderBottom: '1px solid #f0f0f0',
                  }}>
                    <span style={{ color: DARK }}>{h.day}</span>
                    <span style={{ color: h.time === 'Closed' ? '#ccc' : MUTED, fontWeight: h.time === 'Closed' ? 400 : 500 }}>{h.time}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{
              background: BG_CREAM, borderRadius: 8, padding: '2rem',
              display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
              textAlign: 'center',
            }}>
              <h3 style={{
                fontFamily: SERIF, fontSize: '1.3rem', fontWeight: 500,
                color: DARK, marginBottom: '1rem',
              }}>Ready to Dine?</h3>
              <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6, marginBottom: '1.5rem' }}>
                Reserve your table online for instant confirmation. Deposits taken for large parties to secure your booking.
              </p>
              <a href="/book" style={{
                display: 'inline-block', background: ACCENT, color: '#fff',
                padding: '0.85rem 2.5rem', textDecoration: 'none',
                fontWeight: 600, fontSize: '0.85rem', letterSpacing: '0.1em',
                textTransform: 'uppercase',
              }}>Reserve Now</a>
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
            fontFamily: SERIF, fontSize: '1.25rem', fontWeight: 500,
            color: '#fff', marginBottom: '1rem',
          }}>{bizName}</div>
          <div style={{
            display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap',
            fontSize: '0.8rem', marginBottom: '1.5rem',
          }}>
            <a href="#menu" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Menu</a>
            <a href="#about" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>About</a>
            <a href="#gallery" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Gallery</a>
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
          .tavola-desktop-nav { display: none !important; }
          .tavola-mobile-btn { display: block !important; }
        }
        @media (min-width: 769px) {
          .tavola-mobile-btn { display: none !important; }
        }
        html { scroll-behavior: smooth; }
        img { display: block; }
        * { box-sizing: border-box; margin: 0; }
      `}</style>
    </div>
  )
}
