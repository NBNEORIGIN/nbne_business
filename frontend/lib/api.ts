// ============================================================
// NBNE Platform Rev 3 — API Client
// Typed fetch helpers with JWT auth for Django backend
// ============================================================

const API_BASE = '/api/django'

// --- Token Management (client-side) ---
let accessToken: string | null = null
let refreshToken: string | null = null

export function setTokens(access: string, refresh: string) {
  accessToken = access
  refreshToken = refresh
  if (typeof window !== 'undefined') {
    localStorage.setItem('nbne_access', access)
    localStorage.setItem('nbne_refresh', refresh)
  }
}

export function getAccessToken(): string | null {
  if (!accessToken && typeof window !== 'undefined') {
    accessToken = localStorage.getItem('nbne_access')
  }
  return accessToken
}

export function getRefreshToken(): string | null {
  if (!refreshToken && typeof window !== 'undefined') {
    refreshToken = localStorage.getItem('nbne_refresh')
  }
  return refreshToken
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  if (typeof window !== 'undefined') {
    localStorage.removeItem('nbne_access')
    localStorage.removeItem('nbne_refresh')
  }
}

export function isLoggedIn(): boolean {
  return !!getAccessToken()
}

// --- Parse JWT payload without verification (client-side only) ---
export function parseJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload
  } catch {
    return null
  }
}

export function getCurrentUser() {
  const token = getAccessToken()
  if (!token) return null
  const payload = parseJwtPayload(token)
  if (!payload) return null
  return {
    id: payload.user_id,
    name: payload.name || '',
    email: payload.email || '',
    role: payload.role || 'customer',
    tier: payload.tier || 1,
  }
}

// --- Refresh token ---
async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) return false
  try {
    const res = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return false
    const data = await res.json()
    accessToken = data.access
    if (typeof window !== 'undefined') {
      localStorage.setItem('nbne_access', data.access)
    }
    if (data.refresh) {
      refreshToken = data.refresh
      if (typeof window !== 'undefined') {
        localStorage.setItem('nbne_refresh', data.refresh)
      }
    }
    return true
  } catch {
    return false
  }
}

// --- Core fetch with auth ---
async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<{ data: T | null; error: string | null; status: number }> {
  const token = getAccessToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    // Ensure trailing slash before query string to avoid Django 301 redirects
    let url = `${API_BASE}${path}`
    const qIdx = url.indexOf('?')
    if (qIdx === -1) {
      if (!url.endsWith('/')) url += '/'
    } else {
      const base = url.slice(0, qIdx)
      const qs = url.slice(qIdx)
      if (!base.endsWith('/')) url = base + '/' + qs
    }

    const res = await fetch(url, {
      ...options,
      headers,
    })

    // Token expired — try refresh
    if (res.status === 401 && retry) {
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        return apiFetch<T>(path, options, false)
      }
      clearTokens()
      return { data: null, error: 'Session expired', status: 401 }
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      const errMsg = errData.detail || errData.error || errData.message || `Error ${res.status}`
      return { data: null, error: errMsg, status: res.status }
    }

    const data = await res.json()
    return { data, error: null, status: res.status }
  } catch (err: any) {
    return { data: null, error: err.message || 'Network error', status: 0 }
  }
}

// --- Auth ---
export async function login(username: string, password: string) {
  const res = await apiFetch<{ access: string; refresh: string; user: any }>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  if (res.data) {
    setTokens(res.data.access, res.data.refresh)
  }
  return res
}

export async function getMe() {
  return apiFetch<any>('/auth/me/')
}

export async function setPassword(newPassword: string) {
  return apiFetch<any>('/auth/me/set-password/', { method: 'POST', body: JSON.stringify({ new_password: newPassword }) })
}

export async function requestPasswordReset(email: string) {
  return apiFetch<any>('/auth/password-reset/', { method: 'POST', body: JSON.stringify({ email }) })
}

export async function validateResetToken(token: string) {
  return apiFetch<any>(`/auth/validate-token/?token=${token}`)
}

export async function setPasswordWithToken(token: string, newPassword: string) {
  return apiFetch<any>('/auth/set-password-token/', { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) })
}

