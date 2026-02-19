'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { getServices, getBookableStaff, getStaffSlots, getSlots, checkDisclaimer, signDisclaimer, createBooking, createCheckoutSession, setDemoTenant } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

/* ── Design tokens (matching homepage) ── */
const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const ACCENT = '#8B6F47'
const ACCENT_LIGHT = '#C4A97D'
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF8F5'
const BG_WARM = '#F5F0EB'
const HERO_IMG = 'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1920&q=80&auto=format'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }
function fmtTime(iso: string) { try { return iso.includes('T') ? iso.split('T')[1].slice(0, 5) : iso.slice(0, 5) } catch { return iso } }

/* ── Reusable section card ── */
function Section({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 10, border: '1px solid rgba(139,111,71,0.12)',
      padding: '1.25rem 1.25rem', height: '100%',
      boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', margin: '0 0 0.85rem' }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%', background: BG_WARM,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.75rem', fontWeight: 700, color: ACCENT, flexShrink: 0,
        }}>{num}</div>
        <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, margin: 0 }}>
          {title}
        </h2>
      </div>
      {children}
    </div>
  )
}

/* ── Calendar widget ── */
function Calendar({ selectedDate, onSelect, availableDates }: {
  selectedDate: string; onSelect: (d: string) => void; availableDates: string[]
}) {
  const today = new Date()
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())

  const firstDay = new Date(viewYear, viewMonth, 1).getDay()
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
  const monthName = new Date(viewYear, viewMonth).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })

  const todayStr = today.toISOString().split('T')[0]
  const availSet = new Set(availableDates)

  function prevMonth() {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(viewYear - 1) }
    else setViewMonth(viewMonth - 1)
  }
  function nextMonth() {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(viewYear + 1) }
    else setViewMonth(viewMonth + 1)
  }

  const cells: (number | null)[] = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <button onClick={prevMonth} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: MUTED, padding: '0.25rem 0.5rem' }}>&lsaquo;</button>
        <span style={{ fontFamily: SERIF, fontWeight: 500, fontSize: '0.95rem', color: DARK }}>{monthName}</span>
        <button onClick={nextMonth} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: MUTED, padding: '0.25rem 0.5rem' }}>&rsaquo;</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', textAlign: 'center' }}>
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
          <div key={d} style={{ fontSize: '0.7rem', color: ACCENT_LIGHT, fontWeight: 600, padding: '0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{d}</div>
        ))}
        {cells.map((day, i) => {
          if (day === null) return <div key={`e${i}`} />
          const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
          const isPast = dateStr < todayStr
          const isAvail = availSet.has(dateStr)
          const isSel = dateStr === selectedDate
          const isToday = dateStr === todayStr
          const clickable = !isPast && isAvail
          return (
            <button
              key={dateStr}
              onClick={() => clickable && onSelect(dateStr)}
              disabled={!clickable}
              style={{
                width: 36, height: 36, borderRadius: '50%', border: 'none',
                margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.82rem', fontWeight: isSel || isToday ? 700 : 400,
                cursor: clickable ? 'pointer' : 'default',
                background: isSel ? ACCENT : 'transparent',
                color: isSel ? '#fff' : isPast ? '#d1d5db' : isAvail ? DARK : '#d1d5db',
                outline: isToday && !isSel ? `2px solid ${ACCENT_LIGHT}` : 'none',
                outlineOffset: -2,
                transition: 'all 0.15s ease',
              }}
            >{day}</button>
          )
        })}
      </div>
    </div>
  )
}

