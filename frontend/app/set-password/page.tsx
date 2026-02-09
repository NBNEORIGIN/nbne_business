'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { setPassword, getCurrentUser } from '@/lib/api'

export default function SetPasswordPage() {
  const tenant = useTenant()
  const router = useRouter()
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const user = getCurrentUser()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSaving(true)
    const res = await setPassword(newPassword)
    if (res.error) {
      setError(res.error)
      setSaving(false)
      return
    }

    // Password set — redirect to appropriate dashboard
    const role = user?.role
    if (role === 'owner' || role === 'manager') {
      router.push('/admin')
    } else if (role === 'staff') {
      router.push('/app')
    } else {
      router.push('/')
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ maxWidth: 420, width: '90%' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem' }}>{tenant.business_name}</h1>
          <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>Welcome! Please set your password to continue.</p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
          {user && (
            <div style={{ marginBottom: '1.25rem', padding: '0.75rem 1rem', background: 'var(--color-primary-light)', borderRadius: 'var(--radius)', fontSize: '0.9rem' }}>
              Signed in as <strong>{user.name || user.email}</strong>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label className="form-label" htmlFor="new-password">New Password *</label>
            <input id="new-password" className="form-input" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Minimum 8 characters" required autoFocus />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label className="form-label" htmlFor="confirm-password">Confirm Password *</label>
            <input id="confirm-password" className="form-input" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Re-enter your password" required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={saving}>
            {saving ? 'Setting password…' : 'Set Password & Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