// --- Tenant ---
export async function getTenantSettings(params?: { tenant?: string }) {
  const qs = params?.tenant ? `?tenant=${params.tenant}` : ''
  return apiFetch<any>(`/tenant/${qs}`)
}

export async function getTenantBranding(params?: { tenant?: string }) {
  const qs = params?.tenant ? `?tenant=${params.tenant}` : ''
  return apiFetch<any>(`/tenant/branding/${qs}`)
}

// --- Bookings ---
export async function getServices(params?: { all?: boolean }) {
  const qs = params?.all ? '?all=1' : ''
  return apiFetch<any[]>(`/services/${qs}`)
}

export async function createService(data: any) {
  return apiFetch<any>('/services/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateService(id: number, data: any) {
  return apiFetch<any>(`/services/${id}/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteService(id: number) {
  return apiFetch<any>(`/services/${id}/`, { method: 'DELETE' })
}

export function getSlots(params?: { service_id?: number; date_from?: string; date_to?: string }) {
  const qs = new URLSearchParams()
  if (params?.service_id) qs.set('service_id', String(params.service_id))
  if (params?.date_from) qs.set('date_from', params.date_from)
  if (params?.date_to) qs.set('date_to', params.date_to)
  const q = qs.toString()
  return apiFetch<any[]>(`/bookings/slots/${q ? '?' + q : ''}`)
}

export async function getBookableStaff(serviceId?: number) {
  const q = serviceId ? `?service_id=${serviceId}` : ''
  return apiFetch<any[]>(`/bookings/staff-available/${q}`)
}

export async function getStaffSlots(staffId: number, serviceId: number, date: string) {
  return apiFetch<any>(`/bookings/staff-slots/?staff_id=${staffId}&service_id=${serviceId}&date=${date}`)
}

export async function checkDisclaimer(email: string) {
  return apiFetch<any>(`/bookings/disclaimer/check/?email=${encodeURIComponent(email)}`)
}

export async function signDisclaimer(data: { email: string; name: string; disclaimer_id: number }) {
  return apiFetch<any>('/bookings/disclaimer/sign/', { method: 'POST', body: JSON.stringify(data) })
}

export async function createBooking(data: any) {
  return apiFetch<any>('/bookings/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function getBookings(params?: { status?: string; email?: string }) {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.email) qs.set('email', params.email)
  const q = qs.toString()
  return apiFetch<any[]>(`/bookings/${q ? '?' + q : ''}`)
}

export async function confirmBooking(id: number) {
  return apiFetch<any>(`/bookings/${id}/confirm/`, { method: 'POST' })
}

export async function cancelBooking(id: number, reason = '') {
  return apiFetch<any>(`/bookings/${id}/cancel/`, { method: 'POST', body: JSON.stringify({ reason }) })
}

export async function completeBooking(id: number) {
  return apiFetch<any>(`/bookings/${id}/complete/`, { method: 'POST' })
}

export async function deleteBooking(id: number) {
  return apiFetch<any>(`/bookings/${id}/delete/`, { method: 'DELETE' })
}

export async function markNoShow(id: number) {
  return apiFetch<any>(`/bookings/${id}/no-show/`, { method: 'POST' })
}

export async function assignStaffToBooking(bookingId: number, staffId: number | null) {
  return apiFetch<any>(`/bookings/${bookingId}/assign-staff/`, { method: 'POST', body: JSON.stringify({ staff_id: staffId || 0 }) })
}

export async function getBookingReports(params?: { report?: string; date_from?: string; date_to?: string; staff_id?: number }) {
  const qs = new URLSearchParams()
  if (params?.report) qs.set('report', params.report)
  if (params?.date_from) qs.set('date_from', params.date_from)
  if (params?.date_to) qs.set('date_to', params.date_to)
  if (params?.staff_id) qs.set('staff_id', String(params.staff_id))
  const q = qs.toString()
  return apiFetch<any>(`/bookings/reports/${q ? '?' + q : ''}`)
}

// --- Staff ---
export async function getStaffList() {
  return apiFetch<any[]>('/staff-module/')
}

export async function createStaff(data: { first_name: string; last_name: string; email: string; phone?: string; role?: string }) {
  return apiFetch<any>('/staff-module/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateStaff(id: number, data: Record<string, any>) {
  return apiFetch<any>(`/staff-module/${id}/update/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteStaff(id: number) {
  return apiFetch<any>(`/staff-module/${id}/delete/`, { method: 'DELETE' })
}

export async function getShifts(params?: { staff_id?: number; date?: string }) {
  const qs = new URLSearchParams()
  if (params?.staff_id) qs.set('staff_id', String(params.staff_id))
  if (params?.date) qs.set('date', params.date)
  const q = qs.toString()
  return apiFetch<any[]>(`/staff-module/shifts/${q ? '?' + q : ''}`)
}

export async function createShift(data: Record<string, any>) {
  return apiFetch<any>('/staff-module/shifts/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateShift(id: number, data: Record<string, any>) {
  return apiFetch<any>(`/staff-module/shifts/${id}/update/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteShift(id: number) {
  return apiFetch<any>(`/staff-module/shifts/${id}/delete/`, { method: 'DELETE' })
}

export async function getMyShifts() {
  return apiFetch<any[]>('/staff-module/my-shifts/')
}

export async function getLeaveRequests(params?: { status?: string }) {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  const q = qs.toString()
  return apiFetch<any[]>(`/staff-module/leave/${q ? '?' + q : ''}`)
}

export async function getLeaveCalendar(params: { date_from: string; date_to: string }) {
  const qs = new URLSearchParams()
  qs.set('date_from', params.date_from)
  qs.set('date_to', params.date_to)
  return apiFetch<any[]>(`/staff-module/leave/calendar/?${qs.toString()}`)
}

export async function createLeaveRequest(data: any) {
  return apiFetch<any>('/staff-module/leave/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function reviewLeave(id: number, status: string) {
  return apiFetch<any>(`/staff-module/leave/${id}/review/`, { method: 'POST', body: JSON.stringify({ status }) })
}

export async function deleteLeaveRequest(id: number) {
  return apiFetch<any>(`/staff-module/leave/${id}/delete/`, { method: 'DELETE' })
}

export async function getTrainingRecords() {
  return apiFetch<any[]>('/staff-module/training/')
}

export async function createTrainingRecord(data: any) {
  return apiFetch<any>('/staff-module/training/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function deleteTrainingRecord(id: number) {
  return apiFetch<any>(`/staff-module/training/${id}/delete/`, { method: 'DELETE' })
}

export async function getTrainingReminders() {
  return apiFetch<any[]>('/staff-module/training/reminders/')
}

export async function getTrainingCompliance() {
  return apiFetch<any[]>('/staff-module/training/compliance/')
}

export async function getTrainingCourses() {
  return apiFetch<any[]>('/staff-module/training/courses/')
}

export async function createTrainingCourse(data: any) {
  return apiFetch<any>('/staff-module/training/courses/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateTrainingCourse(id: number, data: any) {
  return apiFetch<any>(`/staff-module/training/courses/${id}/update/`, { method: 'PUT', body: JSON.stringify(data) })
}

export async function deleteTrainingCourse(id: number) {
  return apiFetch<any>(`/staff-module/training/courses/${id}/delete/`, { method: 'DELETE' })
}

// --- Working Hours ---
export async function getWorkingHours(params?: { staff_id?: number }) {
  const qs = new URLSearchParams()
  if (params?.staff_id) qs.set('staff_id', String(params.staff_id))
  const q = qs.toString()
  return apiFetch<any[]>(`/staff-module/working-hours/${q ? '?' + q : ''}`)
}

export async function bulkSetWorkingHours(staffId: number, hours: any[]) {
  return apiFetch<any>('/staff-module/working-hours/bulk-set/', {
    method: 'POST', body: JSON.stringify({ staff: staffId, hours }),
  })
}

export async function deleteWorkingHours(id: number) {
  return apiFetch<any>(`/staff-module/working-hours/${id}/delete/`, { method: 'DELETE' })
}

// --- Timesheets ---
export async function getTimesheets(params?: { staff_id?: number; date_from?: string; date_to?: string }) {
  const qs = new URLSearchParams()
  if (params?.staff_id) qs.set('staff_id', String(params.staff_id))
  if (params?.date_from) qs.set('date_from', params.date_from)
  if (params?.date_to) qs.set('date_to', params.date_to)
  const q = qs.toString()
  return apiFetch<any[]>(`/staff-module/timesheets/${q ? '?' + q : ''}`)
}

export async function updateTimesheet(id: number, data: Record<string, any>) {
  return apiFetch<any>(`/staff-module/timesheets/${id}/update/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function generateTimesheets(data: { date_from: string; date_to: string; staff_id?: number }) {
  return apiFetch<any>('/staff-module/timesheets/generate/', { method: 'POST', body: JSON.stringify(data) })
}

export async function getTimesheetSummary(params?: { period?: string; date?: string; staff_id?: number }) {
  const qs = new URLSearchParams()
  if (params?.period) qs.set('period', params.period)
  if (params?.date) qs.set('date', params.date)
  if (params?.staff_id) qs.set('staff_id', String(params.staff_id))
  const q = qs.toString()
  return apiFetch<any>(`/staff-module/timesheets/summary/${q ? '?' + q : ''}`)
}

// --- Project Codes ---
export async function getProjectCodes(params?: { include_inactive?: boolean }) {
  const qs = new URLSearchParams()
  if (params?.include_inactive) qs.set('include_inactive', 'true')
  const q = qs.toString()
  return apiFetch<any[]>(`/staff-module/project-codes/${q ? '?' + q : ''}`)
}

export async function createProjectCode(data: { code: string; name: string; client_name?: string; is_billable?: boolean; hourly_rate?: number; notes?: string }) {
  return apiFetch<any>('/staff-module/project-codes/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateProjectCode(id: number, data: Record<string, any>) {
  return apiFetch<any>(`/staff-module/project-codes/${id}/update/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteProjectCode(id: number) {
  return apiFetch<any>(`/staff-module/project-codes/${id}/delete/`, { method: 'DELETE' })
}

// --- Payroll ---
export async function getPayrollSummary(params?: { month?: string }) {
  const qs = new URLSearchParams()
  if (params?.month) qs.set('month', params.month)
  const q = qs.toString()
  return apiFetch<any>(`/staff-module/payroll/summary/${q ? '?' + q : ''}`)
}

export function getTimesheetExportUrl(params: { date_from: string; date_to: string; staff_id?: number }) {
  const qs = new URLSearchParams()
  qs.set('date_from', params.date_from)
  qs.set('date_to', params.date_to)
  if (params.staff_id) qs.set('staff_id', String(params.staff_id))
  return `${API_BASE}/staff-module/timesheets/export/?${qs.toString()}`
}

export async function downloadTimesheetCsv(params: { date_from: string; date_to: string; staff_id?: number }) {
  const token = getAccessToken()
  const url = getTimesheetExportUrl(params)
  const res = await fetch(url, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  })
  if (!res.ok) return { error: 'Export failed', data: null }
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `timesheets_${params.date_from}_to_${params.date_to}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
  return { error: null, data: true }
}

// --- Media URL helper ---
const BACKEND_BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_BASE_URL || '').trim()
  : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').trim()

export function getMediaUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  // Relative path from backend — prepend backend base
  return `${BACKEND_BASE}${path.startsWith('/') ? '' : '/'}${path}`
}

export function isImageFile(filename: string): boolean {
  return /\.(jpe?g|png|gif|webp|bmp|svg|heic|heif|tiff?)$/i.test(filename)
}

export function isVideoFile(filename: string): boolean {
  return /\.(mp4|webm|mov|avi|mkv|m4v)$/i.test(filename)
}

// --- Comms ---
export async function getChannels() {
  return apiFetch<any[]>('/comms/channels/')
}

export async function getMessages(channelId: number, limit = 50) {
  return apiFetch<any[]>(`/comms/channels/${channelId}/messages/?limit=${limit}`)
}

export async function sendMessage(channelId: number, body: string, files?: File[]) {
  if (files && files.length > 0) {
    // Use FormData for file uploads — bypass apiFetch to avoid JSON content-type
    const token = getAccessToken()
    const formData = new FormData()
    formData.append('body', body)
    for (const f of files) formData.append('files', f)
    try {
      const res = await fetch(`${API_BASE}/comms/channels/${channelId}/messages/create/`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        return { data: null, error: err.detail || err.error || `Error ${res.status}`, status: res.status }
      }
      const data = await res.json()
      return { data, error: null, status: res.status }
    } catch (err: any) {
      return { data: null, error: err.message || 'Network error', status: 0 }
    }
  }
  return apiFetch<any>(`/comms/channels/${channelId}/messages/create/`, {
    method: 'POST', body: JSON.stringify({ body }),
  })
}

// --- Compliance ---
export async function getComplianceDashboard() {
  return apiFetch<any>('/compliance/dashboard/')
}

// getComplianceCalendar moved below with year/month params

export async function getComplianceCategories() {
  return apiFetch<any[]>('/compliance/categories/')
}

export async function createComplianceCategory(data: any) {
  return apiFetch<any>('/compliance/categories/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function getComplianceItems(params?: { status?: string; category?: number; legal?: boolean }) {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.category) qs.set('category', String(params.category))
  if (params?.legal) qs.set('legal', 'true')
  const q = qs.toString()
  return apiFetch<any[]>(`/compliance/items/${q ? '?' + q : ''}`)
}

export async function createComplianceItem(data: any) {
  return apiFetch<any>('/compliance/items/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function completeComplianceItem(id: number, completedDate?: string) {
  return apiFetch<any>(`/compliance/items/${id}/complete/`, {
    method: 'POST', body: JSON.stringify(completedDate ? { completed_date: completedDate } : {}),
  })
}

export async function assignComplianceItem(id: number, userId: number) {
  return apiFetch<any>(`/compliance/items/${id}/assign/`, { method: 'POST', body: JSON.stringify({ user_id: userId }) })
}

export async function getMyActions() {
  return apiFetch<any[]>('/compliance/my-actions/')
}

export async function getMyTraining() {
  return apiFetch<any[]>('/compliance/my-training/')
}

export async function getTrainingList(params?: { user?: number; type?: string; status?: string }) {
  const qs = new URLSearchParams()
  if (params?.user) qs.set('user', String(params.user))
  if (params?.type) qs.set('type', params.type)
  if (params?.status) qs.set('status', params.status)
  const q = qs.toString()
  return apiFetch<any[]>(`/compliance/training/${q ? '?' + q : ''}`)
}

export async function getComplianceDocuments(params?: { type?: string }) {
  const qs = new URLSearchParams()
  if (params?.type) qs.set('type', params.type)
  const q = qs.toString()
  return apiFetch<any[]>(`/compliance/documents/${q ? '?' + q : ''}`)
}

export async function getComplianceActionLogs(params?: { item?: number; incident?: number; limit?: number }) {
  const qs = new URLSearchParams()
  if (params?.item) qs.set('item', String(params.item))
  if (params?.incident) qs.set('incident', String(params.incident))
  if (params?.limit) qs.set('limit', String(params.limit))
  const q = qs.toString()
  return apiFetch<any[]>(`/compliance/logs/${q ? '?' + q : ''}`)
}

export async function getIncidents(params?: { status?: string }) {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  const q = qs.toString()
  return apiFetch<any[]>(`/compliance/incidents/${q ? '?' + q : ''}`)
}

export async function createIncident(data: any) {
  return apiFetch<any>('/compliance/incidents/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function uploadIncidentPhoto(incidentId: number, image: File, caption = '') {
  const token = getAccessToken()
  const formData = new FormData()
  formData.append('image', image)
  formData.append('caption', caption)
  try {
    const res = await fetch(`${API_BASE}/compliance/incidents/${incidentId}/photo/`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return { data: null, error: err.detail || err.error || `Error ${res.status}`, status: res.status }
    }
    const data = await res.json()
    return { data, error: null, status: res.status }
  } catch (err: any) {
    return { data: null, error: err.message || 'Network error', status: 0 }
  }
}

export async function updateIncidentStatus(id: number, status: string, notes = '') {
  return apiFetch<any>(`/compliance/incidents/${id}/status/`, {
    method: 'POST', body: JSON.stringify({ status, resolution_notes: notes }),
  })
}

export async function deleteComplianceItem(id: number) {
  return apiFetch<any>(`/compliance/items/${id}/delete/`, { method: 'DELETE' })
}

export async function completeComplianceItemWithEvidence(id: number, formData: FormData) {
  const res = await fetch(`/api/django/compliance/items/${id}/complete/`, { method: 'POST', body: formData })
  const data = await res.json()
  return { data, error: res.ok ? null : data.error || 'Failed' }
}

export async function getWiggumDashboard() {
  return apiFetch<any>('/compliance/wiggum/')
}

export async function parseComplianceCommand(text: string) {
  return apiFetch<any>('/compliance/parse-command/', { method: 'POST', body: JSON.stringify({ text }) })
}

export async function getComplianceCalendar(year: number, month: number) {
  return apiFetch<any>(`/compliance/calendar/?year=${year}&month=${month}`)
}

export async function getComplianceAuditLog(limit = 20) {
  return apiFetch<any>(`/compliance/audit-log/?limit=${limit}`)
}

export async function getDashboardV2() {
  return apiFetch<any>('/compliance/dashboard-v2/')
}

export async function recalculateComplianceScore() {
  return apiFetch<any>('/compliance/recalculate/', { method: 'POST' })
}

export async function getRams() {
  return apiFetch<any[]>('/compliance/rams/')
}

export async function getAccidents() {
  return apiFetch<any[]>('/compliance/accidents/')
}

export async function createAccident(data: any) {
  return apiFetch<any>('/compliance/accidents/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateAccident(id: number, data: any) {
  return apiFetch<any>(`/compliance/accidents/${id}/update/`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteAccident(id: number) {
  return apiFetch<any>(`/compliance/accidents/${id}/delete/`, { method: 'DELETE' })
}

// --- Documents ---
export async function getDocuments() {
  return apiFetch<any[]>('/documents/')
}

// --- CRM ---
export async function getLeads(params?: { status?: string }) {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  const q = qs.toString()
  return apiFetch<any[]>(`/crm/leads/${q ? '?' + q : ''}`)
}

export async function createLead(data: any) {
  return apiFetch<any>('/crm/leads/create/', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateLeadStatus(id: number, status: string) {
  return apiFetch<any>(`/crm/leads/${id}/status/`, { method: 'POST', body: JSON.stringify({ status }) })
}

// --- Dashboard Today V2 (Operational Incident Board) ---
export async function getDashboardToday() {
  return apiFetch<any>('/dashboard/today/')
}

// --- Business Events (Event Logging Discipline) ---
export async function logBusinessEvent(data: {
  event_type: string
  action_label: string
  source_event_type?: string
  source_entity_type?: string
  source_entity_id?: number | null
  action_detail?: string
  payload?: Record<string, any>
}) {
  return apiFetch<any>('/events/log/', { method: 'POST', body: JSON.stringify(data) })
}

export async function getTodayResolved() {
  return apiFetch<any>('/events/today/')
}

export async function declineCover(data: {
  absent_staff_id: number
  declined_staff_id: number
  declined_staff_ids: number[]
  source_entity_id?: number | null
  service_id?: number | null
}) {
  return apiFetch<any>('/events/decline/', { method: 'POST', body: JSON.stringify(data) })
}

// --- Assistant (Stateless Command Parser) ---
export async function parseAssistantCommand(text: string) {
  return apiFetch<any>('/assistant/parse/', { method: 'POST', body: JSON.stringify({ text }) })
}

// --- Analytics ---
export async function getAnalyticsDashboard() {
  return apiFetch<any>('/analytics/dashboard/')
}

export async function getRecommendations() {
  return apiFetch<any[]>('/analytics/recommendations/')
}

// --- Audit ---
export async function getAuditLog(params?: { limit?: number; action?: string }) {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.action) qs.set('action', params.action)
  const q = qs.toString()
  return apiFetch<any[]>(`/audit/${q ? '?' + q : ''}`)
}

// --- Users (admin) ---
export async function getUsers(params?: { role?: string }) {
  const qs = new URLSearchParams()
  if (params?.role) qs.set('role', params.role)
  const q = qs.toString()
  return apiFetch<any[]>(`/auth/users/${q ? '?' + q : ''}`)
}
