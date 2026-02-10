'use client'

import { useState, useEffect } from 'react'
import { getServices, getSlots, createBooking } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

interface BookingState {
  step: 'service' | 'date' | 'details' | 'confirm'
  selectedService: any | null
  selectedDate: string
  selectedSlot: any | null
  slots: any[]
  name: string; email: string; phone: string; notes: string
}

export default function PublicHomePage() {
  const tenant = useTenant()
  const [services, setServices] = useState<any[]>([])
  const [loadingServices, setLoadingServices] = useState(true)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [state, setState] = useState<BookingState>({
    step: 'service', selectedService: null, selectedDate: '', selectedSlot: null,
    slots: [], name: '', email: '', phone: '', notes: '',
  })
  const [confirmed, setConfirmed] = useState<{ id: number; service: string } | null>(null)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoadingServices(false) })
  }, [])

  function selectService(svc: any) {
    setState(s => ({ ...s, selectedService: svc, step: 'date' }))
  }

  async function selectDate(dateStr: string) {
    setLoadingSlots(true)
    setState(s => ({ ...s, selectedDate: dateStr, selectedSlot: null, slots: [] }))
    const res = await getSlots({ date_from: dateStr, date_to: dateStr })
    setState(s => ({ ...s, slots: res.data || [] }))
    setLoadingSlots(false)
  }

  function selectSlot(slot: any) {
    setState(s => ({ ...s, selectedSlot: slot, step: 'details' }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    const res = await createBooking({
      service_id: state.selectedService!.id,
      time_slot_id: state.selectedSlot!.id,
      customer_name: state.name,
      customer_email: state.email,
      customer_phone: state.phone,
      notes: state.notes,
    })
    setSubmitting(false)
    if (res.data) {
      setConfirmed({ id: res.data.id, service: state.selectedService!.name })
      setState(s => ({ ...s, step: 'confirm' }))
    }
  }

  // Generate next 14 days
  const dates: string[] = []
  for (let i = 0; i < 14; i++) {
    const d = new Date(); d.setDate(d.getDate() + i)
    dates.push(d.toISOString().split('T')[0])
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      <header style={{ background: 'var(--color-primary-dark)', color: '#fff', padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ color: '#fff', fontSize: '1.5rem' }}>{tenant.business_name}</h1>
        <a href="/login" style={{ color: '#fff', opacity: 0.8, fontSize: '0.85rem' }}>Staff Login →</a>
      </header>

      <main style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem' }}>
        {state.step === 'service' && (
          <div>
            <h2 style={{ marginBottom: '1rem' }}>Choose a Service</h2>
            {loadingServices ? <div className="empty-state">Loading services…</div> : (
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {services.filter((s: any) => s.is_active !== false).map((svc: any) => (
                  <div key={svc.id} className="card" style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onClick={() => selectService(svc)}>
                    <div>
                      <strong>{svc.name}</strong>
                      <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{svc.description}</div>
                      <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>{svc.duration_minutes} min</div>
                    </div>
                    <div style={{ textAlign: 'right', whiteSpace: 'nowrap', marginLeft: '1rem' }}>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--color-primary-dark)' }}>{formatPrice(svc.price_pence)}</div>
                      {(svc.deposit_percentage > 0 || svc.deposit_pence > 0) && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          Deposit: {svc.deposit_percentage > 0 ? `${svc.deposit_percentage}%` : formatPrice(svc.deposit_pence)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {state.step === 'date' && (
          <div>
            <button className="btn btn-ghost" onClick={() => setState(s => ({ ...s, step: 'service' }))}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>Pick a Date — {state.selectedService!.name}</h2>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
              {dates.map(d => (
                <button key={d} className={`btn ${state.selectedDate === d ? 'btn-primary' : 'btn-outline'}`} style={{ minWidth: 90 }} onClick={() => selectDate(d)}>
                  {new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}
                </button>
              ))}
            </div>
            {state.selectedDate && (
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>Available Times</h3>
                {loadingSlots ? <div className="empty-state">Loading slots…</div> : (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {state.slots.filter((s: any) => s.has_capacity).map((slot: any) => (
                      <button key={slot.id} className="btn btn-outline" onClick={() => selectSlot(slot)}>
                        {slot.start_time.slice(0, 5)}
                      </button>
                    ))}
                    {state.slots.filter((s: any) => s.has_capacity).length === 0 && (
                      <p style={{ color: 'var(--color-text-muted)' }}>No slots available on this date.</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {state.step === 'details' && (
          <div>
            <button className="btn btn-ghost" onClick={() => setState(s => ({ ...s, step: 'date' }))}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>Your Details</h2>
            <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem', background: 'var(--color-primary-light)' }}>
              <strong>{state.selectedService!.name}</strong> — {state.selectedDate} at {state.selectedSlot!.start_time.slice(0, 5)}
              <div style={{ fontWeight: 700, marginTop: '0.25rem' }}>{formatPrice(state.selectedService!.price_pence)}</div>
            </div>
            <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
              <div><label>Full Name</label><input required value={state.name} onChange={e => setState(s => ({ ...s, name: e.target.value }))} /></div>
              <div><label>Email</label><input type="email" required value={state.email} onChange={e => setState(s => ({ ...s, email: e.target.value }))} /></div>
              <div><label>Phone</label><input type="tel" required value={state.phone} onChange={e => setState(s => ({ ...s, phone: e.target.value }))} /></div>
              <div><label>Notes (optional)</label><textarea rows={3} value={state.notes} onChange={e => setState(s => ({ ...s, notes: e.target.value }))} /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={submitting}>
                {submitting ? 'Submitting…' : 'Confirm Booking'}
              </button>
            </form>
          </div>
        )}

        {state.step === 'confirm' && confirmed && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
            <h2>Booking Confirmed!</h2>
            <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
              Reference: <strong>#{confirmed.id}</strong> — {confirmed.service}
            </p>
            <p style={{ color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
              {state.selectedDate} at {state.selectedSlot?.start_time.slice(0, 5)}
            </p>
            <button className="btn btn-primary" style={{ marginTop: '2rem' }} onClick={() => { setState({ step: 'service', selectedService: null, selectedDate: '', selectedSlot: null, slots: [], name: '', email: '', phone: '', notes: '' }); setConfirmed(null) }}>
              Book Another
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
