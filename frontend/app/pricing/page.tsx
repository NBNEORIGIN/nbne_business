'use client'

const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#0f0f0f'
const MUTED = '#6b6b6b'
const ACCENT = '#2563eb'

const FEATURES = [
  { item: 'Bespoke booking website', detail: 'We design, build, host, and maintain it. Your brand, your domain. Not a template.' },
  { item: 'Online booking system', detail: 'Clients book 24/7. You control services, staff, availability, and deposit rules.' },
  { item: 'Stripe payments', detail: 'Take deposits or full payment. No fees from us — just standard Stripe rates (1.4% + 20p).' },
  { item: 'Staff management', detail: 'Rotas, shifts, leave requests, working hours, timesheets, payroll CSV export.' },
  { item: 'CRM & lead tracking', detail: 'Track every enquiry from first contact to paying customer. See revenue per source.' },
  { item: 'Health & safety compliance', detail: 'PAT certs, fire risk assessments, COSHH, incident logs, training tracker. Stay inspection-ready.' },
  { item: 'Team chat', detail: 'Simple internal messaging. Keep work chat off WhatsApp.' },
  { item: 'Document vault', detail: 'Policies, contracts, certificates, insurance docs. All in one place with audit trail.' },
  { item: 'Smart dashboard', detail: 'See revenue at risk, overdue tasks, and daily gaps the moment you log in.' },
  { item: 'Unlimited staff logins', detail: 'No per-seat charges. Add 2 staff or 20 — same price.' },
  { item: 'No per-client fees', detail: 'Your client list grows without your bill growing.' },
  { item: 'Booking reminders', detail: 'Automatic email reminders to reduce no-shows.' },
  { item: 'Reports & analytics', detail: 'Revenue, staff performance, no-show rates, daily takings — all built in.' },
]

const ANTI_FEATURES = [
  'No per-seat charges that punish you for hiring',
  'No per-client fees that penalise growth',
  'No "free tier" that suddenly costs money when you rely on it',
  'No 12-month contracts or lock-in periods',
  'No surprise price increases',
  'No commission on your bookings',
  'No upsell to "premium" features you actually need',
]

const COMPARISON = [
  { feature: 'Monthly cost (5 staff)', nbne: 'From £30', fresha: '£0 + commission', treatwell: '£0 + commission', square: '£0 + fees' },
  { feature: 'Per-seat charges', nbne: 'None', fresha: 'Yes', treatwell: 'N/A', square: 'Yes' },
  { feature: 'Commission on bookings', nbne: 'None', fresha: '20% on new clients', treatwell: 'Up to 35%', square: 'None' },
  { feature: 'Custom website included', nbne: '✓', fresha: '✕', treatwell: '✕', square: '✕' },
  { feature: 'Staff rotas & timesheets', nbne: '✓', fresha: 'Basic', treatwell: '✕', square: '✕' },
  { feature: 'Health & safety compliance', nbne: '✓', fresha: '✕', treatwell: '✕', square: '✕' },
  { feature: 'CRM & lead tracking', nbne: '✓', fresha: 'Basic', treatwell: '✕', square: '✕' },
  { feature: 'Document vault', nbne: '✓', fresha: '✕', treatwell: '✕', square: '✕' },
  { feature: 'UK-based support', nbne: '✓', fresha: 'Limited', treatwell: 'Limited', square: 'Email only' },
]

const FAQS = [
  { q: 'What does the £199 setup fee cover?', a: 'We design and build your bespoke website, configure your booking system, set up your staff accounts, import your services, and get you live. It\'s a one-off — no recurring design fees.' },
  { q: 'Is there a contract?', a: 'No. Pay monthly, cancel anytime. No notice period, no exit fees.' },
  { q: 'What about Stripe fees?', a: 'Stripe charges their standard rate (1.4% + 20p for UK cards). We don\'t add anything on top.' },
  { q: 'Do I need to be technical?', a: 'Not at all. We set everything up for you. You just run your business.' },
  { q: 'Can I use my own domain?', a: 'Yes. We\'ll set up your website on your domain at no extra cost.' },
  { q: 'What if I have more than one location?', a: 'Each location is £30/month with its own setup. Same deal, same features.' },
  { q: 'Where is my data stored?', a: 'Your data is securely hosted on encrypted, enterprise-grade cloud infrastructure. We take backups daily and follow GDPR best practices.' },
  { q: 'What support do I get?', a: 'Real support from real people. Email, chat, or phone. We actually pick up.' },
  { q: 'Can I try before I buy?', a: 'Yes. Our live demos are fully functional — click through, make bookings, explore the admin panel. No signup required.' },
]

