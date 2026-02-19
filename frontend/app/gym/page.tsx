'use client'

const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#0f0f0f'
const ACCENT = '#dc2626'
const HERO_IMG = 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1920&q=80&auto=format'

export default function GymPage() {
  return (
    <div style={{ minHeight: '100vh', fontFamily: SANS, color: DARK }}>
      {/* Hero */}
      <section style={{
        position: 'relative', minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        backgroundImage: `url(${HERO_IMG})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.45) 50%, rgba(0,0,0,0.7) 100%)',
        }} />
        <div style={{ position: 'relative', textAlign: 'center', padding: '2rem', maxWidth: 700 }}>
          <div style={{
            display: 'inline-block', background: ACCENT, color: '#fff',
            padding: '0.35rem 1rem', borderRadius: 4, marginBottom: '1.5rem',
            fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
          }}>
            Coming Soon
          </div>
          <h1 style={{
            fontFamily: SERIF, fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
            fontWeight: 700, color: '#fff', lineHeight: 1.08, marginBottom: '1.5rem',
            letterSpacing: '-0.02em',
          }}>
            FitHub
          </h1>
          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.2rem)',
            color: 'rgba(255,255,255,0.75)', fontWeight: 400,
            marginBottom: '2.5rem', lineHeight: 1.6, maxWidth: 550, margin: '0 auto 2.5rem',
          }}>
            A high-energy gym website with class timetables, PT booking, membership plans,
            and trainer profiles. Built on the NBNE platform.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: 10, padding: '2rem 2.5rem', maxWidth: 420,
            }}>
              <h3 style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>
                What&apos;s included
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', textAlign: 'left' }}>
                {['Class timetable & booking', 'Personal trainer sessions', 'Membership sign-up & payments', 'Trainer profiles & bios', 'Staff management & rotas', 'CRM & lead tracking'].map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'rgba(255,255,255,0.85)', fontSize: '0.9rem' }}>
                    <span style={{ color: ACCENT, fontWeight: 700 }}>&#10003;</span>
                    {f}
                  </div>
                ))}
              </div>
            </div>

            <a href="/" style={{
              background: '#fff', color: DARK, padding: '0.85rem 2.25rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '0.9rem',
              borderRadius: 6, marginTop: '0.5rem',
            }}>
              &larr; Back to NBNE
            </a>
          </div>
        </div>
      </section>

      <style>{`
        * { box-sizing: border-box; margin: 0; }
        img { display: block; }
      `}</style>
    </div>
  )
}
