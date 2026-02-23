'use client'

import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { getRestaurantAvailability, getRestaurantAvailableDates, createBooking, setDemoTenant } from '@/lib/api'

const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF8F5'
const BG_WARM = '#F5F0EB'

export default function RestaurantBookingFlow() {
  const tenant = useTenant()
  const searchParams = useSearchParams()
  const demoSlug = searchParams.get('demo') || ''
  const accent = tenant.colour_primary || '#059669'
  const accentLight = accent + '80'
  const bizName = tenant.business_name || 'Restaurant'

  const [step, setStep] = useState(1) // 1=party+date, 2=time, 3=details, 4=confirmed
  const [partySize, setPartySize] = useState(2)
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [selectedDate, setSelectedDate] = useState('')
  const [windows, setWindows] = useState<any[]>([])
  const [selectedSlot, setSelectedSlot] = useState<any>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState<any>(null)

  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
  }, [demoSlug])

  // Fetch available dates immediately on mount and when party size changes
  useEffect(() => {
    setLoading(true)
    getRestaurantAvailableDates(partySize).then(res => {
      setAvailableDates(res.data?.dates || [])
      setLoading(false)
    })
  }, [partySize])

  // Fetch time slots when date selected
  useEffect(() => {
    if (selectedDate) {
      setLoading(true)
      getRestaurantAvailability(selectedDate, partySize).then(res => {
        setWindows(res.data?.windows || [])
        setLoading(false)
      })
    }
  }, [selectedDate, partySize])

  // Format selected date nicely
  const formattedDate = useMemo(() => {
    if (!selectedDate) return ''
    return new Date(selectedDate + 'T00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
  }, [selectedDate])

  async function handleSubmit() {
    if (!name || !email || !phone) {
      setError('Please fill in all required fields')
      return
    }
    setSubmitting(true)
    setError('')

    const bookingData = {
      client_name: name,
      client_email: email,
      client_phone: phone,
      notes: `Party of ${partySize}. ${selectedSlot?.start_time || ''} - ${selectedSlot?.end_time || ''}. ${notes}`,
      date: selectedDate,
      start_time: selectedSlot?.start_time,
      party_size: partySize,
    }

    const res = await createBooking(bookingData)
    setSubmitting(false)
    if (res.data?.checkout_url) {
      window.location.href = res.data.checkout_url
      return
    }
    if (res.error) {
      setError(res.error)
    } else {
      setConfirmed(res.data)
      setStep(4)
    }
  }

  // Calendar component (inline)
  function Calendar() {
    const today = new Date()
    const [viewYear, setViewYear] = useState(today.getFullYear())
    const [viewMonth, setViewMonth] = useState(today.getMonth())
    const firstDay = new Date(viewYear, viewMonth, 1).getDay()
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
    const monthName = new Date(viewYear, viewMonth).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
    const todayStr = today.toISOString().split('T')[0]
    const availSet = new Set(availableDates)

    // Start week on Monday
    const adjustedFirst = firstDay === 0 ? 6 : firstDay - 1
    const cells: (number | null)[] = []
    for (let i = 0; i < adjustedFirst; i++) cells.push(null)
    for (let d = 1; d <= daysInMonth; d++) cells.push(d)

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <button onClick={() => viewMonth === 0 ? (setViewMonth(11), setViewYear(viewYear - 1)) : setViewMonth(viewMonth - 1)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: MUTED, padding: '0.25rem 0.5rem' }}>&lsaquo;</button>
          <span style={{ fontFamily: SERIF, fontWeight: 500, fontSize: '0.9rem', color: DARK }}>{monthName}</span>
          <button onClick={() => viewMonth === 11 ? (setViewMonth(0), setViewYear(viewYear + 1)) : setViewMonth(viewMonth + 1)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: MUTED, padding: '0.25rem 0.5rem' }}>&rsaquo;</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '1px', textAlign: 'center' }}>
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <div key={d} style={{ fontSize: '0.68rem', color: MUTED, fontWeight: 600, padding: '0.3rem 0', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{d}</div>
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
              <button key={dateStr}
                onClick={() => { if (clickable) { setSelectedDate(dateStr); setSelectedSlot(null); setStep(2) } }}
                disabled={!clickable}
                style={{
                  width: 34, height: 34, borderRadius: '50%', border: 'none', margin: '1px auto',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.8rem', fontWeight: isSel ? 700 : isToday ? 600 : 400,
                  cursor: clickable ? 'pointer' : 'default',
                  background: isSel ? accent : isToday && !isPast ? accent + '15' : 'transparent',
                  color: isSel ? '#fff' : isPast ? '#d1d5db' : isAvail ? DARK : '#d1d5db',
                  transition: 'all 0.15s ease',
                  outline: isToday && !isSel ? `2px solid ${accent}40` : 'none',
                }}
              >{day}</button>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS }}>
      {/* Header */}
      <header style={{ background: accent, color: '#fff', padding: '1.25rem 1rem', textAlign: 'center' }}>
        <h1 style={{ fontFamily: SERIF, fontSize: '1.4rem', fontWeight: 500, margin: 0 }}>{bizName}</h1>
        <p style={{ fontSize: '0.8rem', opacity: 0.85, margin: '0.2rem 0 0' }}>Reserve a Table</p>
      </header>

      <main style={{ maxWidth: 520, margin: '0 auto', padding: '1rem 0.75rem' }}>
        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '0.6rem 0.85rem', marginBottom: '0.75rem', color: '#dc2626', fontSize: '0.82rem' }}>
            {error}
          </div>
        )}

        {step === 4 && confirmed ? (
          <div style={{ background: '#fff', borderRadius: 12, padding: '2rem', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: accent + '15', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
              <span style={{ fontSize: '1.5rem', color: accent }}>✓</span>
            </div>
            <h2 style={{ fontFamily: SERIF, fontSize: '1.3rem', color: DARK, marginBottom: '0.75rem' }}>Reservation Confirmed</h2>
            <div style={{ background: BG_WARM, borderRadius: 8, padding: '1rem', display: 'inline-block', textAlign: 'left', fontSize: '0.85rem', color: DARK, lineHeight: 1.8 }}>
              <div><strong>Party:</strong> {partySize} {partySize === 1 ? 'guest' : 'guests'}</div>
              <div><strong>Date:</strong> {formattedDate}</div>
              <div><strong>Time:</strong> {selectedSlot?.start_time}</div>
            </div>
            <p style={{ color: MUTED, fontSize: '0.82rem', marginTop: '1rem' }}>
              A confirmation has been sent to <strong>{email}</strong>
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.25rem' }}>
              <button onClick={() => { setStep(1); setSelectedDate(''); setSelectedSlot(null); setName(''); setEmail(''); setPhone(''); setNotes(''); setConfirmed(null) }}
                style={{ padding: '0.6rem 1.25rem', borderRadius: 8, background: accent, color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem', fontFamily: SANS }}>
                Book Another Table
              </button>
              <a href="/" style={{ padding: '0.6rem 1.25rem', borderRadius: 8, background: '#f3f4f6', color: DARK, textDecoration: 'none', fontWeight: 500, fontSize: '0.85rem', fontFamily: SANS, display: 'inline-flex', alignItems: 'center' }}>
                Back to Website
              </a>
            </div>
          </div>
        ) : (
          <div style={{ background: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            {/* Party size — always visible, compact inline bar */}
            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                <span style={{ fontFamily: SERIF, fontSize: '0.95rem', fontWeight: 500, color: DARK }}>Guests</span>
                {selectedDate && (
                  <span style={{ fontSize: '0.75rem', color: MUTED }}>
                    {formattedDate}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map(n => (
                  <button key={n} onClick={() => { setPartySize(n); setSelectedDate(''); setSelectedSlot(null); setStep(1) }}
                    style={{
                      flex: 1, padding: '0.5rem 0', borderRadius: 6,
                      border: 'none',
                      background: partySize === n ? accent : '#f3f4f6',
                      color: partySize === n ? '#fff' : DARK,
                      cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem',
                      transition: 'all 0.15s ease',
                    }}
                  >{n}{n === 8 ? '+' : ''}</button>
                ))}
              </div>
            </div>

            {/* Calendar — always visible */}
            <div style={{ padding: '1rem 1.25rem', borderBottom: selectedDate ? '1px solid #f3f4f6' : 'none' }}>
              {loading && availableDates.length === 0 ? (
                <p style={{ color: MUTED, fontSize: '0.85rem', textAlign: 'center', padding: '1rem 0' }}>Loading availability...</p>
              ) : (
                <Calendar />
              )}
            </div>

            {/* Time slots — shown after date selection */}
            {step >= 2 && selectedDate && (
              <div style={{ padding: '1rem 1.25rem', borderBottom: selectedSlot ? '1px solid #f3f4f6' : 'none' }}>
                <div style={{ fontFamily: SERIF, fontSize: '0.9rem', fontWeight: 500, color: DARK, marginBottom: '0.6rem' }}>
                  Available Times
                </div>
                {loading ? (
                  <p style={{ color: MUTED, fontSize: '0.82rem' }}>Loading times...</p>
                ) : windows.length === 0 ? (
                  <p style={{ color: MUTED, fontSize: '0.82rem' }}>No availability on this date. Try another day.</p>
                ) : (
                  <div>
                    {windows.map((w: any) => {
                      const availSlots = w.slots?.filter((s: any) => s.has_capacity) || []
                      if (availSlots.length === 0) return null
                      return (
                        <div key={w.id} style={{ marginBottom: '0.75rem' }}>
                          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: MUTED, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
                            {w.name}
                          </div>
                          <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                            {availSlots.map((slot: any) => (
                              <button key={slot.start_time}
                                onClick={() => { setSelectedSlot(slot); setStep(3) }}
                                style={{
                                  padding: '0.45rem 0.7rem', borderRadius: 6,
                                  border: `1px solid ${selectedSlot?.start_time === slot.start_time ? accent : '#e5e7eb'}`,
                                  background: selectedSlot?.start_time === slot.start_time ? accent : '#fff',
                                  color: selectedSlot?.start_time === slot.start_time ? '#fff' : DARK,
                                  cursor: 'pointer', fontSize: '0.8rem', fontWeight: 500,
                                  transition: 'all 0.15s ease',
                                }}
                              >{slot.start_time}</button>
                            ))}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Details form — shown after time selection */}
            {step >= 3 && selectedSlot && (
              <div style={{ padding: '1rem 1.25rem' }}>
                {/* Reservation summary bar */}
                <div style={{ background: accent + '10', borderRadius: 8, padding: '0.65rem 0.85rem', marginBottom: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                  <span style={{ color: DARK }}>
                    <strong>{partySize}</strong> {partySize === 1 ? 'guest' : 'guests'} · <strong>{formattedDate}</strong> · <strong>{selectedSlot.start_time}</strong>
                  </span>
                  <button onClick={() => { setStep(1); setSelectedDate(''); setSelectedSlot(null) }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: accent, fontSize: '0.75rem', fontWeight: 600 }}>
                    Change
                  </button>
                </div>

                <div style={{ fontFamily: SERIF, fontSize: '0.9rem', fontWeight: 500, color: DARK, marginBottom: '0.6rem' }}>
                  Your Details
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  <input placeholder="Full Name *" value={name} onChange={e => setName(e.target.value)}
                    style={{ padding: '0.6rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.85rem', fontFamily: SANS }} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
                    <input placeholder="Email *" type="email" value={email} onChange={e => setEmail(e.target.value)}
                      style={{ padding: '0.6rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.85rem', fontFamily: SANS }} />
                    <input placeholder="Phone *" type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                      style={{ padding: '0.6rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.85rem', fontFamily: SANS }} />
                  </div>
                  <textarea placeholder="Special requests or dietary requirements" value={notes} onChange={e => setNotes(e.target.value)} rows={2}
                    style={{ padding: '0.6rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.85rem', fontFamily: SANS, resize: 'vertical' }} />
                </div>

                <button onClick={handleSubmit} disabled={submitting}
                  style={{
                    width: '100%', marginTop: '0.85rem', padding: '0.8rem', borderRadius: 8,
                    background: accent, color: '#fff', border: 'none', cursor: submitting ? 'wait' : 'pointer',
                    fontWeight: 600, fontSize: '0.9rem', fontFamily: SANS, opacity: submitting ? 0.7 : 1,
                    transition: 'opacity 0.15s ease',
                  }}
                >{submitting ? 'Reserving...' : 'Confirm Reservation'}</button>
              </div>
            )}
          </div>
        )}

        <div style={{ textAlign: 'center', padding: '1.5rem 0 0.5rem', fontSize: '0.72rem', color: accentLight, letterSpacing: '0.03em' }}>
          Powered by NBNE
        </div>
      </main>
    </div>
  )
}
