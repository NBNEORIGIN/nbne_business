'use client'

import { useState, useEffect } from 'react'
import DemoBanner, { DEMO_BANNER_HEIGHT } from '@/components/DemoBanner'

/* ── Design tokens ── */
const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const ACCENT = '#8B6F47'        // warm gold-brown
const ACCENT_LIGHT = '#C4A97D'  // lighter gold
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF8F5'
const BG_WARM = '#F5F0EB'

/* ── Unsplash images (salon-appropriate, free to use) ── */
const HERO_IMG = 'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1920&q=80&auto=format'
const ABOUT_IMG = 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&q=80&auto=format'
const GALLERY = [
  'https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1562322140-8baeececf3df?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1559599101-f09722fb4948?w=600&q=80&auto=format',
  'https://images.unsplash.com/photo-1522338242992-e1a54571a9f7?w=600&q=80&auto=format',
]

const TEAM = [
  { name: 'Chloe Williams', role: 'Senior Stylist', img: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80&auto=format', bio: 'Colour specialist with 8 years experience. Balayage and lived-in colour.' },
  { name: 'Emma Johnson', role: 'Stylist', img: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80&auto=format', bio: 'Creative cuts and styling. Passionate about textured, modern looks.' },
  { name: 'Sophie Taylor', role: 'Junior Stylist', img: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&q=80&auto=format', bio: 'Blow-dry queen and up-and-coming talent. Fresh from advanced training.' },
]

const SERVICES = [
  { category: 'Cuts', items: [{ name: 'Ladies\' Cut & Blow Dry', price: '£45' }, { name: 'Restyle', price: '£55' }, { name: 'Men\'s Cut', price: '£22' }, { name: 'Children\'s Cut', price: '£18' }] },
  { category: 'Colour', items: [{ name: 'Full Head Colour', price: '£75' }, { name: 'Balayage', price: '£140' }, { name: 'Highlights (Half Head)', price: '£85' }, { name: 'Root Touch-Up', price: '£55' }] },
  { category: 'Styling', items: [{ name: 'Blow Dry', price: '£30' }, { name: 'Occasion Hair', price: '£55' }, { name: 'Bridal Hair', price: 'from £85' }, { name: 'Hair Treatment', price: '£25' }] },
]

const REVIEWS = [
  { name: 'Sarah M.', text: 'Absolutely love my balayage! Chloe really listened to what I wanted and the result was even better than I imagined. The salon is gorgeous too.', stars: 5 },
  { name: 'Rachel K.', text: 'Best salon I\'ve been to in years. The online booking is so easy and the deposit system means no messing about. Highly recommend.', stars: 5 },
  { name: 'Louise T.', text: 'Emma did an incredible job on my restyle. I\'ve had so many compliments! The whole experience from booking to leaving was perfect.', stars: 5 },
]

const HOURS = [
  { day: 'Monday', time: 'Closed' },
  { day: 'Tuesday', time: '9:00 - 17:30' },
  { day: 'Wednesday', time: '9:00 - 17:30' },
  { day: 'Thursday', time: '9:00 - 19:00' },
  { day: 'Friday', time: '9:00 - 17:30' },
  { day: 'Saturday', time: '9:00 - 16:00' },
  { day: 'Sunday', time: 'Closed' },
]

export default function SalonPage() {
  const bizName = 'Salon X'
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
        <a href="/salon" style={{
          fontFamily: SERIF, fontWeight: 600, fontSize: '1.5rem',
          color: scrolled ? DARK : '#fff', textDecoration: 'none',
          letterSpacing: '0.02em',
        }}>
          {bizName}
        </a>

        {/* Desktop nav */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="desktop-nav">
          {[
            { label: 'Services', href: '#services' },
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
          }}>Book Now</a>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenu(!mobileMenu)}
          className="mobile-menu-btn"
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
            { label: 'Services', href: '#services' },
            { label: 'About', href: '#about' },
            { label: 'Gallery', href: '#gallery' },
            { label: 'Contact', href: '#contact' },
            { label: 'Book Now', href: '/book' },
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
          background: 'linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0.5) 100%)',
        }} />
        <div style={{ position: 'relative', textAlign: 'center', padding: '2rem', maxWidth: 700 }}>
          <div style={{
            fontSize: '0.8rem', fontWeight: 500, color: ACCENT_LIGHT,
            textTransform: 'uppercase', letterSpacing: '0.25em', marginBottom: '1.5rem',
          }}>
            Welcome to
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
            Where style meets confidence
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/book" style={{
              background: ACCENT, color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              transition: 'background 0.2s',
            }}>Book Your Appointment</a>
            <a href="#services" style={{
              background: 'transparent', color: '#fff', padding: '1rem 2.5rem',
              textDecoration: 'none', fontWeight: 500, fontSize: '0.9rem',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              border: '1px solid rgba(255,255,255,0.4)',
              transition: 'border-color 0.2s',
            }}>View Services</a>
          </div>
        </div>
        {/* Scroll indicator */}
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
              owner@salon-x.demo / admin123
            </span>
          </div>
        </div>
      </section>

      {/* ── Welcome strip ── */}
      <section style={{ padding: '5rem 2rem', background: BG_CREAM, textAlign: 'center' }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{
            width: 50, height: 1, background: ACCENT, margin: '0 auto 2rem',
          }} />
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 500, color: DARK, lineHeight: 1.4, marginBottom: '1.5rem',
          }}>
            A warm welcome awaits you at {bizName}
          </h2>
          <p style={{
            fontSize: '1rem', color: MUTED, lineHeight: 1.8, maxWidth: 560, margin: '0 auto',
          }}>
            Nestled in the heart of town, {bizName} is your destination for exceptional hair care.
            Our talented team combines years of experience with a genuine passion for making you look
            and feel your absolute best. From precision cuts to stunning colour transformations,
            every visit is tailored to you.
          </p>
        </div>
      </section>

      {/* ── Services ── */}
      <section id="services" style={{ padding: '5rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 500, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: '0.75rem',
            }}>What we offer</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>Our Services</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '3rem' }}>
            {SERVICES.map(cat => (
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
            }}>Book an Appointment</a>
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
            }}>Get to know us</div>
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
            }}>Our work</div>
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
                  alt={`Salon work ${i + 1}`}
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
            }}>Kind words</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 500, color: DARK,
            }}>What Our Clients Say</h2>
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
            {/* Address & contact */}
            <div>
              <h3 style={{
                fontFamily: SERIF, fontSize: '1.2rem', fontWeight: 500,
                color: DARK, marginBottom: '1.25rem',
              }}>Contact</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.95rem', color: MUTED }}>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Address</div>
                  12 High Street, Alnwick<br />Northumberland, NE66 1AB
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Phone</div>
                  <a href="tel:01234567890" style={{ color: ACCENT, textDecoration: 'none' }}>01234 567 890</a>
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, marginBottom: '0.25rem' }}>Email</div>
                  <a href="mailto:hello@salonx.co.uk" style={{ color: ACCENT, textDecoration: 'none' }}>hello@salonx.co.uk</a>
                </div>
              </div>
            </div>

            {/* Opening hours */}
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

            {/* Book CTA */}
            <div style={{
              background: BG_CREAM, borderRadius: 8, padding: '2rem',
              display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
              textAlign: 'center',
            }}>
              <h3 style={{
                fontFamily: SERIF, fontSize: '1.3rem', fontWeight: 500,
                color: DARK, marginBottom: '1rem',
              }}>Ready to Book?</h3>
              <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6, marginBottom: '1.5rem' }}>
                Book your appointment online for instant confirmation. Deposits taken securely via Stripe.
              </p>
              <a href="/book" style={{
                display: 'inline-block', background: ACCENT, color: '#fff',
                padding: '0.85rem 2.5rem', textDecoration: 'none',
                fontWeight: 600, fontSize: '0.85rem', letterSpacing: '0.1em',
                textTransform: 'uppercase',
              }}>Book Now</a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        padding: '3rem 2rem', background: '#111', textAlign: 'center',
        borderTop: `1px solid rgba(255,255,255,0.05)`,
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
            <a href="#services" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Services</a>
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
          .desktop-nav { display: none !important; }
          .mobile-menu-btn { display: block !important; }
        }
        @media (min-width: 769px) {
          .mobile-menu-btn { display: none !important; }
        }
        html { scroll-behavior: smooth; }
        img { display: block; }
        * { box-sizing: border-box; margin: 0; }
      `}</style>
    </div>
  )
}