export default function PricingPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#fff', fontFamily: SANS, color: DARK }}>

      {/* ── Nav ── */}
      <nav style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0.85rem 2rem', borderBottom: '1px solid #f0f0f0',
        position: 'sticky', top: 0, background: 'rgba(255,255,255,0.97)',
        backdropFilter: 'blur(12px)', zIndex: 50,
      }}>
        <a href="/" style={{ fontWeight: 800, fontSize: '1.3rem', color: DARK, textDecoration: 'none', letterSpacing: '-0.02em' }}>
          NBNE
        </a>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', fontSize: '0.88rem' }}>
          <a href="/#demos" style={{ color: MUTED, textDecoration: 'none' }}>Demos</a>
          <a href="/#platform" style={{ color: MUTED, textDecoration: 'none' }}>Platform</a>
          <a href="/login?redirect=/admin" style={{
            background: ACCENT, color: '#fff', padding: '0.5rem 1.25rem',
            borderRadius: 6, textDecoration: 'none', fontWeight: 700, fontSize: '0.85rem',
          }}>Try Admin Panel</a>
        </div>
      </nav>

      {/* ── Header ── */}
      <section style={{ padding: '5rem 2rem 3rem', textAlign: 'center', background: 'linear-gradient(180deg, #f8fafc 0%, #fff 100%)' }}>
        <div style={{
          display: 'inline-block', background: '#ecfdf5', color: '#065f46',
          padding: '0.35rem 1rem', borderRadius: 20, fontSize: '0.8rem', fontWeight: 600,
          marginBottom: '1.5rem',
        }}>No per-seat charges &middot; No commission &middot; Cancel anytime</div>
        <h1 style={{
          fontFamily: SERIF, fontSize: 'clamp(2rem, 5vw, 3rem)',
          fontWeight: 600, color: DARK, marginBottom: '0.75rem', lineHeight: 1.1,
        }}>
          One price. Everything included.
        </h1>
        <p style={{ fontSize: '1.1rem', color: MUTED, maxWidth: 520, margin: '0 auto', lineHeight: 1.6 }}>
          Your website, booking system, staff management, compliance, CRM, and payments — all under one roof. No surprises.
        </p>
      </section>

      {/* ── Pricing Cards ── */}
      <section style={{ padding: '0 2rem 4rem', maxWidth: 900, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>

          {/* Setup Fee */}
          <div style={{
            borderRadius: 16, border: '1px solid #e5e7eb', padding: '2.5rem 2rem',
            background: '#fff', textAlign: 'center',
          }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: ACCENT, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
              One-Off Setup
            </div>
            <div style={{ fontSize: '3rem', fontWeight: 800, color: DARK, lineHeight: 1 }}>£199</div>
            <div style={{ fontSize: '0.9rem', color: MUTED, marginTop: '0.5rem', marginBottom: '1.5rem' }}>+ VAT &middot; paid once</div>
            <div style={{ display: 'grid', gap: '0.6rem', textAlign: 'left' }}>
              {[
                'Bespoke website design & build',
                'Booking system configuration',
                'Staff accounts & services setup',
                'Domain & hosting setup',
                'Go-live within 5 working days',
              ].map(item => (
                <div key={item} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.88rem', color: '#374151' }}>
                  <span style={{ color: '#22c55e', fontWeight: 700, flexShrink: 0 }}>✓</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Monthly Fee */}
          <div style={{
            borderRadius: 16, border: '2px solid ' + ACCENT, padding: '2.5rem 2rem',
            background: '#fff', textAlign: 'center', position: 'relative',
            boxShadow: `0 8px 32px ${ACCENT}22`,
          }}>
            <div style={{
              position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)',
              background: ACCENT, color: '#fff', padding: '0.3rem 1.25rem',
              borderRadius: 20, fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.05em',
            }}>EVERYTHING INCLUDED</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: ACCENT, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
              Monthly
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '0.25rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 600, color: MUTED }}>from</span>
              <span style={{ fontSize: '3.5rem', fontWeight: 800, color: DARK, lineHeight: 1 }}>£30</span>
            </div>
            <div style={{ fontSize: '0.9rem', color: MUTED, marginTop: '0.5rem', marginBottom: '1.5rem' }}>per month + VAT &middot; cancel anytime</div>
            <a href="/login?redirect=/admin" style={{
              display: 'inline-block', background: ACCENT, color: '#fff',
              padding: '0.75rem 2.5rem', borderRadius: 8, textDecoration: 'none',
              fontWeight: 700, fontSize: '1rem', marginBottom: '1.5rem',
              boxShadow: `0 4px 16px ${ACCENT}44`,
            }}>Try the Admin Panel &rarr;</a>
            <div style={{ display: 'grid', gap: '0.5rem', textAlign: 'left' }}>
              {[
                'Unlimited staff logins',
                'Unlimited client bookings',
                'Stripe payments & deposits',
                'Staff rotas & timesheets',
                'Health & safety compliance',
                'CRM & lead tracking',
                'Reports & analytics',
                'UK-based support',
              ].map(item => (
                <div key={item} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.88rem', color: '#374151' }}>
                  <span style={{ color: '#22c55e', fontWeight: 700, flexShrink: 0 }}>✓</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.82rem', color: MUTED, marginTop: '1.5rem' }}>
          Demo login: <strong>owner</strong> / <strong>admin123</strong> — no signup required, data resets nightly
        </p>
      </section>

      {/* ── What's Included (detailed) ── */}
      <section style={{ padding: '4rem 2rem', background: '#fafafa' }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600, color: DARK, marginBottom: '0.5rem', textAlign: 'center',
          }}>Everything you get</h2>
          <p style={{ textAlign: 'center', color: MUTED, marginBottom: '2.5rem', fontSize: '0.95rem' }}>
            No tiers. No add-ons. Every feature, every customer.
          </p>
          <div style={{ display: 'grid', gap: '0.85rem' }}>
            {FEATURES.map(f => (
              <div key={f.item} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', background: '#fff', padding: '1rem 1.25rem', borderRadius: 10, border: '1px solid #eee' }}>
                <span style={{ color: '#22c55e', fontWeight: 700, fontSize: '1.1rem', flexShrink: 0, marginTop: '0.1rem' }}>✓</span>
                <div>
                  <div style={{ fontWeight: 600, color: DARK, fontSize: '0.95rem' }}>{f.item}</div>
                  <div style={{ fontSize: '0.82rem', color: MUTED, lineHeight: 1.5 }}>{f.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── What you won't find ── */}
      <section style={{ padding: '4rem 2rem' }}>
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600, color: DARK, marginBottom: '1.5rem', textAlign: 'center',
          }}>What you won&rsquo;t find here</h2>
          <div style={{ display: 'grid', gap: '0.65rem' }}>
            {ANTI_FEATURES.map(item => (
              <div key={item} style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', fontSize: '0.92rem', color: '#374151' }}>
                <span style={{ color: '#ef4444', fontWeight: 700, flexShrink: 0, fontSize: '1rem' }}>✕</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Comparison Table ── */}
      <section style={{ padding: '4rem 2rem', background: '#fafafa' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600, color: DARK, marginBottom: '0.5rem', textAlign: 'center',
          }}>How we compare</h2>
          <p style={{ textAlign: 'center', color: MUTED, marginBottom: '2.5rem', fontSize: '0.95rem' }}>
            One platform vs. stitching together 3&ndash;4 separate tools.
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', background: '#fff', borderRadius: 12, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
              <thead>
                <tr style={{ background: DARK, color: '#fff' }}>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'left', fontWeight: 600 }}>Feature</th>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'center', fontWeight: 700, color: '#93c5fd' }}>NBNE</th>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'center', fontWeight: 500 }}>Fresha</th>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'center', fontWeight: 500 }}>Treatwell</th>
                  <th style={{ padding: '0.85rem 1rem', textAlign: 'center', fontWeight: 500 }}>Square</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON.map((row, i) => (
                  <tr key={row.feature} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: DARK }}>{row.feature}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', fontWeight: 700, color: row.nbne === '✓' ? '#22c55e' : ACCENT }}>{row.nbne}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: row.fresha === '✕' ? '#ef4444' : MUTED }}>{row.fresha}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: row.treatwell === '✕' ? '#ef4444' : MUTED }}>{row.treatwell}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: row.square === '✕' ? '#ef4444' : MUTED }}>{row.square}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ textAlign: 'center', fontSize: '0.78rem', color: MUTED, marginTop: '1rem' }}>
            Comparison based on publicly available pricing as of 2025. Actual costs may vary.
          </p>
        </div>
      </section>

      {/* ── Three Angles ── */}
      <section style={{ padding: '4rem 2rem' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600, color: DARK, marginBottom: '2.5rem', textAlign: 'center',
          }}>Why business owners switch to NBNE</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {[
              {
                icon: '⏱',
                title: 'Ditch the app juggle',
                body: 'You\'re paying for a booking tool, a payment processor, a rota spreadsheet, and chasing staff on WhatsApp. We replace all of it with one platform, one login, one bill. Less admin, more time doing what you\'re actually good at.',
              },
              {
                icon: '💷',
                title: 'Stop losing money to no-shows',
                body: 'Every empty chair is lost revenue. Our Stripe-powered deposit system means clients have skin in the game before they walk through the door. The dashboard flags bookings without deposits so you can act before it\'s too late.',
              },
              {
                icon: '📋',
                title: 'Stay inspection-ready',
                body: 'PAT certificates, fire risk assessments, COSHH records, staff training logs — the stuff you keep meaning to sort out. We track it all and alert you when something\'s overdue. No more scrambling before an inspection.',
              },
            ].map(angle => (
              <div key={angle.title} style={{
                background: '#fafafa', borderRadius: 12, padding: '2rem',
                border: '1px solid #eee',
              }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{angle.icon}</div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: DARK, marginBottom: '0.75rem' }}>{angle.title}</h3>
                <p style={{ fontSize: '0.9rem', color: MUTED, lineHeight: 1.65 }}>{angle.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section style={{ padding: '4rem 2rem', background: '#fafafa' }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600, color: DARK, marginBottom: '2rem', textAlign: 'center',
          }}>Common questions</h2>
          <div style={{ display: 'grid', gap: '1.25rem' }}>
            {FAQS.map(faq => (
              <div key={faq.q} style={{ background: '#fff', padding: '1.25rem 1.5rem', borderRadius: 10, border: '1px solid #eee' }}>
                <div style={{ fontWeight: 600, color: DARK, fontSize: '0.95rem', marginBottom: '0.35rem' }}>{faq.q}</div>
                <div style={{ fontSize: '0.88rem', color: MUTED, lineHeight: 1.6 }}>{faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section style={{
        padding: '5rem 2rem',
        background: `linear-gradient(135deg, ${DARK} 0%, #1e293b 100%)`,
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: SERIF, fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
            fontWeight: 600, color: '#fff', marginBottom: '1rem', lineHeight: 1.15,
          }}>
            You didn&rsquo;t open your business<br />to wrestle with software.
          </h2>
          <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.6)', marginBottom: '2rem', lineHeight: 1.6 }}>
            Try the full platform. No signup. No credit card. No sales call.<br />
            Just click and see what £30/month actually gets you.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/login?redirect=/admin" style={{
              background: ACCENT, color: '#fff', padding: '1rem 2.75rem',
              textDecoration: 'none', fontWeight: 700, fontSize: '1rem',
              borderRadius: 6, boxShadow: `0 4px 24px ${ACCENT}66`,
            }}>Try the Admin Panel &rarr;</a>
            <a href="/#demos" style={{
              background: 'transparent', color: '#fff', padding: '1rem 2.25rem',
              textDecoration: 'none', fontWeight: 500, fontSize: '0.9rem',
              border: '1px solid rgba(255,255,255,0.3)', borderRadius: 6,
            }}>Explore Demos</a>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.35)', marginTop: '1.5rem' }}>
            Demo login: <strong>owner</strong> / <strong>admin123</strong> &mdash; data resets nightly
          </p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        padding: '3rem 2rem', background: '#0a0a0a', textAlign: 'center',
        borderTop: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{ fontWeight: 800, fontSize: '1.2rem', color: '#fff', marginBottom: '1rem', letterSpacing: '-0.02em' }}>NBNE</div>
          <div style={{
            display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap',
            fontSize: '0.8rem', marginBottom: '1.5rem',
          }}>
            <a href="/" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Home</a>
            <a href="/#demos" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Demos</a>
            <a href="/#platform" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Platform</a>
            <a href="/login" style={{ color: 'rgba(255,255,255,0.5)', textDecoration: 'none' }}>Login</a>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.25)' }}>
            Built in Britain. Straightforward pricing. Proper support.
          </p>
          <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.15)', marginTop: '0.5rem' }}>
            &copy; {new Date().getFullYear()} NBNE. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
