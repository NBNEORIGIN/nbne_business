// ============================================================
// NBNE Platform Rev 2 — Shared Types
// ============================================================

// --- Auth & RBAC ---
export type UserRole = 'customer' | 'staff' | 'manager' | 'owner'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  avatar_initials: string
  active: boolean
}

export interface Session {
  user: User
  expires: string
}

// --- Permission Matrix ---
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  customer: 0,
  staff: 1,
  manager: 2,
  owner: 3,
}

export function hasMinRole(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole]
}

// --- Bookings ---
export interface Service {
  id: number; name: string; description: string
  duration_minutes: number; price_pence: number; deposit_pence: number
  category: string; active: boolean
}

export interface TimeSlot {
  id: number; date: string; start_time: string; end_time: string
  has_capacity: boolean; max_bookings: number
}

export interface Booking {
  id: number; customer_name: string; customer_email: string; customer_phone: string
  service_name: string; slot_date: string; slot_start: string; slot_end: string
  status: string; price_pence: number; notes: string; created_at: string
}

// --- Staff ---
export interface StaffMember {
  id: number; name: string; role: string; email: string; phone: string
  bio: string; avatar_initials: string; active: boolean; user_role: UserRole
}

export interface Shift {
  id: number; staff_name: string; date: string; start_time: string
  end_time: string; location: string; duration_hours: number; notes: string
}

export interface LeaveRequest {
  id: number; staff_name: string; leave_type: string; start_date: string
  end_date: string; duration_days: number; status: string; reason: string
}

export interface TrainingRecord {
  id: number; staff_name: string; title: string; provider: string
  completed_date: string; expiry_date: string | null; is_expired: boolean
}

// --- Chat / Comms ---
export interface Channel {
  id: number; name: string; channel_type: 'GENERAL' | 'TEAM' | 'DIRECT'
  member_count: number; unread_count: number
}

export interface ChatMessage {
  id: number; channel_id: number; sender_name: string; sender_id: string
  body: string; message_type: 'text' | 'image' | 'audio'
  media_url?: string; created_at: string
  read_by: string[]; delivered: boolean
}

export interface TypingIndicator {
  channel_id: number; user_name: string; is_typing: boolean
}

// --- CRM ---
export interface Lead {
  id: number; name: string; email: string; phone: string; source: string
  status: string; value_pence: number; notes: string; created_at: string
}

// --- Documents ---
export interface Document {
  id: number; title: string; category: string; uploaded_by: string
  uploaded_at: string; expiry_date: string | null; file_size: string
  tier_access: UserRole
}

// --- HSE / Compliance ---
export interface Incident {
  id: number; title: string; severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: string; reported_by: string; reported_at: string; description: string
}

export interface HazardFinding {
  id: number; assessment_id: number; category: string
  description: string; severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  confidence: number; evidence_url: string
  control_measures: string[]; regulatory_ref: string
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED'
}

export interface RiskAssessment {
  id: number; title: string; site_area: string; assessor: string
  assessment_date: string; review_date: string; status: string
  findings_count: number; high_risks: number
}

export interface RAMSDocument {
  id: number; title: string; version: string; created_by: string
  created_at: string; approved_by: string | null; status: string
}

export interface ComplianceScore {
  overall: number
  categories: { name: string; score: number; max: number }[]
  overdue_actions: number
  upcoming_reviews: number
}

export interface EquipmentItem {
  id: number; name: string; location: string; category: string
  last_inspection: string; next_inspection: string; status: string
}

// --- Schedule ---
export interface ScheduleDay {
  day: string; open: string; close: string; closed: boolean
  slot_duration_minutes: number
}

// --- Analytics ---
export interface DashboardMetric {
  label: string; value: string | number; change?: number; trend?: 'up' | 'down' | 'flat'
}

// --- Audit ---
export interface AuditEntry {
  id: number; user_name: string; user_role: UserRole
  action: string; entity_type: string; entity_id: number
  details: string; timestamp: string; ip_address: string
}
