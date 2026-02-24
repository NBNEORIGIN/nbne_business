'use client'

import { useState } from 'react'
import { sendFeedback } from '@/lib/api'

export default function FeedbackWidget() {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ type: 'bug', message: '', page: '' })
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ ok?: boolean; message?: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.message.trim()) return
    setSubmitting(true)
    setResult(null)
    try {
      const res = await sendFeedback({
        ...form,
        page: typeof window !== 'undefined' ? window.location.pathname : '',
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      })
      if (res.error) {
        setResult({ ok: false, message: res.error })
      } else {
        setResult({ ok: true, message: 'Thanks! Your feedback has been sent.' })
        setForm({ type: 'bug', message: '', page: '' })
        setTimeout(() => { setOpen(false); setResult(null) }, 2500)
      }
    } catch {
      setResult({ ok: false, message: 'Failed to send. Please try again.' })
    }
    setSubmitting(false)
  }

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          title="Send feedback"
          style={{
            position: 'fixed', bottom: 20, left: 20, zIndex: 1000,
            width: 44, height: 44, borderRadius: '50%',
            background: '#6366f1', color: '#fff', border: 'none',
            cursor: 'pointer', fontSize: '1.2rem',
            boxShadow: '0 4px 16px rgba(99,102,241,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'transform 0.15s',
          }}
          onMouseOver={e => (e.currentTarget.style.transform = 'scale(1.1)')}
          onMouseOut={e => (e.currentTarget.style.transform = 'scale(1)')}
        >
          💬
        </button>
      )}

      {/* Feedback panel */}
      {open && (
        <div style={{
          position: 'fixed', bottom: 20, left: 20, zIndex: 1001,
          width: 340, background: '#fff', borderRadius: 12,
          boxShadow: '0 8px 40px rgba(0,0,0,0.15)',
          border: '1px solid #e5e7eb',
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            padding: '0.75rem 1rem',
            background: '#6366f1', color: '#fff',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Send Feedback</span>
            <button
              onClick={() => { setOpen(false); setResult(null) }}
              style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.1rem', padding: 0 }}
            >
              ✕
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit} style={{ padding: '1rem' }}>
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>Type</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {[
                  { value: 'bug', label: '🐛 Bug' },
                  { value: 'feature', label: '💡 Idea' },
                  { value: 'general', label: '💬 General' },
                ].map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setForm({ ...form, type: opt.value })}
                    style={{
                      flex: 1, padding: '0.45rem 0.5rem',
                      border: `1.5px solid ${form.type === opt.value ? '#6366f1' : '#d1d5db'}`,
                      borderRadius: 6, fontSize: '0.78rem', fontWeight: 600,
                      background: form.type === opt.value ? '#eef2ff' : '#fff',
                      color: form.type === opt.value ? '#4338ca' : '#6b7280',
                      cursor: 'pointer', transition: 'all 0.15s',
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>
                {form.type === 'bug' ? 'What went wrong?' : form.type === 'feature' ? 'What would help?' : 'Your feedback'}
              </label>
              <textarea
                required
                value={form.message}
                onChange={e => setForm({ ...form, message: e.target.value })}
                rows={4}
                style={{
                  width: '100%', padding: '0.6rem 0.7rem',
                  border: '1px solid #d1d5db', borderRadius: 6,
                  fontSize: '0.85rem', resize: 'vertical',
                  outline: 'none', fontFamily: 'inherit',
                }}
                placeholder={form.type === 'bug' ? 'Describe what happened and what you expected...' : form.type === 'feature' ? 'Describe the feature or improvement...' : 'Tell us anything...'}
              />
            </div>

            {result && (
              <div style={{
                marginBottom: '0.75rem', padding: '0.5rem 0.65rem',
                background: result.ok ? '#dcfce7' : '#fef2f2',
                border: `1px solid ${result.ok ? '#86efac' : '#fecaca'}`,
                borderRadius: 6, fontSize: '0.82rem',
                color: result.ok ? '#166534' : '#b91c1c',
              }}>
                {result.message}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              style={{
                width: '100%', padding: '0.65rem',
                background: submitting ? '#a5b4fc' : '#6366f1', color: '#fff',
                border: 'none', borderRadius: 6, fontSize: '0.85rem', fontWeight: 700,
                cursor: submitting ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {submitting ? 'Sending...' : 'Send Feedback'}
            </button>

            <p style={{ textAlign: 'center', fontSize: '0.72rem', color: '#9ca3af', marginTop: '0.5rem' }}>
              Your current page and role are included automatically.
            </p>
          </form>
        </div>
      )}
    </>
  )
}
