'use client'

import { useState, useEffect } from 'react'
import SalonPage from './salon/page'
import TavolaPage from './restaurant/client-page'
import FitHubPage from './gym/client-page'

/* ── Design tokens ── */
const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#0f0f0f'
const MUTED = '#6b6b6b'
const ACCENT = '#2563eb'          // NBNE brand blue
const ACCENT_DARK = '#1d4ed8'

/* ── Hero images ── */
const HERO_BG = 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920&q=80&auto=format'

/* ── Demo site cards ── */
const DEMOS = [
  {
    title: 'Salon X',
    subtitle: 'Hair & Beauty',
    description: 'A stunning salon website with online booking, Stripe payments, staff profiles, and a full gallery. Everything a modern salon needs.',
    img: 'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800&q=80&auto=format',
    href: '/salon',
    accent: '#8B6F47',
    features: ['Online Booking', 'Stripe Deposits', 'Staff Profiles', 'Service Menu'],
    status: 'live',
  },
  {
    title: 'FitHub',
    subtitle: 'Gym & Fitness',
    description: 'A high-energy gym website with class timetables, membership sign-ups, trainer bios, and integrated booking for PT sessions.',
    img: 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80&auto=format',
    href: 'https://nbne-business-health-club-x.vercel.app',
    accent: '#dc2626',
    features: ['Class Timetable', 'PT Booking', 'Membership Plans', 'Trainer Profiles'],
    status: 'live',
  },
  {
    title: 'Tavola',
    subtitle: 'Restaurant & Dining',
    description: 'An elegant restaurant website with table reservations, seasonal menus, chef profiles, and event booking for private dining.',
    img: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80&auto=format',
    href: 'https://nbne-business-restaurant-x.vercel.app',
    accent: '#059669',
    features: ['Table Reservations', 'Menu Display', 'Event Booking', 'Chef Profiles'],
    status: 'live',
  },
]

const PLATFORM_FEATURES = [
  { icon: '📅', title: 'Online Booking', desc: 'Customers book 24/7. Real-time availability, staff assignment, and instant confirmation.' },
  { icon: '💳', title: 'Stripe Payments', desc: 'Secure deposits and full payments via Stripe Checkout. No-show protection built in.' },
  { icon: '👥', title: 'Staff Management', desc: 'Rotas, timesheets, leave tracking, working hours, and performance all in one place.' },
  { icon: '📊', title: 'CRM & Leads', desc: 'Track every enquiry from first contact to paying customer. Full pipeline visibility.' },
  { icon: '📋', title: 'Compliance', desc: 'Document vault, PAT certificates, disclaimers, and audit trails. Stay inspection-ready.' },
  { icon: '🌐', title: 'Beautiful Website', desc: 'A bespoke, mobile-first website that represents your brand. Not a template — built for you.' },
]

const TESTIMONIALS = [
  { name: 'Sarah M.', biz: 'Salon Owner', text: 'The booking system alone has saved me hours every week. Clients love being able to book online, and the deposit system means no more no-shows.' },
  { name: 'James R.', biz: 'Gym Manager', text: 'Having everything in one platform — bookings, staff, compliance — is a game changer. We ditched three separate tools.' },
  { name: 'Maria L.', biz: 'Restaurant Owner', text: 'The website NBNE built us is gorgeous. We get compliments on it constantly, and the reservation system just works.' },
]

// Non-NBNE tenants render their own client-facing homepage
const TENANT_SLUG = process.env.NEXT_PUBLIC_TENANT_SLUG || ''

export default function HomePage() {
  if (TENANT_SLUG === 'salon-x') return <SalonPage />
  if (TENANT_SLUG === 'restaurant-x') return <TavolaPage />
  if (TENANT_SLUG === 'health-club-x') return <FitHubPage />

  return <NBNELandingPage />
}

