'use client'

/**
 * DemoBanner — a fixed top banner shown on all demo sites.
 * Clearly distinct from the site itself (dark NBNE-branded bar).
 * Includes scrolling marquee text + admin panel CTA.
 * Exports DEMO_BANNER_HEIGHT so pages can offset their nav.
 */

export const DEMO_BANNER_HEIGHT = 36

export default function DemoBanner() {
  return (
    <>
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
        height: DEMO_BANNER_HEIGHT,
        background: 'linear-gradient(90deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 1rem',
        borderBottom: '2px solid #2563eb',
        fontFamily: "'Inter', -apple-system, sans-serif",
        overflow: 'hidden',
      }}>
        {/* Scrolling marquee */}
        <div style={{
          flex: 1, overflow: 'hidden', marginRight: '1rem',
          maskImage: 'linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%)',
        }}>
          <div className="nbne-demo-marquee" style={{
            display: 'flex', gap: '3rem', whiteSpace: 'nowrap',
            animation: 'nbne-scroll 25s linear infinite',
            fontSize: '0.72rem', fontWeight: 500, color: 'rgba(255,255,255,0.7)',
            letterSpacing: '0.03em',
          }}>
            {[1, 2].map(i => (
              <span key={i} style={{ display: 'flex', gap: '3rem' }}>
                <span>🔵 This is a <strong style={{ color: '#93c5fd' }}>live demo</strong> by NBNE</span>
                <span>Data resets nightly</span>
                <span>Login: <strong style={{ color: '#fff' }}>owner</strong> / <strong style={{ color: '#fff' }}>admin123</strong></span>
                <span>From £30/month &middot; No per-seat charges</span>
                <span>Website + Booking + Staff + Compliance — all included</span>
                <span>🔵 This is a <strong style={{ color: '#93c5fd' }}>live demo</strong> by NBNE</span>
              </span>
            ))}
          </div>
        </div>

        {/* CTA button */}
        <a href="/login?redirect=/admin" style={{
          flexShrink: 0,
          background: '#2563eb', color: '#fff',
          padding: '0.3rem 0.85rem', borderRadius: 4,
          textDecoration: 'none', fontWeight: 700,
          fontSize: '0.7rem', letterSpacing: '0.02em',
          whiteSpace: 'nowrap',
          transition: 'background 0.2s',
        }}>
          Try Admin Panel &rarr;
        </a>
      </div>

      {/* Spacer so page content isn't hidden behind the fixed banner */}
      <div style={{ height: DEMO_BANNER_HEIGHT }} />

      <style>{`
        @keyframes nbne-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </>
  )
}
