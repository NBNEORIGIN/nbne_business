'use client'

import { useState, useEffect } from 'react'
import { getServices, getBookableStaff, getStaffSlots, getSlots, checkDisclaimer, signDisclaimer, createBooking } from '@/lib/api'
// getSlots still used for legacy TimeSlot fallback path
import { useTenant } from '@/lib/tenant'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

type Step = 'service' | 'staff' | 'datetime' | 'details' | 'disclaimer' | 'confirm'

export default function PublicHomePage() {
  const tenant = useTenant()
  const [step, setStep] = useState<Step>('service')
  const [services, setServices] = useState<any[]>([])
  const [staffList, setStaffList] = useState<any[]>([])
  const [selectedService, setSelectedService] = useState<any>(null)
  const [selectedStaff, setSelectedStaff] = useState<any>(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('')
  const [timeSlots, setTimeSlots] = useState<any[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [disclaimerData, setDisclaimerData] = useState<any>(null)
  const [confirmed, setConfirmed] = useState<any>(null)
  const [loadingServices, setLoadingServices] = useState(true)
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Also keep legacy slot support as fallback
  const [legacySlots, setLegacySlots] = useState<any[]>([])
  const [selectedLegacySlot, setSelectedLegacySlot] = useState<any>(null)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoadingServices(false) })
  }, [])

  async function selectService(svc: any) {
    setSelectedService(svc)
    setSelectedStaff(null)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLoadingStaff(true)
    const res = await getBookableStaff(svc.id)
    const staff = res.data || []
    setStaffList(staff)
    setLoadingStaff(false)
    if (staff.length > 0) {
      setStep('staff')
    } else {
      // No staff configured — fall back to legacy TimeSlot flow
      setStep('datetime')
    }
  }

  function selectStaffMember(s: any) {
    setSelectedStaff(s)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setStep('datetime')
  }

  async function selectDate(dateStr: string) {
    setSelectedDate(dateStr)
    setSelectedTime('')
    setError('')
    setLoadingSlots(true)
    if (selectedStaff) {
      const res = await getStaffSlots(selectedStaff.user_id, selectedService.id, dateStr)
      setTimeSlots(res.data?.slots || [])
      setLegacySlots([])
    } else {
      // Legacy: use pre-created TimeSlots
      const res = await getSlots({ service_id: selectedService.id, date_from: dateStr, date_to: dateStr })
      setLegacySlots(res.data || [])
      setTimeSlots([])
    }
    setLoadingSlots(false)
  }

  function selectTime(time: string) {
    setSelectedTime(time)
    setError('')
    setStep('details')
  }

  function selectLegacySlot(slot: any) {
    setSelectedLegacySlot(slot)
    setSelectedTime(slot.start_time.slice(0, 5))
    setError('')
    setStep('details')
  }

  async function handleDetailsSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    // Check disclaimer before proceeding
    const res = await checkDisclaimer(email)
    if (res.data?.required && !res.data?.valid) {
      setDisclaimerData(res.data.disclaimer)
      setStep('disclaimer')
      return
    }
    // No disclaimer needed or already valid — submit booking
    await submitBooking()
  }

  async function handleDisclaimerSign() {
    if (!disclaimerData) return
    setSubmitting(true)
    const res = await signDisclaimer({ email, name, disclaimer_id: disclaimerData.id })
    setSubmitting(false)
    if (res.data?.signed) {
      await submitBooking()
    } else {
      setError('Failed to sign disclaimer. Please try again.')
    }
  }

  async function submitBooking() {
    setSubmitting(true)
    setError('')
    const bookingData: any = {
      service_id: selectedService.id,
      customer_name: name,
      customer_email: email,
      customer_phone: phone,
      notes,
    }
    if (selectedLegacySlot) {
      // Legacy path: pre-created TimeSlot
      bookingData.time_slot_id = selectedLegacySlot.id
    } else {
      // Staff-aware path: send date + time + staff directly
      bookingData.booking_date = selectedDate
      bookingData.booking_time = selectedTime
      if (selectedStaff) {
        bookingData.staff_id = selectedStaff.user_id
      }
    }
    const res = await createBooking(bookingData)
    setSubmitting(false)
    if (res.data) {
      setConfirmed(res.data)
      setStep('confirm')
    } else {
      setError(res.error || 'Booking failed. Please try again.')
    }
  }

  function resetBooking() {
    setStep('service')
    setSelectedService(null)
    setSelectedStaff(null)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLegacySlots([])
    setSelectedLegacySlot(null)
    setName(''); setEmail(''); setPhone(''); setNotes('')
    setDisclaimerData(null)
    setConfirmed(null)
    setError('')
  }

  // Generate next 14 days
  const dates: string[] = []
  for (let i = 0; i < 14; i++) {
    const d = new Date(); d.setDate(d.getDate() + i)
    dates.push(d.toISOString().split('T')[0])
  }

  const stepLabels = selectedStaff
    ? ['Service', 'Staff', 'Date & Time', 'Details', 'Confirm']
    : ['Service', 'Date & Time', 'Details', 'Confirm']

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      <header style={{ background: 'var(--color-primary-dark)', color: '#fff', padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ color: '#fff', fontSize: '1.5rem' }}>{tenant.business_name}</h1>
        <a href="/login" style={{ color: '#fff', opacity: 0.8, fontSize: '0.85rem' }}>Staff Login →</a>
      </header>

      <main style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem' }}>
        {error && (
          <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', color: '#991b1b' }}>
            {error}
            <button onClick={() => setError('')} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>✕</button>
          </div>
        )}

        {/* Step 1: Service */}
        {step === 'service' && (
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
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--color-primary-dark)' }}>{svc.price_pence > 0 ? formatPrice(svc.price_pence) : 'Contact for pricing'}</div>
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

        {/* Step 2: Staff */}
        {step === 'staff' && (
          <div>
            <button className="btn btn-ghost" onClick={() => setStep('service')}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>Choose Your {tenant.business_name?.toLowerCase().includes('hair') || tenant.business_name?.toLowerCase().includes('salon') ? 'Stylist' : 'Staff Member'}</h2>
            {loadingStaff ? <div className="empty-state">Loading…</div> : (
              <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
                {staffList.map((s: any) => (
                  <div key={s.user_id} className="card" style={{ cursor: 'pointer', textAlign: 'center', padding: '1.5rem 1rem' }} onClick={() => selectStaffMember(s)}>
                    <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--color-primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.75rem', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-primary-dark)' }}>
                      {s.display_name?.charAt(0) || '?'}
                    </div>
                    <strong>{s.display_name}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Date & Time */}
        {step === 'datetime' && (
          <div>
            <button className="btn btn-ghost" onClick={() => setStep(staffList.length > 0 ? 'staff' : 'service')}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>
              Pick a Date{selectedStaff ? ` with ${selectedStaff.display_name}` : ''} — {selectedService?.name}
            </h2>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
              {dates.map(d => (
                <button key={d} className={`btn ${selectedDate === d ? 'btn-primary' : 'btn-outline'}`} style={{ minWidth: 90 }} onClick={() => selectDate(d)}>
                  {new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}
                </button>
              ))}
            </div>
            {selectedDate && (
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>Available Times</h3>
                {loadingSlots ? <div className="empty-state">Loading slots…</div> : (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {/* Staff-aware dynamic slots */}
                    {timeSlots.map((slot: any) => (
                      <button key={slot.start_time} className="btn btn-outline" onClick={() => selectTime(slot.start_time)}>
                        {slot.start_time}
                      </button>
                    ))}
                    {/* Legacy pre-created TimeSlots */}
                    {legacySlots.filter((s: any) => s.has_capacity).map((slot: any) => (
                      <button key={slot.id} className="btn btn-outline" onClick={() => selectLegacySlot(slot)}>
                        {slot.start_time.slice(0, 5)}
                      </button>
                    ))}
                    {timeSlots.length === 0 && legacySlots.filter((s: any) => s.has_capacity).length === 0 && (
                      <p style={{ color: 'var(--color-text-muted)' }}>No slots available on this date.</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 4: Customer Details */}
        {step === 'details' && (
          <div>
            <button className="btn btn-ghost" onClick={() => { setStep('datetime'); setSelectedTime('') }}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>Your Details</h2>
            <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem', background: 'var(--color-primary-light)' }}>
              <strong>{selectedService!.name}</strong>
              {selectedStaff && <span> with {selectedStaff.display_name}</span>}
              <span> — {selectedDate} at {selectedTime}</span>
              <div style={{ fontWeight: 700, marginTop: '0.25rem' }}>{formatPrice(selectedService!.price_pence)}</div>
            </div>
            <form onSubmit={handleDetailsSubmit} style={{ display: 'grid', gap: '1rem' }}>
              <div><label>Full Name</label><input required value={name} onChange={e => setName(e.target.value)} /></div>
              <div><label>Email</label><input type="email" required value={email} onChange={e => setEmail(e.target.value)} /></div>
              <div><label>Phone</label><input type="tel" required value={phone} onChange={e => setPhone(e.target.value)} /></div>
              <div><label>Notes (optional)</label><textarea rows={3} value={notes} onChange={e => setNotes(e.target.value)} /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={submitting}>
                {submitting ? 'Processing…' : 'Continue'}
              </button>
            </form>
          </div>
        )}

        {/* Step 5: Disclaimer */}
        {step === 'disclaimer' && disclaimerData && (
          <div>
            <button className="btn btn-ghost" onClick={() => setStep('details')}>← Back</button>
            <h2 style={{ margin: '1rem 0' }}>{disclaimerData.title}</h2>
            <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem', maxHeight: 300, overflowY: 'auto', fontSize: '0.9rem', lineHeight: 1.6 }}>
              {disclaimerData.body.split('\n').map((line: string, i: number) => (
                <p key={i} style={{ marginBottom: '0.5rem' }}>{line}</p>
              ))}
            </div>
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>By clicking below, you confirm:</p>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.9rem' }}>
                <li>You have read and understood the above terms</li>
                <li>You agree to be bound by these terms</li>
                <li>This agreement is valid for 12 months</li>
              </ul>
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleDisclaimerSign} disabled={submitting}>
              {submitting ? 'Signing…' : 'I Agree — Sign & Continue'}
            </button>
          </div>
        )}

        {/* Step 6: Confirmation */}
        {step === 'confirm' && confirmed && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
            <h2>Booking Confirmed!</h2>
            <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
              Reference: <strong>#{confirmed.id}</strong> — {selectedService?.name}
            </p>
            {selectedStaff && <p style={{ color: 'var(--color-text-muted)' }}>with {selectedStaff.display_name}</p>}
            <p style={{ color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
              {selectedDate} at {selectedTime}
            </p>
            {confirmed.checkout_url && (
              <a href={confirmed.checkout_url} className="btn btn-primary" style={{ display: 'inline-block', marginTop: '1.5rem' }}>
                Pay Deposit Now
              </a>
            )}
            <button className="btn btn-outline" style={{ marginTop: '1rem', display: 'block', margin: '1rem auto 0' }} onClick={resetBooking}>
              Book Another
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