function NBNELandingPage() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: '#fff', fontFamily: SANS, color: DARK }}>

      {/* ── Navigation ── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        padding: scrolled ? '0.65rem 2rem' : '1.1rem 2rem',
        background: scrolled ? 'rgba(255,255,255,0.97)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(0,0,0,0.06)' : 'none',
        transition: 'all 0.3s ease',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <a href="/" style={{
          fontWeight: 800, fontSize: '1.3rem',
          color: scrolled ? DARK : '#fff', textDecoration: 'none',
          letterSpacing: '-0.02em',
        }}>
          NBNE
        </a>

        {/* Desktop nav */}
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="nbne-desktop-nav">
          {[
            { label: 'Demos', href: '#demos' },
            { label: 'Platform', href: '#platform' },
            { label: 'Pricing', href: '/pricing' },
          ].map(link => (
            <a key={link.label} href={link.href} style={{
              color: scrolled ? MUTED : 'rgba(255,255,255,0.85)',
              textDecoration: 'none', fontSize: '0.88rem', fontWeight: 500,
              letterSpacing: '0.02em',
              transition: 'color 0.2s',
            }}>{link.label}</a>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenu(!mobileMenu)}
          className="nbne-mobile-btn"
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
            { label: 'Demos', href: '#demos' },
            { label: 'Platform', href: '#platform' },
            { label: 'Pricing', href: '/pricing' },
          ].map(link => (
            <a key={link.label} href={link.href} onClick={() => setMobileMenu(false)} style={{
              color: DARK, textDecoration: 'none', fontSize: '1.25rem', fontWeight: 600,
              letterSpacing: '0.02em',
            }}>{link.label}</a>
          ))}
        </div>
      )}

      {/* ── Hero ── */}
      <section style={{
        position: 'relative', minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        backgroundImage: `url(${HERO_BG})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.65) 100%)',
        }} />
        <div style={{ position: 'relative', textAlign: 'center', padding: '2rem', maxWidth: 800 }}>
          <div style={{
            display: 'inline-block', background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)',
            padding: '0.4rem 1.25rem', borderRadius: 20, marginBottom: '2rem',
            fontSize: '0.82rem', fontWeight: 500, color: 'rgba(255,255,255,0.9)',
            letterSpacing: '0.05em', border: '1px solid rgba(255,255,255,0.15)',
          }}>
            UK-Built &middot; No Hidden Fees &middot; Unlimited Staff
          </div>
          <h1 style={{
            fontFamily: SERIF, fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
            fontWeight: 600, color: '#fff', lineHeight: 1.08, marginBottom: '1.5rem',
            letterSpacing: '-0.02em',
          }}>
            Beautiful websites that<br />
            <span style={{ fontStyle: 'italic', fontWeight: 400 }}>actually run your business</span>
          </h1>
          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.2rem)',
            color: 'rgba(255,255,255,0.75)', fontWeight: 400,
            marginBottom: '2.5rem', lineHeight: 1.6, maxWidth: 600, margin: '0 auto 2.5rem',
          }}>
            One flat price. No per-seat charges. Add as many staff as you want.
            Booking, payments, compliance, CRM &mdash; all included. We even handle the stuff
            you keep meaning to sort out, like PAT certs and document audits.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="#demos" style={{
              background: '#fff', color: DARK, padding: '0.9rem 2.25rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '0.9rem',
              borderRadius: 6, transition: 'transform 0.2s',
            }}>View Live Demos</a>
            <a href="/pricing" style={{
              background: 'transparent', color: '#fff', padding: '0.9rem 2.25rem',
              textDecoration: 'none', fontWeight: 500, fontSize: '0.9rem',
              border: '1px solid rgba(255,255,255,0.35)', borderRadius: 6,
              transition: 'border-color 0.2s',
            }}>See Pricing</a>
          </div>
        </div>
        {/* Scroll indicator */}
        <div style={{
          position: 'absolute', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
          color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem', textAlign: 'center',
          letterSpacing: '0.15em', textTransform: 'uppercase',
        }}>
          <div style={{ width: 1, height: 36, background: 'rgba(255,255,255,0.25)', margin: '0 auto 0.5rem' }} />
          Explore
        </div>
      </section>

      {/* ── Social proof strip ── */}
      <section style={{ padding: '3rem 2rem', background: '#fafafa', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <p style={{ fontSize: '1.05rem', color: MUTED, lineHeight: 1.7 }}>
            <strong style={{ color: DARK }}>Built in the UK for UK businesses.</strong>{' '}
            We&apos;re not a Silicon Valley startup. We&apos;re a small, straight-talking team that builds
            the whole system &mdash; website, booking, payments, staff, compliance, CRM &mdash; and actually picks up the phone.
          </p>
        </div>
      </section>

      {/* ── Demo Sites ── */}
      <section id="demos" style={{ padding: '6rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 600, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '0.75rem',
            }}>Live Demos</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.75rem)',
              fontWeight: 600, color: DARK, marginBottom: '1rem',
            }}>See What We Build</h2>
            <p style={{ fontSize: '1rem', color: MUTED, maxWidth: 560, margin: '0 auto', lineHeight: 1.6 }}>
              Explore our live demo websites. Each one is a fully functional example of what we deliver to clients &mdash; click through, book an appointment, try the admin panel.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
            {DEMOS.map(demo => (
              <a
                key={demo.title}
                href={demo.status === 'live' ? demo.href : undefined}
                style={{
                  display: 'block', textDecoration: 'none', color: DARK,
                  borderRadius: 12, overflow: 'hidden',
                  border: '1px solid #e8e8e8',
                  transition: 'transform 0.25s, box-shadow 0.25s',
                  cursor: demo.status === 'live' ? 'pointer' : 'default',
                  opacity: demo.status === 'live' ? 1 : 0.7,
                }}
                onMouseOver={e => { if (demo.status === 'live') { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.1)' }}}
                onMouseOut={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
              >
                {/* Image */}
                <div style={{ position: 'relative', aspectRatio: '16/10', overflow: 'hidden' }}>
                  <img
                    src={demo.img}
                    alt={demo.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    loading="lazy"
                  />
                  <div style={{
                    position: 'absolute', inset: 0,
                    background: `linear-gradient(transparent 40%, ${demo.accent}cc 100%)`,
                  }} />
                  <div style={{
                    position: 'absolute', bottom: '1rem', left: '1.25rem',
                    color: '#fff',
                  }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', opacity: 0.8, marginBottom: '0.25rem' }}>
                      {demo.subtitle}
                    </div>
                    <div style={{ fontFamily: SERIF, fontSize: '1.5rem', fontWeight: 600 }}>
                      {demo.title}
                    </div>
                  </div>
                  {demo.status === 'coming' && (
                    <div style={{
                      position: 'absolute', top: '1rem', right: '1rem',
                      background: 'rgba(0,0,0,0.6)', color: '#fff', padding: '0.3rem 0.75rem',
                      borderRadius: 20, fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.05em',
                    }}>Coming Soon</div>
                  )}
                  {demo.status === 'live' && (
                    <div style={{
                      position: 'absolute', top: '1rem', right: '1rem',
                      background: 'rgba(255,255,255,0.95)', color: demo.accent, padding: '0.3rem 0.75rem',
                      borderRadius: 20, fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.05em',
                    }}>Live Demo</div>
                  )}
                </div>

                {/* Content */}
                <div style={{ padding: '1.5rem 1.25rem' }}>
                  <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6, marginBottom: '1.25rem' }}>
                    {demo.description}
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {demo.features.map(f => (
                      <span key={f} style={{
                        background: '#f5f5f5', padding: '0.3rem 0.7rem', borderRadius: 4,
                        fontSize: '0.75rem', fontWeight: 600, color: '#555',
                      }}>{f}</span>
                    ))}
                  </div>
                  {demo.status === 'live' && (
                    <div style={{
                      marginTop: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                      fontSize: '0.85rem', fontWeight: 600, color: demo.accent,
                    }}>
                      Explore Demo
                      <span style={{ fontSize: '1rem' }}>&rarr;</span>
                    </div>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ── Platform Features ── */}
      <section id="platform" style={{ padding: '6rem 2rem', background: '#fafafa' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 600, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '0.75rem',
            }}>The Platform</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.75rem)',
              fontWeight: 600, color: DARK, marginBottom: '1rem',
            }}>Everything Under One Roof</h2>
            <p style={{ fontSize: '1rem', color: MUTED, maxWidth: 560, margin: '0 auto', lineHeight: 1.6 }}>
              Your website is just the front door. Behind it sits a complete business management platform.
            </p>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
          }}>
            {PLATFORM_FEATURES.map(f => (
              <div key={f.title} style={{
                background: '#fff', borderRadius: 10, padding: '2rem',
                border: '1px solid #eee', transition: 'box-shadow 0.2s',
              }}>
                <div style={{ fontSize: '1.75rem', marginBottom: '1rem' }}>{f.icon}</div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: DARK, marginBottom: '0.5rem' }}>{f.title}</h3>
                <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section style={{ padding: '6rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 600, color: ACCENT,
              textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '0.75rem',
            }}>Testimonials</div>
            <h2 style={{
              fontFamily: SERIF, fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
              fontWeight: 600, color: DARK,
            }}>What Business Owners Say</h2>
          </div>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '2rem',
          }}>
            {TESTIMONIALS.map((t, i) => (
              <div key={i} style={{
                background: '#fafafa', borderRadius: 10, padding: '2rem',
                border: '1px solid #eee',
              }}>
                <p style={{
                  fontSize: '0.95rem', color: '#4a4a4a', lineHeight: 1.7,
                  fontStyle: 'italic', marginBottom: '1.5rem',
                }}>
                  &ldquo;{t.text}&rdquo;
                </p>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: DARK }}>{t.name}</div>
                  <div style={{ fontSize: '0.8rem', color: MUTED }}>{t.biz}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Section ── */}
      <section style={{
        padding: '6rem 2rem',
        background: `linear-gradient(135deg, ${DARK} 0%, #1e293b 100%)`,
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.75rem, 4vw, 2.75rem)',
            fontWeight: 600, color: '#fff', marginBottom: '1.25rem', lineHeight: 1.15,
          }}>
            Ready to transform<br />your business?
          </h2>
          <p style={{
            fontSize: '1.05rem', color: 'rgba(255,255,255,0.6)', marginBottom: '2.5rem', lineHeight: 1.6,
          }}>
            Try our live demos, explore the admin panel, and see exactly what you&apos;ll get.
            No sales calls. No commitment. Just click and explore.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/salon" style={{
              background: '#fff', color: DARK, padding: '0.9rem 2.25rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '0.9rem',
              borderRadius: 6,
            }}>Explore Salon Demo</a>
            <a href="/login?redirect=/admin" style={{
              background: 'transparent', color: '#fff', padding: '0.9rem 2.25rem',
              textDecoration: 'none', fontWeight: 500, fontSize: '0.9rem',
              border: '1px solid rgba(255,255,255,0.3)', borderRadius: 6,
            }}>Try Admin Panel</a>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.35)', marginTop: '1.5rem' }}>
            Demo login: <strong>owner@{process.env.NEXT_PUBLIC_TENANT_SLUG || 'demo'}.demo</strong> / <strong>admin123</strong> &mdash; data resets nightly
          </p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        padding: '3rem 2rem', background: '#0a0a0a', textAlign: 'center',
        borderTop: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{
            fontWeight: 800, fontSize: '1.2rem',
            color: '#fff', marginBottom: '1rem', letterSpacing: '-0.02em',
          }}>NBNE</div>
          <div style={{
            display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap',
            fontSize: '0.8rem', marginBottom: '1.5rem',
          }}>
            <a href="/salon" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Salon Demo</a>
            <a href="/gym" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Gym Demo</a>
            <a href="/restaurant" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Restaurant Demo</a>
            <a href="/pricing" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Pricing</a>
            <a href="/login" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Login</a>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.2)' }}>
            &copy; {new Date().getFullYear()} NBNE. All rights reserved.
          </div>
        </div>
      </footer>

      {/* ── Responsive CSS ── */}
      <style>{`
        @media (max-width: 768px) {
          .nbne-desktop-nav { display: none !important; }
          .nbne-mobile-btn { display: block !important; }
        }
        @media (min-width: 769px) {
          .nbne-mobile-btn { display: none !important; }
        }
        html { scroll-behavior: smooth; }
        img { display: block; }
        * { box-sizing: border-box; margin: 0; }
      `}</style>
    </div>
  )
}
