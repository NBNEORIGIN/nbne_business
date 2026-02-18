'use client'

import { useState, useEffect, useRef } from 'react'
import { getServices, getBookableStaff, getStaffSlots, getSlots, checkDisclaimer, signDisclaimer, createBooking } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

function SectionHeader({ num, title, done, active }: { num: number; title: string; done: boolean; active: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.85rem', fontWeight: 700,
        background: done ? '#111827' : active ? '#2563eb' : '#e5e7eb',
        color: done || active ? '#fff' : '#9ca3af',
      }}>
        {done ? '✓' : num}
      </div>
      <h2 style={{
        fontSize: '1.1rem', fontWeight: 700, margin: 0,
        color: active || done ? '#111827' : '#9ca3af',
      }}>{title}</h2>
    </div>
  )
}

export default function BookPage() {
  const tenant = useTenant()
  const bizName = tenant.business_name || 'Salon-X'

  // Data
  const [services, setServices] = useState<any[]>([])
  const [staffList, setStaffList] = useState<any[]>([])
  const [timeSlots, setTimeSlots] = useState<any[]>([])
  const [legacySlots, setLegacySlots] = useState<any[]>([])

  // Selections
  const [selectedService, setSelectedService] = useState<any>(null)
  const [selectedStaff, setSelectedStaff] = useState<any>(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('')
  const [selectedLegacySlot, setSelectedLegacySlot] = useState<any>(null)

  // Customer details
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')

  // UI state
  const [loadingServices, setLoadingServices] = useState(true)
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [disclaimerData, setDisclaimerData] = useState<any>(null)
  const [showDisclaimer, setShowDisclaimer] = useState(false)
  const [confirmed, setConfirmed] = useState<any>(null)

  // Refs for smooth scrolling
  const staffRef = useRef<HTMLDivElement>(null)
  const dateRef = useRef<HTMLDivElement>(null)
  const detailsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoadingServices(false) })
  }, [])

  function scrollTo(ref: React.RefObject<HTMLDivElement | null>) {
    setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
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
    const staff = res.data || []
    setStaffList(staff)
    setLoadingStaff(false)
    if (staff.length > 0) {
      scrollTo(staffRef)
    } else {
      scrollTo(dateRef)
    }
  }

  async function selectStaffMember(s: any) {
    setSelectedStaff(s)
    setSelectedDate('')
    setSelectedTime('')
    setTimeSlots([])
    setLegacySlots([])
    setSelectedLegacySlot(null)
    scrollTo(dateRef)
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
    scrollTo(detailsRef)
  }

  function selectLegacySlot(slot: any) {
    setSelectedLegacySlot(slot)
    setSelectedTime(slot.start_time.slice(0, 5))
    setError('')
    scrollTo(detailsRef)
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

  // Generate next 14 days
  const dates: string[] = []
  for (let i = 0; i < 14; i++) {
    const d = new Date(); d.setDate(d.getDate() + i)
    dates.push(d.toISOString().split('T')[0])
  }

  const hasStaff = staffList.length > 0
  const canShowDate = selectedService && (!hasStaff || selectedStaff)
  const canShowDetails = selectedService && selectedTime
  const allSlots = [...timeSlots, ...legacySlots.filter((s: any) => s.has_capacity)]

  // ── Confirmation overlay ──
  if (confirmed) {
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
        <header style={{ background: '#111827', color: '#fff', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="/" style={{ color: '#fff', textDecoration: 'none', fontWeight: 800, fontSize: '1.3rem' }}>{bizName}</a>
        </header>
        <div style={{ maxWidth: 480, margin: '0 auto', padding: '4rem 1.5rem', textAlign: 'center' }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%', background: '#dcfce7',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.5rem', fontSize: '1.75rem',
          }}>✓</div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#111827', marginBottom: '0.5rem' }}>Booking Confirmed!</h1>
          <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
            Reference: <strong>#{confirmed.id}</strong>
          </p>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '1.5rem', border: '1px solid #e5e7eb',
            textAlign: 'left', marginBottom: '1.5rem',
          }}>
            <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>Service</span>
                <strong>{selectedService?.name}</strong>
              </div>
              {selectedStaff && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#6b7280' }}>Stylist</span>
                  <strong>{selectedStaff.display_name}</strong>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>Date</span>
                <strong>{selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>Time</span>
                <strong>{selectedTime}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#6b7280' }}>Price</span>
                <strong>{selectedService && formatPrice(selectedService.price_pence)}</strong>
              </div>
            </div>
          </div>
          {confirmed.checkout_url && (
            <a href={confirmed.checkout_url} style={{
              display: 'inline-block', background: '#111827', color: '#fff',
              padding: '0.75rem 2rem', borderRadius: 8, textDecoration: 'none',
              fontWeight: 700, fontSize: '1rem', marginBottom: '0.75rem',
            }}>Pay Deposit Now</a>
          )}
          <div>
            <button onClick={resetBooking} style={{
              background: 'none', border: 'none', color: '#2563eb',
              fontSize: '0.9rem', cursor: 'pointer', fontWeight: 600, marginTop: '0.5rem',
            }}>Book Another Appointment</button>
          </div>
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
          <div style={{
            background: '#fff', borderRadius: 10, padding: '1.5rem', border: '1px solid #e5e7eb',
            maxHeight: 320, overflowY: 'auto', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.25rem',
          }}>
            {disclaimerData.body.split('\n').map((line: string, i: number) => (
              <p key={i} style={{ marginBottom: '0.5rem' }}>{line}</p>
            ))}
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
            <button onClick={handleDisclaimerSign} disabled={submitting} style={{
              flex: 1, padding: '0.75rem', borderRadius: 8, border: 'none',
              background: '#111827', color: '#fff', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer',
            }}>{submitting ? 'Signing…' : 'I Agree — Continue'}</button>
            <button onClick={() => setShowDisclaimer(false)} style={{
              padding: '0.75rem 1.25rem', borderRadius: 8, border: '1px solid #e5e7eb',
              background: '#fff', color: '#6b7280', cursor: 'pointer', fontSize: '0.9rem',
            }}>Back</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Main single-page booking ──
  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Header */}
      <header style={{
        background: '#111827', color: '#fff', padding: '1rem 2rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <a href="/" style={{ color: '#fff', textDecoration: 'none', fontWeight: 800, fontSize: '1.3rem' }}>{bizName}</a>
        <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', fontSize: '0.85rem' }}>
          <a href="/" style={{ color: '#d1d5db', textDecoration: 'none' }}>Home</a>
          <a href="/pricing" style={{ color: '#d1d5db', textDecoration: 'none' }}>Pricing</a>
          <a href="/login" style={{ color: '#d1d5db', textDecoration: 'none' }}>Login</a>
        </div>
      </header>

      {/* Title bar */}
      <div style={{ background: '#fff', borderBottom: '1px solid #e5e7eb', padding: '1.5rem 2rem' }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#111827', margin: 0 }}>Book an Appointment</h1>
          <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: '0.25rem 0 0' }}>
            Choose your service, pick a time, and you&rsquo;re sorted.
          </p>
        </div>
      </div>

      <main style={{ maxWidth: 720, margin: '0 auto', padding: '1.5rem 1rem 4rem' }}>
        {error && (
          <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', color: '#991b1b', fontSize: '0.9rem' }}>
            {error}
            <button onClick={() => setError('')} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem' }}>✕</button>
          </div>
        )}

        {/* ── 1. Service ── */}
        <section style={{ marginBottom: '2rem' }}>
          <SectionHeader num={1} title="Choose a Service" done={!!selectedService} active={!selectedService} />
          {loadingServices ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>Loading services…</div>
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {services.filter((s: any) => s.is_active !== false).map((svc: any) => {
                const isSelected = selectedService?.id === svc.id
                return (
                  <div
                    key={svc.id}
                    onClick={() => selectService(svc)}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.85rem 1rem', borderRadius: 10, cursor: 'pointer',
                      background: isSelected ? '#111827' : '#fff',
                      color: isSelected ? '#fff' : '#111827',
                      border: isSelected ? '2px solid #111827' : '1px solid #e5e7eb',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{svc.name}</div>
                      {svc.description && (
                        <div style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: '0.15rem' }}>{svc.description}</div>
                      )}
                      <div style={{ fontSize: '0.78rem', opacity: 0.6, marginTop: '0.15rem' }}>{svc.duration_minutes} min</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '1rem' }}>
                      <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>
                        {svc.price_pence > 0 ? formatPrice(svc.price_pence) : 'POA'}
                      </div>
                      {(svc.deposit_percentage > 0 || svc.deposit_pence > 0) && (
                        <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>
                          Deposit: {svc.deposit_percentage > 0 ? `${svc.deposit_percentage}%` : formatPrice(svc.deposit_pence)}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* ── 2. Stylist ── */}
        {selectedService && hasStaff && (
          <section ref={staffRef} style={{ marginBottom: '2rem' }}>
            <SectionHeader num={2} title="Choose Your Stylist" done={!!selectedStaff} active={!selectedStaff} />
            {loadingStaff ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: '#9ca3af' }}>Loading stylists…</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '0.6rem' }}>
                {staffList.map((s: any) => {
                  const isSelected = selectedStaff?.user_id === s.user_id
                  return (
                    <div
                      key={s.user_id}
                      onClick={() => selectStaffMember(s)}
                      style={{
                        textAlign: 'center', padding: '1.25rem 0.75rem', borderRadius: 10,
                        cursor: 'pointer', transition: 'all 0.15s ease',
                        background: isSelected ? '#111827' : '#fff',
                        color: isSelected ? '#fff' : '#111827',
                        border: isSelected ? '2px solid #111827' : '1px solid #e5e7eb',
                      }}
                    >
                      <div style={{
                        width: 48, height: 48, borderRadius: '50%',
                        background: isSelected ? 'rgba(255,255,255,0.2)' : '#f0f9ff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 0.5rem', fontSize: '1.1rem', fontWeight: 700,
                        color: isSelected ? '#fff' : '#2563eb',
                      }}>
                        {s.display_name?.charAt(0) || '?'}
                      </div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{s.display_name}</div>
                    </div>
                  )
                })}
              </div>
            )}
          </section>
        )}

        {/* ── 3. Date & Time ── */}
        {canShowDate && (
          <section ref={dateRef} style={{ marginBottom: '2rem' }}>
            <SectionHeader
              num={hasStaff ? 3 : 2}
              title={selectedStaff ? `Pick a Date with ${selectedStaff.display_name}` : 'Pick a Date & Time'}
              done={!!selectedTime}
              active={!selectedTime}
            />

            {/* Date pills */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {dates.map(d => {
                  const isSelected = selectedDate === d
                  const dateObj = new Date(d + 'T00:00:00')
                  const isToday = d === dates[0]
                  return (
                    <button
                      key={d}
                      onClick={() => selectDate(d)}
                      style={{
                        padding: '0.5rem 0.75rem', borderRadius: 8, border: 'none',
                        cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                        background: isSelected ? '#111827' : '#fff',
                        color: isSelected ? '#fff' : '#374151',
                        boxShadow: isSelected ? 'none' : '0 1px 2px rgba(0,0,0,0.06)',
                        minWidth: 80, textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '0.7rem', opacity: 0.7 }}>
                        {isToday ? 'Today' : dateObj.toLocaleDateString('en-GB', { weekday: 'short' })}
                      </div>
                      <div>{dateObj.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Time slots */}
            {selectedDate && (
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>Available times</div>
                {loadingSlots ? (
                  <div style={{ padding: '1rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>Loading times…</div>
                ) : allSlots.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))', gap: '0.4rem' }}>
                    {timeSlots.map((slot: any) => {
                      const isSelected = selectedTime === slot.start_time && !selectedLegacySlot
                      return (
                        <button
                          key={slot.start_time}
                          onClick={() => selectTime(slot.start_time)}
                          style={{
                            padding: '0.55rem 0.5rem', borderRadius: 8, border: 'none',
                            cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                            background: isSelected ? '#111827' : '#fff',
                            color: isSelected ? '#fff' : '#374151',
                            boxShadow: isSelected ? 'none' : '0 1px 2px rgba(0,0,0,0.06)',
                          }}
                        >{slot.start_time}</button>
                      )
                    })}
                    {legacySlots.filter((s: any) => s.has_capacity).map((slot: any) => {
                      const t = slot.start_time.slice(0, 5)
                      const isSelected = selectedLegacySlot?.id === slot.id
                      return (
                        <button
                          key={slot.id}
                          onClick={() => selectLegacySlot(slot)}
                          style={{
                            padding: '0.55rem 0.5rem', borderRadius: 8, border: 'none',
                            cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                            background: isSelected ? '#111827' : '#fff',
                            color: isSelected ? '#fff' : '#374151',
                            boxShadow: isSelected ? 'none' : '0 1px 2px rgba(0,0,0,0.06)',
                          }}
                        >{t}</button>
                      )
                    })}
                  </div>
                ) : (
                  <div style={{ padding: '1rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem', background: '#fff', borderRadius: 8 }}>
                    No slots available on this date. Try another day.
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* ── 4. Your Details ── */}
        {canShowDetails && (
          <section ref={detailsRef} style={{ marginBottom: '2rem' }}>
            <SectionHeader num={hasStaff ? 4 : 3} title="Your Details" done={false} active={true} />

            {/* Booking summary */}
            <div style={{
              background: '#fff', borderRadius: 10, padding: '1rem 1.25rem',
              border: '1px solid #e5e7eb', marginBottom: '1.25rem',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div style={{ fontSize: '0.88rem' }}>
                <strong>{selectedService.name}</strong>
                {selectedStaff && <span style={{ color: '#6b7280' }}> with {selectedStaff.display_name}</span>}
                <div style={{ color: '#6b7280', fontSize: '0.82rem', marginTop: '0.15rem' }}>
                  {selectedDate && new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })} at {selectedTime}
                </div>
              </div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#111827' }}>
                {formatPrice(selectedService.price_pence)}
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '0.85rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>Full Name</label>
                <input
                  required value={name} onChange={e => setName(e.target.value)}
                  placeholder="e.g. Sarah Jones"
                  style={{
                    width: '100%', padding: '0.65rem 0.85rem', borderRadius: 8,
                    border: '1px solid #d1d5db', fontSize: '0.9rem', outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>Email</label>
                <input
                  type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="sarah@example.com"
                  style={{
                    width: '100%', padding: '0.65rem 0.85rem', borderRadius: 8,
                    border: '1px solid #d1d5db', fontSize: '0.9rem', outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>Phone</label>
                <input
                  type="tel" required value={phone} onChange={e => setPhone(e.target.value)}
                  placeholder="07700 900000"
                  style={{
                    width: '100%', padding: '0.65rem 0.85rem', borderRadius: 8,
                    border: '1px solid #d1d5db', fontSize: '0.9rem', outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' }}>Notes (optional)</label>
                <textarea
                  rows={2} value={notes} onChange={e => setNotes(e.target.value)}
                  placeholder="Anything we should know?"
                  style={{
                    width: '100%', padding: '0.65rem 0.85rem', borderRadius: 8,
                    border: '1px solid #d1d5db', fontSize: '0.9rem', outline: 'none',
                    resize: 'vertical', boxSizing: 'border-box',
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={submitting || !name.trim() || !email.trim() || !phone.trim()}
                style={{
                  width: '100%', padding: '0.85rem', borderRadius: 10, border: 'none',
                  background: '#111827', color: '#fff', fontWeight: 700, fontSize: '1rem',
                  cursor: submitting ? 'wait' : 'pointer',
                  opacity: submitting || !name.trim() || !email.trim() || !phone.trim() ? 0.5 : 1,
                  marginTop: '0.25rem',
                }}
              >
                {submitting ? 'Booking…' : 'Confirm Booking'}
              </button>
              {selectedService && (selectedService.deposit_percentage > 0 || selectedService.deposit_pence > 0) && (
                <p style={{ textAlign: 'center', fontSize: '0.78rem', color: '#6b7280', margin: 0 }}>
                  A deposit of {selectedService.deposit_percentage > 0 ? `${selectedService.deposit_percentage}%` : formatPrice(selectedService.deposit_pence)} will be requested after booking.
                </p>
              )}
            </form>
          </section>
        )}

        {/* Powered by footer */}
        <div style={{ textAlign: 'center', padding: '2rem 0 1rem', fontSize: '0.75rem', color: '#9ca3af' }}>
          Powered by NBNE Business Platform
        </div>
      </main>
    </div>
  )
}
