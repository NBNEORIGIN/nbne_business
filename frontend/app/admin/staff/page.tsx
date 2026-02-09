'use client'

import React, { useEffect, useState } from 'react'
import { getStaffList, getShifts, getLeaveRequests, getTrainingRecords, createStaff, updateStaff, deleteStaff, createShift, updateShift, deleteShift, getWorkingHours, bulkSetWorkingHours, getTimesheets, updateTimesheet, generateTimesheets } from '@/lib/api'

interface StaffForm {
  first_name: string
  last_name: string
  email: string
  phone: string
  role: string
}

const emptyForm: StaffForm = { first_name: '', last_name: '', email: '', phone: '', role: 'staff' }

export default function AdminStaffPage() {
  const [tab, setTab] = useState<'profiles' | 'hours' | 'timesheets' | 'shifts' | 'leave' | 'training'>('profiles')
  const [staff, setStaff] = useState<any[]>([])
  const [shifts, setShifts] = useState<any[]>([])
  const [leave, setLeave] = useState<any[]>([])
  const [training, setTraining] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const [showAddModal, setShowAddModal] = useState(false)
  const [editingStaff, setEditingStaff] = useState<any | null>(null)
  const [form, setForm] = useState<StaffForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [createdCreds, setCreatedCreds] = useState<{ name: string; username: string; email: string; temp_password: string } | null>(null)

  // Shift modal state
  const [showShiftModal, setShowShiftModal] = useState(false)
  const [editingShift, setEditingShift] = useState<any | null>(null)
  const [shiftSegments, setShiftSegments] = useState<{ start_time: string; end_time: string }[]>([{ start_time: '09:00', end_time: '17:00' }])
  const [shiftForm, setShiftForm] = useState({ staff: '', date: '', location: '', notes: '', is_published: true })
  const [shiftSaving, setShiftSaving] = useState(false)
  const [shiftError, setShiftError] = useState('')

  // Working Hours state
  const [workingHours, setWorkingHours] = useState<any[]>([])
  const [whStaffId, setWhStaffId] = useState<number | null>(null)
  const [whGrid, setWhGrid] = useState<Record<number, { start_time: string; end_time: string; break_minutes: number }[]>>({})
  const [whSaving, setWhSaving] = useState(false)

  // Timesheet state
  const [timesheets, setTimesheets] = useState<any[]>([])
  const [tsDateFrom, setTsDateFrom] = useState('')
  const [tsDateTo, setTsDateTo] = useState('')
  const [tsStaffFilter, setTsStaffFilter] = useState('')
  const [tsGenerating, setTsGenerating] = useState(false)
  const [editingTs, setEditingTs] = useState<any | null>(null)
  const [tsForm, setTsForm] = useState({ actual_start: '', actual_end: '', actual_break_minutes: 0, status: '', notes: '' })
  const [tsSaving, setTsSaving] = useState(false)

  const loadData = () => {
    setLoading(true)
    Promise.all([getStaffList(), getShifts(), getLeaveRequests(), getTrainingRecords()]).then(([s, sh, lv, tr]) => {
      setStaff(s.data || [])
      setShifts(sh.data || [])
      setLeave(lv.data || [])
      setTraining(tr.data || [])
      setLoading(false)
    })
  }

  useEffect(() => { loadData() }, [])

  const openAdd = () => {
    setForm(emptyForm)
    setError('')
    setEditingStaff(null)
    setShowAddModal(true)
  }

  const openEdit = (s: any) => {
    const nameParts = (s.display_name || '').split(' ')
    setForm({
      first_name: nameParts[0] || '',
      last_name: nameParts.slice(1).join(' ') || '',
      email: s.email || '',
      phone: s.phone || '',
      role: s.role || 'staff',
    })
    setError('')
    setEditingStaff(s)
    setShowAddModal(true)
  }

  const handleAuthError = (res: { error: string | null; status: number }) => {
    if (res.status === 401 || res.error?.toLowerCase().includes('inactive') || res.error?.toLowerCase().includes('expired')) {
      window.location.href = '/login'
      return true
    }
    return false
  }

  const handleSave = async () => {
    setError('')
    if (!form.first_name.trim() || !form.last_name.trim()) { setError('First and last name are required.'); return }
    if (!form.email.trim()) { setError('Email is required.'); return }
    setSaving(true)
    if (editingStaff) {
      const res = await updateStaff(editingStaff.id, form)
      if (res.error) { if (handleAuthError(res)) return; setError(res.error); setSaving(false); return }
    } else {
      const res = await createStaff(form)
      if (res.error) { if (handleAuthError(res)) return; setError(res.error); setSaving(false); return }
      // Show temp credentials to admin
      if (res.data) {
        setCreatedCreds({
          name: `${form.first_name} ${form.last_name}`,
          username: res.data.username || form.email.split('@')[0],
          email: form.email,
          temp_password: res.data.temp_password || '',
        })
      }
    }
    setSaving(false)
    setShowAddModal(false)
    loadData()
  }

  const handleDelete = async (s: any) => {
    if (!confirm(`Deactivate ${s.display_name}? They will no longer be able to log in.`)) return
    const res = await deleteStaff(s.id)
    if (res.error) { alert(res.error); return }
    loadData()
  }

  // --- Shift handlers ---
  const today = new Date().toISOString().split('T')[0]

  const openAddShift = () => {
    setShiftForm({ staff: staff.length > 0 ? String(staff[0].id) : '', date: today, location: '', notes: '', is_published: true })
    setShiftSegments([{ start_time: '09:00', end_time: '17:00' }])
    setShiftError('')
    setEditingShift(null)
    setShowShiftModal(true)
  }

  const openEditShift = (s: any) => {
    setShiftForm({ staff: String(s.staff), date: s.date, location: s.location || '', notes: s.notes || '', is_published: s.is_published })
    setShiftSegments([{ start_time: s.start_time?.slice(0, 5) || '09:00', end_time: s.end_time?.slice(0, 5) || '17:00' }])
    setShiftError('')
    setEditingShift(s)
    setShowShiftModal(true)
  }

  const addSegment = () => setShiftSegments(prev => [...prev, { start_time: '13:00', end_time: '17:00' }])
  const removeSegment = (i: number) => setShiftSegments(prev => prev.filter((_, idx) => idx !== i))
  const updateSegment = (i: number, field: string, val: string) => {
    setShiftSegments(prev => prev.map((seg, idx) => idx === i ? { ...seg, [field]: val } : seg))
  }

  const handleSaveShift = async () => {
    setShiftError('')
    if (!shiftForm.staff) { setShiftError('Select a staff member.'); return }
    if (!shiftForm.date) { setShiftError('Date is required.'); return }
    for (const seg of shiftSegments) {
      if (!seg.start_time || !seg.end_time) { setShiftError('All segments need start and end times.'); return }
      if (seg.start_time >= seg.end_time) { setShiftError('End time must be after start time for each segment.'); return }
    }
    setShiftSaving(true)
    if (editingShift) {
      // Update single shift
      const seg = shiftSegments[0]
      const res = await updateShift(editingShift.id, { ...shiftForm, staff: Number(shiftForm.staff), start_time: seg.start_time, end_time: seg.end_time })
      if (res.error) { setShiftError(res.error); setShiftSaving(false); return }
    } else {
      // Create one shift per segment (split shift support)
      for (const seg of shiftSegments) {
        const res = await createShift({ ...shiftForm, staff: Number(shiftForm.staff), start_time: seg.start_time, end_time: seg.end_time })
        if (res.error) { setShiftError(res.error); setShiftSaving(false); return }
      }
    }
    setShiftSaving(false)
    setShowShiftModal(false)
    loadData()
  }

  const handleDeleteShift = async (s: any) => {
    if (!confirm(`Delete shift for ${s.staff_name} on ${s.date}?`)) return
    const res = await deleteShift(s.id)
    if (res.error) { alert(res.error); return }
    loadData()
  }

  // --- Working Hours handlers ---
  const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const defaultSeg = { start_time: '09:00', end_time: '17:00', break_minutes: 0 }

  const loadWorkingHours = async (staffId: number) => {
    setWhStaffId(staffId)
    const res = await getWorkingHours({ staff_id: staffId })
    const entries = res.data || []
    const grid: Record<number, { start_time: string; end_time: string; break_minutes: number }[]> = {}
    for (let d = 0; d < 7; d++) grid[d] = []
    for (const e of entries) {
      grid[e.day_of_week].push({ start_time: e.start_time?.slice(0, 5) || '09:00', end_time: e.end_time?.slice(0, 5) || '17:00', break_minutes: e.break_minutes || 0 })
    }
    setWhGrid(grid)
    setWorkingHours(entries)
  }

  const saveWorkingHours = async () => {
    if (!whStaffId) return
    setWhSaving(true)
    const hours: any[] = []
    for (let d = 0; d < 7; d++) {
      for (const seg of (whGrid[d] || [])) {
        hours.push({ day_of_week: d, start_time: seg.start_time, end_time: seg.end_time, break_minutes: seg.break_minutes })
      }
    }
    const res = await bulkSetWorkingHours(whStaffId, hours)
    if (res.error) alert(res.error)
    else alert('Working hours saved.')
    setWhSaving(false)
  }

  const addWhSegment = (day: number) => {
    setWhGrid(prev => ({ ...prev, [day]: [...(prev[day] || []), { ...defaultSeg }] }))
  }
  const removeWhSegment = (day: number, idx: number) => {
    setWhGrid(prev => ({ ...prev, [day]: (prev[day] || []).filter((_, i) => i !== idx) }))
  }
  const updateWhSegment = (day: number, idx: number, field: string, val: any) => {
    setWhGrid(prev => ({ ...prev, [day]: (prev[day] || []).map((seg, i) => i === idx ? { ...seg, [field]: val } : seg) }))
  }

  const calcSegHours = (seg: { start_time: string; end_time: string; break_minutes: number }) => {
    const [sh, sm] = seg.start_time.split(':').map(Number)
    const [eh, em] = seg.end_time.split(':').map(Number)
    return Math.max(0, (eh * 60 + em - sh * 60 - sm - seg.break_minutes) / 60)
  }
  const calcDayHours = (segs: { start_time: string; end_time: string; break_minutes: number }[]) =>
    segs.reduce((sum, seg) => sum + calcSegHours(seg), 0)
  const calcWeeklyHours = () =>
    DAYS.reduce((sum, _, d) => sum + calcDayHours(whGrid[d] || []), 0)

  // --- Timesheet handlers ---
  const initTsDates = () => {
    const now = new Date()
    const mon = new Date(now)
    mon.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1))
    const sun = new Date(mon)
    sun.setDate(mon.getDate() + 6)
    return { from: mon.toISOString().split('T')[0], to: sun.toISOString().split('T')[0] }
  }

  const loadTimesheets = async (from?: string, to?: string, staffId?: string) => {
    const dates = initTsDates()
    const df = from || tsDateFrom || dates.from
    const dt = to || tsDateTo || dates.to
    if (!tsDateFrom) setTsDateFrom(df)
    if (!tsDateTo) setTsDateTo(dt)
    const params: any = { date_from: df, date_to: dt }
    if (staffId || tsStaffFilter) params.staff_id = Number(staffId || tsStaffFilter)
    const res = await getTimesheets(params)
    setTimesheets(res.data || [])
  }

  const handleGenerateTimesheets = async () => {
    if (!tsDateFrom || !tsDateTo) { alert('Set date range first.'); return }
    setTsGenerating(true)
    const data: any = { date_from: tsDateFrom, date_to: tsDateTo }
    if (tsStaffFilter) data.staff_id = Number(tsStaffFilter)
    const res = await generateTimesheets(data)
    if (res.error) alert(res.error)
    else alert(res.data?.detail || 'Timesheets generated.')
    setTsGenerating(false)
    loadTimesheets()
  }

  const openEditTs = (ts: any) => {
    setEditingTs(ts)
    setTsForm({
      actual_start: ts.actual_start?.slice(0, 5) || ts.scheduled_start?.slice(0, 5) || '',
      actual_end: ts.actual_end?.slice(0, 5) || ts.scheduled_end?.slice(0, 5) || '',
      actual_break_minutes: ts.actual_break_minutes ?? ts.scheduled_break_minutes ?? 0,
      status: ts.status || 'SCHEDULED',
      notes: ts.notes || '',
    })
  }

  const saveTs = async () => {
    if (!editingTs) return
    setTsSaving(true)
    const res = await updateTimesheet(editingTs.id, tsForm)
    if (res.error) alert(res.error)
    setTsSaving(false)
    setEditingTs(null)
    loadTimesheets()
  }

  if (loading) return <div className="empty-state">Loading staff data…</div>

  const tabLabels: Record<string, string> = { profiles: 'Profiles', hours: 'Working Hours', timesheets: 'Timesheets', shifts: 'Shifts', leave: 'Leave', training: 'Training' }

  return (
    <div>
      <div className="page-header"><h1>Staff Management</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="tabs">
        {(['profiles', 'hours', 'timesheets', 'shifts', 'leave', 'training'] as const).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => { setTab(t); if (t === 'timesheets' && timesheets.length === 0) loadTimesheets() }}>{tabLabels[t]}</button>
        ))}
      </div>

      {tab === 'profiles' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-primary" onClick={openAdd}>+ Add Staff Member</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Role</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {staff.map((s: any) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.display_name}</td>
                    <td>{s.role}</td>
                    <td>{s.email}</td>
                    <td>{s.phone || '—'}</td>
                    <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-neutral'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>
                      <button className="btn btn-sm" onClick={() => openEdit(s)} style={{ marginRight: 8 }}>Edit</button>
                      {s.is_active && <button className="btn btn-sm btn-danger" onClick={() => handleDelete(s)}>Deactivate</button>}
                    </td>
                  </tr>
                ))}
                {staff.length === 0 && <tr><td colSpan={6} className="empty-state">No staff profiles</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'hours' && (
        <div style={{ maxWidth: 780 }}>
          <div style={{ marginBottom: 16 }}>
            <label className="form-label">Select Staff Member</label>
            <select className="form-input" value={whStaffId || ''} onChange={e => { const id = Number(e.target.value); if (id) loadWorkingHours(id) }} style={{ maxWidth: 300 }}>
              <option value="">Choose staff…</option>
              {staff.map((s: any) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
            </select>
          </div>
          {whStaffId && (
            <>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Day</th><th>Start</th><th>End</th><th>Break (min)</th><th>Hours</th><th></th></tr></thead>
                  <tbody>
                    {DAYS.map((dayName, d) => {
                      const segs = whGrid[d] || []
                      const dayHrs = calcDayHours(segs)
                      return (
                        <React.Fragment key={d}>
                          {segs.length === 0 ? (
                            <tr style={{ opacity: 0.45 }}>
                              <td style={{ fontWeight: 600 }}>{dayName}</td>
                              <td colSpan={3} style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>Day off</td>
                              <td>—</td>
                              <td><button className="btn btn-sm" onClick={() => addWhSegment(d)}>+ Add</button></td>
                            </tr>
                          ) : (
                            segs.map((seg, i) => (
                              <tr key={`${d}-${i}`}>
                                <td style={{ fontWeight: 600 }}>{i === 0 ? dayName : ''}{segs.length > 1 && <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginLeft: 4 }}>{i === 0 ? '' : `#${i + 1}`}</span>}</td>
                                <td><input className="form-input" type="time" value={seg.start_time} onChange={e => updateWhSegment(d, i, 'start_time', e.target.value)} style={{ width: 120 }} /></td>
                                <td><input className="form-input" type="time" value={seg.end_time} onChange={e => updateWhSegment(d, i, 'end_time', e.target.value)} style={{ width: 120 }} /></td>
                                <td><input className="form-input" type="number" value={seg.break_minutes} onChange={e => updateWhSegment(d, i, 'break_minutes', Number(e.target.value))} style={{ width: 80 }} min={0} /></td>
                                <td>{i === 0 ? `${dayHrs.toFixed(1)}h` : ''}</td>
                                <td style={{ whiteSpace: 'nowrap' }}>
                                  {i === 0 && <button className="btn btn-sm" onClick={() => addWhSegment(d)} title="Add split shift" style={{ marginRight: 4 }}>+ Split</button>}
                                  <button className="btn btn-sm btn-danger" onClick={() => removeWhSegment(d, i)} title="Remove this segment">×</button>
                                </td>
                              </tr>
                            ))
                          )}
                        </React.Fragment>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                  Weekly total: {calcWeeklyHours().toFixed(1)}h
                </span>
                <button className="btn btn-primary" onClick={saveWorkingHours} disabled={whSaving}>{whSaving ? 'Saving…' : 'Save Working Hours'}</button>
              </div>
            </>
          )}
          {!whStaffId && <div className="empty-state">Select a staff member to set their working hours</div>}
        </div>
      )}

      {tab === 'timesheets' && (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
            <div>
              <label className="form-label">From</label>
              <input className="form-input" type="date" value={tsDateFrom} onChange={e => setTsDateFrom(e.target.value)} />
            </div>
            <div>
              <label className="form-label">To</label>
              <input className="form-input" type="date" value={tsDateTo} onChange={e => setTsDateTo(e.target.value)} />
            </div>
            <div>
              <label className="form-label">Staff</label>
              <select className="form-input" value={tsStaffFilter} onChange={e => setTsStaffFilter(e.target.value)}>
                <option value="">All Staff</option>
                {staff.map((s: any) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
              </select>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => loadTimesheets()}>Load</button>
            <button className="btn btn-sm" onClick={handleGenerateTimesheets} disabled={tsGenerating} title="Auto-populate from working hours">{tsGenerating ? 'Generating…' : 'Generate from Hours'}</button>
          </div>

          {editingTs && (
            <div style={{ background: 'var(--color-primary-light)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: 16 }}>
              <h3 style={{ marginBottom: 8 }}>Edit: {editingTs.staff_name} — {editingTs.date}</h3>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <div>
                  <label className="form-label">Actual Start</label>
                  <input className="form-input" type="time" value={tsForm.actual_start} onChange={e => setTsForm({ ...tsForm, actual_start: e.target.value })} />
                </div>
                <div>
                  <label className="form-label">Actual End</label>
                  <input className="form-input" type="time" value={tsForm.actual_end} onChange={e => setTsForm({ ...tsForm, actual_end: e.target.value })} />
                </div>
                <div>
                  <label className="form-label">Break (min)</label>
                  <input className="form-input" type="number" value={tsForm.actual_break_minutes} onChange={e => setTsForm({ ...tsForm, actual_break_minutes: Number(e.target.value) })} min={0} style={{ width: 80 }} />
                </div>
                <div>
                  <label className="form-label">Status</label>
                  <select className="form-input" value={tsForm.status} onChange={e => setTsForm({ ...tsForm, status: e.target.value })}>
                    <option value="SCHEDULED">Scheduled</option>
                    <option value="WORKED">Worked</option>
                    <option value="LATE">Late Arrival</option>
                    <option value="LEFT_EARLY">Left Early</option>
                    <option value="ABSENT">Absent</option>
                    <option value="SICK">Sick</option>
                    <option value="HOLIDAY">Holiday</option>
                    <option value="AMENDED">Amended</option>
                  </select>
                </div>
                <div style={{ flex: 1, minWidth: 150 }}>
                  <label className="form-label">Notes</label>
                  <input className="form-input" value={tsForm.notes} onChange={e => setTsForm({ ...tsForm, notes: e.target.value })} placeholder="e.g. Left 30min early" />
                </div>
                <button className="btn btn-primary btn-sm" onClick={saveTs} disabled={tsSaving}>{tsSaving ? '…' : 'Save'}</button>
                <button className="btn btn-sm" onClick={() => setEditingTs(null)}>Cancel</button>
              </div>
            </div>
          )}

          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Staff</th><th>Sched. Start</th><th>Sched. End</th><th>Sched. Hrs</th><th>Actual Start</th><th>Actual End</th><th>Actual Hrs</th><th>Variance</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {timesheets.map((ts: any) => {
                  const variance = ts.variance_hours || 0
                  const statusColors: Record<string, string> = { WORKED: 'badge-success', SCHEDULED: 'badge-neutral', LATE: 'badge-warning', LEFT_EARLY: 'badge-warning', ABSENT: 'badge-danger', SICK: 'badge-danger', HOLIDAY: 'badge-info', AMENDED: 'badge-info' }
                  return (
                    <tr key={ts.id}>
                      <td style={{ fontWeight: 600 }}>{ts.date}</td>
                      <td>{ts.staff_name}</td>
                      <td>{ts.scheduled_start?.slice(0, 5) || '—'}</td>
                      <td>{ts.scheduled_end?.slice(0, 5) || '—'}</td>
                      <td>{ts.scheduled_hours ? `${Number(ts.scheduled_hours).toFixed(1)}h` : '—'}</td>
                      <td>{ts.actual_start?.slice(0, 5) || '—'}</td>
                      <td>{ts.actual_end?.slice(0, 5) || '—'}</td>
                      <td>{ts.actual_hours ? `${Number(ts.actual_hours).toFixed(1)}h` : '—'}</td>
                      <td style={{ color: variance < 0 ? 'var(--color-danger)' : variance > 0 ? 'var(--color-success)' : 'inherit', fontWeight: variance !== 0 ? 600 : 400 }}>{variance !== 0 ? `${variance > 0 ? '+' : ''}${variance.toFixed(1)}h` : '—'}</td>
                      <td><span className={`badge ${statusColors[ts.status] || 'badge-neutral'}`}>{ts.status_display || ts.status}</span></td>
                      <td><button className="btn btn-sm" onClick={() => openEditTs(ts)}>Edit</button></td>
                    </tr>
                  )
                })}
                {timesheets.length === 0 && <tr><td colSpan={11} className="empty-state">No timesheet entries. Set working hours first, then click "Generate from Hours".</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'shifts' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button className="btn btn-primary" onClick={openAddShift}>+ Add Shift</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Staff</th><th>Start</th><th>End</th><th>Hours</th><th>Location</th><th>Published</th><th>Actions</th></tr></thead>
              <tbody>
                {shifts.map((s: any) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.date}</td>
                    <td>{s.staff_name}</td>
                    <td>{s.start_time?.slice(0, 5)}</td>
                    <td>{s.end_time?.slice(0, 5)}</td>
                    <td>{s.duration_hours ? `${Number(s.duration_hours).toFixed(1)}h` : '—'}</td>
                    <td>{s.location || '—'}</td>
                    <td><span className={`badge ${s.is_published ? 'badge-success' : 'badge-neutral'}`}>{s.is_published ? 'Yes' : 'Draft'}</span></td>
                    <td>
                      <button className="btn btn-sm" onClick={() => openEditShift(s)} style={{ marginRight: 8 }}>Edit</button>
                      <button className="btn btn-sm btn-danger" onClick={() => handleDeleteShift(s)}>Delete</button>
                    </td>
                  </tr>
                ))}
                {shifts.length === 0 && <tr><td colSpan={8} className="empty-state">No shifts assigned yet</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'leave' && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Staff</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th></tr></thead>
            <tbody>
              {leave.map((l: any) => (
                <tr key={l.id}><td style={{ fontWeight: 600 }}>{l.staff_name}</td><td>{l.leave_type}</td><td>{l.start_date}</td><td>{l.end_date}</td><td>{l.duration_days}</td><td style={{ maxWidth: 200 }}>{l.reason}</td><td><span className={`badge ${l.status === 'APPROVED' ? 'badge-success' : l.status === 'PENDING' ? 'badge-warning' : 'badge-danger'}`}>{l.status}</span></td></tr>
              ))}
              {leave.length === 0 && <tr><td colSpan={7} className="empty-state">No leave requests</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'training' && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Staff</th><th>Course</th><th>Provider</th><th>Completed</th><th>Expiry</th><th>Status</th></tr></thead>
            <tbody>
              {training.map((t: any) => (
                <tr key={t.id}><td style={{ fontWeight: 600 }}>{t.staff_name}</td><td>{t.title}</td><td>{t.provider}</td><td>{t.completed_date}</td><td>{t.expiry_date || 'N/A'}</td><td><span className={`badge ${t.is_expired ? 'badge-danger' : 'badge-success'}`}>{t.is_expired ? 'EXPIRED' : 'VALID'}</span></td></tr>
              ))}
              {training.length === 0 && <tr><td colSpan={6} className="empty-state">No training records</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit Staff Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 style={{ marginBottom: 16 }}>{editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}</h2>
            {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{error}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">First Name *</label>
                  <input className="form-input" value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} placeholder="e.g. Sam" />
                </div>
                <div>
                  <label className="form-label">Last Name *</label>
                  <input className="form-input" value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} placeholder="e.g. Kim" />
                </div>
              </div>
              <div>
                <label className="form-label">Email *</label>
                <input className="form-input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="e.g. sam.kim@company.com" />
              </div>
              <div>
                <label className="form-label">Phone</label>
                <input className="form-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="e.g. 07700 900000" />
              </div>
              <div>
                <label className="form-label">Role</label>
                <select className="form-input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                  <option value="staff">Staff</option>
                  <option value="manager">Manager</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving…' : editingStaff ? 'Save Changes' : 'Add Staff'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Credentials Modal — shown after successful staff creation */}
      {createdCreds && (
        <div className="modal-overlay" onClick={() => setCreatedCreds(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 style={{ marginBottom: 4 }}>Staff Member Created</h2>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: 16, fontSize: '0.9rem' }}>Share these login details with <strong>{createdCreds.name}</strong>. They will be asked to set their own password on first login.</p>
            <div style={{ background: 'var(--color-primary-light)', borderRadius: 'var(--radius-md)', padding: '1rem', display: 'grid', gap: 8, fontSize: '0.9rem' }}>
              <div><strong>Login URL:</strong> <code>{window.location.origin}/login</code></div>
              <div><strong>Email:</strong> <code>{createdCreds.email}</code></div>
              <div><strong>Temporary Password:</strong> <code style={{ fontSize: '1.1rem', fontWeight: 700 }}>{createdCreds.temp_password}</code></div>
            </div>
            <p style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>This password is shown once. The staff member must change it on their first login.</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button className="btn btn-primary" onClick={() => setCreatedCreds(null)}>Done</button>
            </div>
          </div>
        </div>
      )}

      {/* Shift Modal */}
      {showShiftModal && (
        <div className="modal-overlay" onClick={() => setShowShiftModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <h2>{editingShift ? 'Edit Shift' : 'Add Shift'}</h2>
            {shiftError && <div className="alert alert-danger">{shiftError}</div>}
            <div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
              <div>
                <label className="form-label">Staff Member *</label>
                <select className="form-input" value={shiftForm.staff} onChange={e => setShiftForm({ ...shiftForm, staff: e.target.value })}>
                  <option value="">Select staff…</option>
                  {staff.map((s: any) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Date *</label>
                <input className="form-input" type="date" value={shiftForm.date} onChange={e => setShiftForm({ ...shiftForm, date: e.target.value })} />
              </div>

              {/* Time segments — split shift support */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <label className="form-label" style={{ margin: 0 }}>Working Hours *</label>
                  {!editingShift && <button type="button" className="btn btn-sm" onClick={addSegment}>+ Split Shift</button>}
                </div>
                {shiftSegments.map((seg, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ flex: 1 }}>
                      {i === 0 && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Start</span>}
                      <input className="form-input" type="time" value={seg.start_time} onChange={e => updateSegment(i, 'start_time', e.target.value)} />
                    </div>
                    <span style={{ paddingTop: i === 0 ? 16 : 0 }}>→</span>
                    <div style={{ flex: 1 }}>
                      {i === 0 && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>End</span>}
                      <input className="form-input" type="time" value={seg.end_time} onChange={e => updateSegment(i, 'end_time', e.target.value)} />
                    </div>
                    {shiftSegments.length > 1 && (
                      <button type="button" onClick={() => removeSegment(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', fontWeight: 700, fontSize: '1.2rem', paddingTop: i === 0 ? 16 : 0 }}>×</button>
                    )}
                  </div>
                ))}
                {shiftSegments.length > 1 && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: 4 }}>Split shift: {shiftSegments.length} segments will be created for this day.</p>
                )}
              </div>

              <div>
                <label className="form-label">Location</label>
                <input className="form-input" value={shiftForm.location} onChange={e => setShiftForm({ ...shiftForm, location: e.target.value })} placeholder="e.g. Main Office" />
              </div>
              <div>
                <label className="form-label">Notes</label>
                <input className="form-input" value={shiftForm.notes} onChange={e => setShiftForm({ ...shiftForm, notes: e.target.value })} placeholder="Optional notes" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input type="checkbox" id="shift-published" checked={shiftForm.is_published} onChange={e => setShiftForm({ ...shiftForm, is_published: e.target.checked })} />
                <label htmlFor="shift-published" style={{ fontSize: '0.9rem' }}>Published (visible to staff)</label>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowShiftModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveShift} disabled={shiftSaving}>{shiftSaving ? 'Saving…' : editingShift ? 'Save Changes' : 'Add Shift'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
