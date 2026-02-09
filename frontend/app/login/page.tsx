'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading…</div>}>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const tenant = useTenant()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get('redirect') || '/app'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Extract username from email (e.g. owner@demo.local → owner)
      const username = email.includes('@') ? email.split('@')[0] : email

      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()
      if (data.ok) {
        // Store JWT tokens in localStorage for API client
        if (data.access && data.refresh) {
          localStorage.setItem('nbne_access', data.access)
          localStorage.setItem('nbne_refresh', data.refresh)
        }
        // Force password change on first login
        if (data.must_change_password) {
          router.push('/set-password')
          return
        }
        // Route based on role
        const role = data.user?.role
        if (role === 'owner' || role === 'manager') {
          router.push(redirect.startsWith('/admin') ? redirect : '/admin')
        } else if (role === 'staff') {
          router.push(redirect.startsWith('/app') ? redirect : '/app')
        } else {
          router.push('/')
        }
      } else {
        setError(data.error || 'Invalid credentials')
      }
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ maxWidth: 420, width: '90%' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem' }}>{tenant.business_name}</h1>
          <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
          {error && (
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your.email@company.com" required autoFocus />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          {tenant.slug && tenant.slug !== 'nbne' && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--color-primary-light)', borderRadius: 'var(--radius)', fontSize: '0.8rem' }}>
              <strong>Demo Accounts:</strong>
              <div style={{ marginTop: '0.5rem', display: 'grid', gap: '0.25rem' }}>
                <div><code>owner@demo.local</code> / admin123 — <span className="badge badge-info">Owner</span></div>
                <div><code>manager@demo.local</code> / admin123 — <span className="badge badge-success">Manager</span></div>
                <div><code>staff1@demo.local</code> / admin123 — <span className="badge badge-neutral">Staff</span></div>
              </div>
            </div>
          )}

          <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            <a href="/">← Back to public site</a>
          </p>
        </form>
      </div>
    </div>
  )
}
