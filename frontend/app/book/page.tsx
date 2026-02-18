'use client'

import { useState, useEffect } from 'react'
import { getServices, getBookableStaff, getStaffSlots, getSlots, checkDisclaimer, signDisclaimer, createBooking } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

/* ── Reusable section card ── */
function Section({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb',
      padding: '1.25rem 1.5rem', height: '100%',
    }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#111827', margin: '0 0 1rem' }}>
        {num}. {title}
      </h2>
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
        <button onClick={prevMonth} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', color: '#6b7280', padding: '0.25rem 0.5rem' }}>&lsaquo;</button>
        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#111827' }}>{monthName}</span>
        <button onClick={nextMonth} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', color: '#6b7280', padding: '0.25rem 0.5rem' }}>&rsaquo;</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', textAlign: 'center' }}>
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
          <div key={d} style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 600, padding: '0.25rem 0' }}>{d}</div>
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
                background: isSel ? '#111827' : 'transparent',
                color: isSel ? '#fff' : isPast ? '#d1d5db' : isAvail ? '#111827' : '#d1d5db',
                outline: isToday && !isSel ? '2px solid #2563eb' : 'none',
                outlineOffset: -2,
              }}
            >{day}</button>
          )
        })}
      </div>
    </div>
  )
}

export default function BookPage() {
  const tenant = useTenant()
  const bizName = tenant.business_name || 'Salon-X'

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

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoadingServices(false) })
  }, [])

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
      const res = await getStaffSlots(selectedStaff.user_id, selectedService.id, dateStr)
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
        bookingData.staff_id = selectedStaff.user_id
      }
    }
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
      <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
        <header style={{ background: '#111827', color: '#fff', padding: '1rem 2rem', textAlign: 'center' }}>
          <a href="/" style={{ color: '#fff', textDecoration: 'none', fontWeight: 800, fontSize: '1.3rem' }}>{bizName}</a>
        </header>
        <div style={{ maxWidth: 480, margin: '0 auto', padding: '4rem 1.5rem', textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%', background: '#dcfce7',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.5rem', fontSize: '1.75rem',
          }}>✓</div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#111827', marginBottom: '0.5rem' }}>Booking Confirmed!</h1>
          <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>Reference: <strong>#{confirmed.id}</strong></p>
          <div style={{ background: '#fff', borderRadius: 12, padding: '1.5rem', border: '1px solid #e5e7eb', textAlign: 'left', marginBottom: '1.5rem' }}>
            <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Service</span><strong>{selectedService?.name}</strong></div>
              {selectedStaff && <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Stylist</span><strong>{staffName(selectedStaff)}</strong></div>}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Date</span><strong>{selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}</strong></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Time</span><strong>{selectedTime}</strong></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Price</span><strong>{selectedService && formatPrice(selectedService.price_pence)}</strong></div>
            </div>
          </div>
          {confirmed.checkout_url && (
            <a href={confirmed.checkout_url} style={{ display: 'inline-block', background: '#111827', color: '#fff', padding: '0.75rem 2rem', borderRadius: 8, textDecoration: 'none', fontWeight: 700, marginBottom: '0.75rem' }}>Pay Deposit Now</a>
          )}
          <div><button onClick={resetBooking} style={{ background: 'none', border: 'none', color: '#2563eb', fontSize: '0.9rem', cursor: 'pointer', fontWeight: 600, marginTop: '0.5rem' }}>Book Another Appointment</button></div>
        </div>
      </div>
    )
  }

  // ── Disclaimer overlay ──
  if (showDisclaimer && disclaimerData) {
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
        <header style={{ background: '#111827', color: '#fff', padding: '1rem 2rem' }}>
          <a href="/" style={{ color: '#fff', textDecoration: 'none', fontWeight: 800, fontSize: '1.3rem' }}>{bizName}</a>
        </header>
        <div style={{ maxWidth: 560, margin: '0 auto', padding: '2rem 1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>{disclaimerData.title}</h2>
          <div style={{ background: '#fff', borderRadius: 10, padding: '1.5rem', border: '1px solid #e5e7eb', maxHeight: 320, overflowY: 'auto', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.25rem' }}>
            {disclaimerData.body.split('\n').map((line: string, i: number) => (<p key={i} style={{ marginBottom: '0.5rem' }}>{line}</p>))}
          </div>
          <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '1rem', marginBottom: '1.25rem' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem' }}>By clicking below, you confirm:</p>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem' }}>
              <li>You have read and understood the above terms</li>
              <li>You agree to be bound by these terms</li>
              <li>This agreement is valid for 12 months</li>
            </ul>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleDisclaimerSign} disabled={submitting} style={{ flex: 1, padding: '0.75rem', borderRadius: 8, border: 'none', background: '#111827', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>{submitting ? 'Signing…' : 'I Agree — Continue'}</button>
            <button onClick={() => setShowDisclaimer(false)} style={{ padding: '0.75rem 1.25rem', borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', color: '#6b7280', cursor: 'pointer' }}>Back</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Main booking page — House of Hair layout ──
  return (
    <div style={{ minHeight: '100vh', background: '#f5f0eb' }}>
      {/* Header */}
      <header style={{ background: '#111827', color: '#fff', padding: '2rem 2rem 2.5rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 0.25rem', color: '#fff' }}>{bizName}</h1>
        <p style={{ color: '#9ca3af', fontSize: '0.9rem', margin: 0 }}>
          Professional Hair Salon &middot; Book Your Appointment
        </p>
        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginTop: '0.75rem', fontSize: '0.82rem' }}>
          <a href="/" style={{ color: '#d1d5db', textDecoration: 'none' }}>Home</a>
          <a href="/pricing" style={{ color: '#d1d5db', textDecoration: 'none' }}>Pricing</a>
          <a href="/login" style={{ color: '#d1d5db', textDecoration: 'none' }}>Login</a>
        </div>
      </header>

      {error && (
        <div style={{ maxWidth: 960, margin: '1rem auto 0', padding: '0 1rem' }}>
          <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 8, padding: '0.75rem 1rem', color: '#991b1b', fontSize: '0.9rem' }}>
            {error}
            <button onClick={() => setError('')} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>✕</button>
          </div>
        </div>
      )}

      <main style={{ maxWidth: 960, margin: '0 auto', padding: '1.5rem 1rem 3rem' }}>

        {/* ── Row 1: Service + Stylist ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>

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
                        padding: '1rem 0.75rem', borderRadius: 10, cursor: 'pointer',
                        textAlign: 'center', transition: 'all 0.15s ease',
                        background: isSel ? '#111827' : '#fff',
                        color: isSel ? '#fff' : '#111827',
                        border: isSel ? '2px solid #111827' : '1px solid #e5e7eb',
                      }}
                    >
                      <div style={{ fontSize: '1.25rem', marginBottom: '0.35rem' }}>✂️</div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.2rem' }}>{svc.name}</div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', color: isSel ? '#93c5fd' : '#2563eb' }}>
                        {svc.price_pence > 0 ? formatPrice(svc.price_pence) : 'POA'}
                      </div>
                      <div style={{ fontSize: '0.72rem', opacity: 0.6, marginTop: '0.1rem' }}>{svc.duration_minutes} min</div>
                    </div>
                  )
                })}
              </div>
            )}
          </Section>

          {/* 2. Choose Stylist */}
          <Section num={2} title="Choose Stylist">
            {!selectedService ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Select a service first</div>
            ) : loadingStaff ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>Loading…</div>
            ) : !hasStaff ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Any available stylist</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.6rem' }}>
                {staffList.map((s: any) => {
                  const isSel = selectedStaff?.user_id === s.user_id
                  const sName = staffName(s)
                  return (
                    <div
                      key={s.user_id}
                      onClick={() => selectStaffMember(s)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        padding: '0.65rem 0.85rem', borderRadius: 10, cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        background: isSel ? '#111827' : '#fff',
                        color: isSel ? '#fff' : '#111827',
                        border: isSel ? '2px solid #111827' : '1px solid #e5e7eb',
                      }}
                    >
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                        background: isSel ? 'rgba(255,255,255,0.2)' : '#e0e7ff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.85rem', fontWeight: 700,
                        color: isSel ? '#fff' : '#4338ca',
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>

          {/* 3. Choose Date — calendar */}
          <Section num={3} title="Choose Date">
            {!selectedService || (hasStaff && !selectedStaff) ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>
                {!selectedService ? 'Select a service first' : 'Select a stylist first'}
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
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                {timeSlots.map((slot: any) => {
                  const isSel = selectedTime === slot.start_time && !selectedLegacySlot
                  return (
                    <button
                      key={slot.start_time}
                      onClick={() => selectTime(slot.start_time)}
                      style={{
                        padding: '0.55rem 0.25rem', borderRadius: 8,
                        border: isSel ? '2px solid #111827' : '1px solid #d1d5db',
                        background: isSel ? '#111827' : '#fff',
                        color: isSel ? '#fff' : '#374151',
                        fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
                      }}
                    >{slot.start_time}</button>
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
                        padding: '0.55rem 0.25rem', borderRadius: 8,
                        border: isSel ? '2px solid #111827' : '1px solid #d1d5db',
                        background: isSel ? '#111827' : '#fff',
                        color: isSel ? '#fff' : '#374151',
                        fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
                      }}
                    >{t}</button>
                  )
                })}
              </div>
            )}
          </Section>
        </div>

        {/* ── Row 3: Your Details ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
          <Section num={5} title="Your Details">
            {!selectedTime ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Complete the steps above first</div>
            ) : (
              <>
                {/* Summary strip */}
                <div style={{
                  background: '#f8fafc', borderRadius: 8, padding: '0.75rem 1rem',
                  marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  border: '1px solid #e5e7eb', fontSize: '0.88rem',
                }}>
                  <div>
                    <strong>{selectedService.name}</strong>
                    {selectedStaff && <span style={{ color: '#6b7280' }}> with {staffName(selectedStaff)}</span>}
                    <span style={{ color: '#6b7280' }}> &middot; {selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })} at {selectedTime}</span>
                  </div>
                  <strong style={{ color: '#111827', fontSize: '1rem' }}>{formatPrice(selectedService.price_pence)}</strong>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Name *</label>
                    <input required value={name} onChange={e => setName(e.target.value)} placeholder="Your full name" style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 8, border: '1px solid #d1d5db', fontSize: '0.88rem', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Email *</label>
                    <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 8, border: '1px solid #d1d5db', fontSize: '0.88rem', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Phone *</label>
                    <input type="tel" required value={phone} onChange={e => setPhone(e.target.value)} placeholder="07700 900000" style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 8, border: '1px solid #d1d5db', fontSize: '0.88rem', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Notes</label>
                    <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Anything we should know?" style={{ width: '100%', padding: '0.6rem 0.75rem', borderRadius: 8, border: '1px solid #d1d5db', fontSize: '0.88rem', boxSizing: 'border-box' }} />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <button
                      type="submit"
                      disabled={submitting || !name.trim() || !email.trim() || !phone.trim()}
                      style={{
                        width: '100%', padding: '0.85rem', borderRadius: 10, border: 'none',
                        background: '#111827', color: '#fff', fontWeight: 700, fontSize: '1rem',
                        cursor: submitting ? 'wait' : 'pointer',
                        opacity: submitting || !name.trim() || !email.trim() || !phone.trim() ? 0.5 : 1,
                      }}
                    >{submitting ? 'Booking…' : 'Confirm Booking'}</button>
                    {selectedService && (selectedService.deposit_percentage > 0 || selectedService.deposit_pence > 0) && (
                      <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#6b7280', margin: '0.5rem 0 0' }}>
                        A deposit of {selectedService.deposit_percentage > 0 ? `${selectedService.deposit_percentage}%` : formatPrice(selectedService.deposit_pence)} will be requested after booking.
                      </p>
                    )}
                  </div>
                </form>
              </>
            )}
          </Section>
        </div>

        <div style={{ textAlign: 'center', padding: '2rem 0 0.5rem', fontSize: '0.75rem', color: '#9ca3af' }}>
          Powered by NBNE Business Platform
        </div>
      </main>
    </div>
  )
}