function BookPageInner() {
  const tenant = useTenant()
  const searchParams = useSearchParams()
  const demoSlug = searchParams.get('demo') || ''
  const bizName = demoSlug === 'salon-x' ? 'Salon X' : (tenant.business_name || 'Salon-X')

  const [services, setServices] = useState<any[]>([])
  const [staffList, setStaffList] = useState<any[]>([])
  const [timeSlots, setTimeSlots] = useState<any[]>([])
  const [legacySlots, setLegacySlots] = useState<any[]>([])

  const [selectedService, setSelectedService] = useState<any>(null)
  const [selectedStaff, setSelectedStaff] = useState<any>(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('')
  const [selectedLegacySlot, setSelectedLegacySlot] = useState<any>(null)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')

  const [loadingServices, setLoadingServices] = useState(true)
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [disclaimerData, setDisclaimerData] = useState<any>(null)
  const [showDisclaimer, setShowDisclaimer] = useState(false)
  const [confirmed, setConfirmed] = useState<any>(null)

  // Set demo tenant override synchronously so all API calls use the right tenant
  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
    return () => { setDemoTenant(null) }
  }, [demoSlug])

  useEffect(() => {
    // Ensure demo tenant is set before fetching
    if (demoSlug) setDemoTenant(demoSlug)
    getServices().then(r => { setServices(r.data || []); setLoadingServices(false) })
    // Handle Stripe payment return
    const payment = searchParams.get('payment')
    const bookingId = searchParams.get('booking_id')
    if (payment === 'success' && bookingId) {
      setConfirmed({ id: bookingId, payment_success: true })
    } else if (payment === 'cancelled' && bookingId) {
      setError('Payment was cancelled. Your booking has not been confirmed. Please try again.')
    }
  }, [searchParams, demoSlug])

  // Available dates for calendar (next 60 days)
  const availableDates: string[] = []
  for (let i = 0; i < 60; i++) {
    const d = new Date(); d.setDate(d.getDate() + i)
    availableDates.push(d.toISOString().split('T')[0])
  }

  async function selectService(svc: any) {
    setSelectedService(svc)
    setSelectedStaff(null)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLegacySlots([])
    setSelectedLegacySlot(null)
    setLoadingStaff(true)
    const res = await getBookableStaff(svc.id)
    setStaffList(res.data || [])
    setLoadingStaff(false)
  }

  function selectStaffMember(s: any) {
    setSelectedStaff(s)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLegacySlots([])
    setSelectedLegacySlot(null)
  }

  async function selectDate(dateStr: string) {
    setSelectedDate(dateStr)
    setSelectedTime('')
    setSelectedLegacySlot(null)
    setError('')
    setLoadingSlots(true)
    if (selectedStaff) {
      const res = await getStaffSlots(selectedStaff.id, selectedService.id, dateStr)
      setTimeSlots(res.data?.slots || [])
      setLegacySlots([])
    } else {
      const res = await getSlots({ service_id: selectedService.id, date_from: dateStr, date_to: dateStr })
      setLegacySlots(res.data || [])
      setTimeSlots([])
    }
    setLoadingSlots(false)
  }

  function selectTime(time: string) {
    setSelectedTime(time)
    setSelectedLegacySlot(null)
    setError('')
  }

  function selectLegacySlot(slot: any) {
    setSelectedLegacySlot(slot)
    setSelectedTime(slot.start_time.slice(0, 5))
    setError('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    const res = await checkDisclaimer(email)
    if (res.data?.required && !res.data?.valid) {
      setDisclaimerData(res.data.disclaimer)
      setShowDisclaimer(true)
      return
    }
    await submitBooking()
  }

  async function handleDisclaimerSign() {
    if (!disclaimerData) return
    setSubmitting(true)
    const res = await signDisclaimer({ email, name, disclaimer_id: disclaimerData.id })
    setSubmitting(false)
    if (res.data?.signed) {
      setShowDisclaimer(false)
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
      bookingData.time_slot_id = selectedLegacySlot.id
    } else {
      bookingData.booking_date = selectedDate
      bookingData.booking_time = selectedTime
      if (selectedStaff) {
        bookingData.staff_id = selectedStaff.id
      }
    }

    // If service has a price, use Stripe Checkout
    const hasCost = selectedService.price_pence > 0 || selectedService.deposit_pence > 0
    if (hasCost) {
      const res = await createCheckoutSession(bookingData)
      setSubmitting(false)
      if (res.data?.checkout_url) {
        window.location.href = res.data.checkout_url
        return
      } else if (res.data?.free) {
        setConfirmed(res.data)
        return
      } else {
        setError(res.error || 'Payment setup failed. Please try again.')
        return
      }
    }

    // Free service — book directly
    const res = await createBooking(bookingData)
    setSubmitting(false)
    if (res.data) {
      setConfirmed(res.data)
    } else {
      setError(res.error || 'Booking failed. Please try again.')
    }
  }

  function resetBooking() {
    setSelectedService(null)
    setSelectedStaff(null)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLegacySlots([])
    setSelectedLegacySlot(null)
    setName(''); setEmail(''); setPhone(''); setNotes('')
    setDisclaimerData(null)
    setShowDisclaimer(false)
    setConfirmed(null)
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const hasStaff = staffList.length > 0
  const allSlots = [...timeSlots, ...legacySlots.filter((s: any) => s.has_capacity)]
  const staffName = (s: any) => s.display_name || s.name || '?'

  // ── Confirmation overlay ──
  if (confirmed) {
    return (
      <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS }}>
        <header style={{
          background: `linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url(${HERO_IMG}) center/cover`,
          color: '#fff', padding: '1.25rem 2rem', textAlign: 'center',
        }}>
          <a href="/" style={{ fontFamily: SERIF, color: '#fff', textDecoration: 'none', fontWeight: 500, fontSize: '1.4rem', letterSpacing: '0.02em' }}>{bizName}</a>
        </header>
        <div style={{ maxWidth: 480, margin: '0 auto', padding: '4rem 1.5rem', textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%', background: BG_WARM,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.5rem', fontSize: '1.5rem', color: ACCENT,
          }}>✓</div>
          <h1 style={{ fontFamily: SERIF, fontSize: '1.75rem', fontWeight: 500, color: DARK, marginBottom: '0.5rem' }}>Booking Confirmed</h1>
          <p style={{ color: MUTED, marginBottom: '1.5rem' }}>Reference: <strong>#{confirmed.id}</strong></p>
          {confirmed.payment_success && (
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1.5rem', fontSize: '0.9rem', color: '#166534' }}>
              ✓ Payment received — your booking is confirmed.
            </div>
          )}
          {selectedService && (
            <div style={{ background: '#fff', borderRadius: 10, padding: '1.5rem', border: `1px solid rgba(139,111,71,0.12)`, textAlign: 'left', marginBottom: '1.5rem' }}>
              <div style={{ display: 'grid', gap: '0.6rem', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED }}>Service</span><strong style={{ color: DARK }}>{selectedService?.name}</strong></div>
                {selectedStaff && <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED }}>Stylist</span><strong style={{ color: DARK }}>{staffName(selectedStaff)}</strong></div>}
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED }}>Date</span><strong style={{ color: DARK }}>{selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED }}>Time</span><strong style={{ color: DARK }}>{selectedTime}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.4rem', borderTop: `1px solid ${BG_WARM}` }}><span style={{ color: MUTED }}>Price</span><strong style={{ color: ACCENT, fontSize: '1rem' }}>{formatPrice(selectedService.price_pence)}</strong></div>
              </div>
            </div>
          )}
          <div><button onClick={resetBooking} style={{ background: 'none', border: 'none', color: ACCENT, fontSize: '0.9rem', cursor: 'pointer', fontWeight: 600, marginTop: '0.5rem', letterSpacing: '0.03em' }}>Book Another Appointment</button></div>
        </div>
      </div>
    )
  }

  // ── Disclaimer overlay ──
  if (showDisclaimer && disclaimerData) {
    return (
      <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS }}>
        <header style={{
          background: `linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url(${HERO_IMG}) center/cover`,
          color: '#fff', padding: '1.25rem 2rem',
        }}>
          <a href="/" style={{ fontFamily: SERIF, color: '#fff', textDecoration: 'none', fontWeight: 500, fontSize: '1.4rem', letterSpacing: '0.02em' }}>{bizName}</a>
        </header>
        <div style={{ maxWidth: 560, margin: '0 auto', padding: '2rem 1.5rem' }}>
          <h2 style={{ fontFamily: SERIF, fontSize: '1.25rem', fontWeight: 500, color: DARK, marginBottom: '1rem' }}>{disclaimerData.title}</h2>
          <div style={{ background: '#fff', borderRadius: 10, padding: '1.5rem', border: `1px solid rgba(139,111,71,0.12)`, maxHeight: 320, overflowY: 'auto', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.25rem', color: MUTED }}>
            {disclaimerData.body.split('\n').map((line: string, i: number) => (<p key={i} style={{ marginBottom: '0.5rem' }}>{line}</p>))}
          </div>
          <div style={{ background: BG_WARM, border: `1px solid rgba(139,111,71,0.15)`, borderRadius: 8, padding: '1rem', marginBottom: '1.25rem' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem', color: DARK }}>By clicking below, you confirm:</p>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: MUTED }}>
              <li>You have read and understood the above terms</li>
              <li>You agree to be bound by these terms</li>
              <li>This agreement is valid for 12 months</li>
            </ul>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleDisclaimerSign} disabled={submitting} style={{ flex: 1, padding: '0.75rem', borderRadius: 6, border: 'none', background: ACCENT, color: '#fff', fontWeight: 600, cursor: 'pointer', letterSpacing: '0.03em' }}>{submitting ? 'Signing…' : 'I Agree — Continue'}</button>
            <button onClick={() => setShowDisclaimer(false)} style={{ padding: '0.75rem 1.25rem', borderRadius: 6, border: `1px solid rgba(139,111,71,0.2)`, background: '#fff', color: MUTED, cursor: 'pointer' }}>Back</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Main booking page ──
  return (
    <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS, color: DARK }}>
      {/* Header with faded hero background */}
      <header style={{
        background: `linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.55)), url(${HERO_IMG}) center/cover`,
        color: '#fff', padding: '2rem 2rem 2.25rem', textAlign: 'center',
      }}>
        <a href="/" style={{ fontFamily: SERIF, color: '#fff', textDecoration: 'none', fontWeight: 500, fontSize: '1.6rem', letterSpacing: '0.02em' }}>{bizName}</a>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0.35rem 0 0', fontWeight: 300, letterSpacing: '0.05em' }}>
          {tenant.tagline || 'Book Your Appointment'}
        </p>
        <div style={{ display: 'flex', gap: '1.75rem', justifyContent: 'center', marginTop: '0.75rem', fontSize: '0.78rem' }}>
          <a href="/" style={{ color: 'rgba(255,255,255,0.6)', textDecoration: 'none', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Home</a>
          <a href="#services" style={{ color: 'rgba(255,255,255,0.6)', textDecoration: 'none', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Services</a>
          <a href="#contact" style={{ color: 'rgba(255,255,255,0.6)', textDecoration: 'none', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Contact</a>
        </div>
      </header>

      {error && (
        <div style={{ maxWidth: 960, margin: '1rem auto 0', padding: '0 1rem' }}>
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '0.75rem 1rem', color: '#991b1b', fontSize: '0.9rem' }}>
            {error}
            <button onClick={() => setError('')} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', color: '#991b1b' }}>✕</button>
          </div>
        </div>
      )}

      <main style={{ maxWidth: 960, margin: '0 auto', padding: '1.25rem 1rem 2rem' }}>

        {/* ── Row 1: Service + Stylist ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>

          {/* 1. Choose Service — grid cards */}
          <Section num={1} title="Choose Service">
            {loadingServices ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.6rem' }}>
                {services.filter((s: any) => s.is_active !== false).map((svc: any) => {
                  const isSel = selectedService?.id === svc.id
                  return (
                    <div
                      key={svc.id}
                      onClick={() => selectService(svc)}
                      style={{
                        padding: '1rem 0.75rem', borderRadius: 8, cursor: 'pointer',
                        textAlign: 'center', transition: 'all 0.15s ease',
                        background: isSel ? ACCENT : '#fff',
                        color: isSel ? '#fff' : DARK,
                        border: isSel ? `2px solid ${ACCENT}` : '1px solid rgba(139,111,71,0.12)',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem' }}>{svc.name}</div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', color: isSel ? 'rgba(255,255,255,0.9)' : ACCENT }}>
                        {svc.price_pence > 0 ? formatPrice(svc.price_pence) : 'POA'}
                      </div>
                      <div style={{ fontSize: '0.72rem', opacity: 0.5, marginTop: '0.15rem' }}>{svc.duration_minutes} min</div>
                    </div>
                  )
                })}
              </div>
            )}
          </Section>

          {/* 2. Choose Staff */}
          <Section num={2} title={`Choose ${tenant.booking_staff_label || 'Staff'}`}>
            {!selectedService ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Select a service first</div>
            ) : loadingStaff ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
            ) : !hasStaff ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Any available {(tenant.booking_staff_label || 'staff').toLowerCase()}</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.6rem' }}>
                {staffList.map((s: any) => {
                  const isSel = selectedStaff?.id === s.id
                  const sName = staffName(s)
                  return (
                    <div
                      key={s.id}
                      onClick={() => selectStaffMember(s)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        padding: '0.65rem 0.85rem', borderRadius: 8, cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        background: isSel ? ACCENT : '#fff',
                        color: isSel ? '#fff' : DARK,
                        border: isSel ? `2px solid ${ACCENT}` : '1px solid rgba(139,111,71,0.12)',
                      }}
                    >
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                        background: isSel ? 'rgba(255,255,255,0.2)' : BG_WARM,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.85rem', fontWeight: 700,
                        color: isSel ? '#fff' : ACCENT,
                      }}>{sName.charAt(0)}</div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{sName}</div>
                    </div>
                  )
                })}
              </div>
            )}
          </Section>
        </div>

        {/* ── Row 2: Date + Time ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>

          {/* 3. Choose Date — calendar */}
          <Section num={3} title="Choose Date">
            {!selectedService || (hasStaff && !selectedStaff) ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>
                {!selectedService ? 'Select a service first' : `Select a ${(tenant.booking_staff_label || 'staff').toLowerCase()} first`}
              </div>
            ) : (
              <Calendar selectedDate={selectedDate} onSelect={selectDate} availableDates={availableDates} />
            )}
          </Section>

          {/* 4. Choose Time — grid */}
          <Section num={4} title="Choose Time">
            {!selectedDate ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Select a date first</div>
            ) : loadingSlots ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
            ) : allSlots.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>No slots available. Try another date.</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem' }}>
                {timeSlots.map((slot: any) => {
                  const timeStr = fmtTime(slot.start_time)
                  const isSel = selectedTime === timeStr && !selectedLegacySlot
                  return (
                    <button
                      key={slot.start_time}
                      onClick={() => selectTime(timeStr)}
                      style={{
                        padding: '0.5rem 0.25rem', borderRadius: 6,
                        border: isSel ? `2px solid ${ACCENT}` : '1px solid rgba(139,111,71,0.15)',
                        background: isSel ? ACCENT : '#fff',
                        color: isSel ? '#fff' : DARK,
                        fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >{timeStr}</button>
                  )
                })}
                {legacySlots.filter((s: any) => s.has_capacity).map((slot: any) => {
                  const t = slot.start_time.slice(0, 5)
                  const isSel = selectedLegacySlot?.id === slot.id
                  return (
                    <button
                      key={slot.id}
                      onClick={() => selectLegacySlot(slot)}
                      style={{
                        padding: '0.5rem 0.25rem', borderRadius: 6,
                        border: isSel ? `2px solid ${ACCENT}` : '1px solid rgba(139,111,71,0.15)',
                        background: isSel ? ACCENT : '#fff',
                        color: isSel ? '#fff' : DARK,
                        fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >{t}</button>
                  )
                })}
              </div>
            )}
          </Section>
        </div>

        {/* ── Row 3: Your Details ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.75rem' }}>
          <Section num={5} title="Your Details">
            {!selectedTime ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Complete the steps above first</div>
            ) : (
              <>
                {/* Summary strip */}
                <div style={{
                  background: BG_WARM, borderRadius: 8, padding: '0.85rem 1rem',
                  marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  border: `1px solid rgba(139,111,71,0.1)`, fontSize: '0.88rem',
                }}>
                  <div>
                    <strong style={{ color: DARK }}>{selectedService.name}</strong>
                    {selectedStaff && <span style={{ color: MUTED }}> with {staffName(selectedStaff)}</span>}
                    <span style={{ color: MUTED }}> &middot; {selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })} at {selectedTime}</span>
                  </div>
                  <strong style={{ color: ACCENT, fontSize: '1rem' }}>{formatPrice(selectedService.price_pence)}</strong>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: DARK, marginBottom: '0.3rem', letterSpacing: '0.02em' }}>Name *</label>
                    <input required value={name} onChange={e => setName(e.target.value)} placeholder="Your full name" style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid rgba(139,111,71,0.2)', fontSize: '0.88rem', boxSizing: 'border-box', fontFamily: SANS, outline: 'none' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: DARK, marginBottom: '0.3rem', letterSpacing: '0.02em' }}>Email *</label>
                    <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid rgba(139,111,71,0.2)', fontSize: '0.88rem', boxSizing: 'border-box', fontFamily: SANS, outline: 'none' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: DARK, marginBottom: '0.3rem', letterSpacing: '0.02em' }}>Phone *</label>
                    <input type="tel" required value={phone} onChange={e => setPhone(e.target.value)} placeholder="07700 900000" style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid rgba(139,111,71,0.2)', fontSize: '0.88rem', boxSizing: 'border-box', fontFamily: SANS, outline: 'none' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: DARK, marginBottom: '0.3rem', letterSpacing: '0.02em' }}>Notes</label>
                    <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Anything we should know?" style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid rgba(139,111,71,0.2)', fontSize: '0.88rem', boxSizing: 'border-box', fontFamily: SANS, outline: 'none' }} />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <button
                      type="submit"
                      disabled={submitting || !name.trim() || !email.trim() || !phone.trim()}
                      style={{
                        width: '100%', padding: '0.9rem', borderRadius: 6, border: 'none',
                        background: ACCENT, color: '#fff', fontWeight: 600, fontSize: '0.95rem',
                        cursor: submitting ? 'wait' : 'pointer',
                        opacity: submitting || !name.trim() || !email.trim() || !phone.trim() ? 0.5 : 1,
                        letterSpacing: '0.05em', textTransform: 'uppercase',
                        fontFamily: SANS, transition: 'opacity 0.2s',
                      }}
                    >{submitting ? 'Processing…' : (selectedService?.price_pence > 0 ? (selectedService.deposit_percentage > 0 || selectedService.deposit_pence > 0 ? 'Pay Deposit & Confirm' : 'Pay & Confirm') : 'Confirm Booking')}</button>
                    {selectedService && (selectedService.deposit_percentage > 0 || selectedService.deposit_pence > 0) && (
                      <p style={{ textAlign: 'center', fontSize: '0.75rem', color: MUTED, margin: '0.6rem 0 0' }}>
                        A deposit of {selectedService.deposit_percentage > 0 ? `${selectedService.deposit_percentage}% (${formatPrice(Math.round(selectedService.price_pence * selectedService.deposit_percentage / 100))})` : formatPrice(selectedService.deposit_pence)} will be taken securely via Stripe.
                      </p>
                    )}
                  </div>
                </form>
              </>
            )}
          </Section>
        </div>

        <div style={{ textAlign: 'center', padding: '2rem 0 0.5rem', fontSize: '0.72rem', color: ACCENT_LIGHT, letterSpacing: '0.03em' }}>
          Powered by NBNE
        </div>
      </main>
    </div>
  )
}

export default function BookPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>}>
      <BookPageInner />
    </Suspense>
  )
}
