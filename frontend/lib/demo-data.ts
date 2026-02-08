// ============================================================
// NBNE Platform Rev 2 — Demo Data (first-class, interconnected)
// ============================================================

import type {
  Service, Booking, StaffMember, Shift, LeaveRequest, TrainingRecord,
  Channel, ChatMessage, Lead, Document, Incident, HazardFinding,
  RiskAssessment, RAMSDocument, ComplianceScore, EquipmentItem,
  ScheduleDay, AuditEntry, User,
} from './types'

// --- Demo Users (all tiers) ---
export const DEMO_USERS: User[] = [
  { id: 'u1', email: 'owner@demo.local', name: 'Jordan Riley', role: 'owner', avatar_initials: 'JR', active: true },
  { id: 'u2', email: 'manager@demo.local', name: 'Sam Kim', role: 'manager', avatar_initials: 'SK', active: true },
  { id: 'u3', email: 'staff1@demo.local', name: 'Alex Taylor', role: 'staff', avatar_initials: 'AT', active: true },
  { id: 'u4', email: 'staff2@demo.local', name: 'Morgan Patel', role: 'staff', avatar_initials: 'MP', active: true },
  { id: 'u5', email: 'emma@example.com', name: 'Emma Wilson', role: 'customer', avatar_initials: 'EW', active: true },
  { id: 'u6', email: 'olivia@example.com', name: 'Olivia Brown', role: 'customer', avatar_initials: 'OB', active: true },
]

// --- Services ---
export const DEMO_SERVICES: Service[] = [
  { id: 1, name: 'Cut & Style', description: 'Precision cut and blow dry tailored to your face shape.', duration_minutes: 45, price_pence: 3500, deposit_pence: 1000, category: 'Cuts', active: true },
  { id: 2, name: 'Colour', description: 'Full colour, balayage, highlights, or creative colour.', duration_minutes: 90, price_pence: 6500, deposit_pence: 2000, category: 'Colour', active: true },
  { id: 3, name: 'Treatments', description: 'Deep conditioning, keratin smoothing, and scalp treatments.', duration_minutes: 60, price_pence: 2500, deposit_pence: 0, category: 'Treatments', active: true },
  { id: 4, name: 'Bridal & Occasion', description: 'Updos, braids, and styling for weddings and events.', duration_minutes: 120, price_pence: 7500, deposit_pence: 3000, category: 'Occasion', active: true },
  { id: 5, name: 'Gents Cut', description: 'Classic or modern cuts, skin fades, and beard trims.', duration_minutes: 30, price_pence: 2000, deposit_pence: 0, category: 'Cuts', active: true },
]

// --- Staff ---
export const DEMO_STAFF: StaffMember[] = [
  { id: 1, name: 'Jordan Riley', role: 'Senior Stylist & Owner', email: 'jordan@salonx.demo', phone: '07700 900001', bio: '12 years experience. Colour specialist and salon owner.', avatar_initials: 'JR', active: true, user_role: 'owner' },
  { id: 2, name: 'Sam Kim', role: 'Colour Technician & Manager', email: 'sam@salonx.demo', phone: '07700 900002', bio: 'Balayage and creative colour expert. Wella certified.', avatar_initials: 'SK', active: true, user_role: 'manager' },
  { id: 3, name: 'Alex Taylor', role: 'Stylist', email: 'alex@salonx.demo', phone: '07700 900003', bio: 'Specialises in precision cutting and bridal styling.', avatar_initials: 'AT', active: true, user_role: 'staff' },
  { id: 4, name: 'Morgan Patel', role: 'Junior Stylist', email: 'morgan@salonx.demo', phone: '07700 900004', bio: 'NVQ Level 3 qualified. Passionate about modern cuts.', avatar_initials: 'MP', active: true, user_role: 'staff' },
]

// --- Bookings ---
export const DEMO_BOOKINGS: Booking[] = [
  { id: 1001, customer_name: 'Emma Wilson', customer_email: 'emma@example.com', customer_phone: '07700 800001', service_name: 'Cut & Style', slot_date: '2026-02-09', slot_start: '09:00', slot_end: '09:45', status: 'CONFIRMED', price_pence: 3500, notes: '', created_at: '2026-02-05T10:30:00Z' },
  { id: 1002, customer_name: 'Olivia Brown', customer_email: 'olivia@example.com', customer_phone: '07700 800002', service_name: 'Colour', slot_date: '2026-02-09', slot_start: '10:00', slot_end: '11:30', status: 'CONFIRMED', price_pence: 6500, notes: 'Wants balayage, shown reference photos', created_at: '2026-02-04T14:15:00Z' },
  { id: 1003, customer_name: 'James Smith', customer_email: 'james@example.com', customer_phone: '07700 800003', service_name: 'Gents Cut', slot_date: '2026-02-09', slot_start: '11:00', slot_end: '11:30', status: 'CONFIRMED', price_pence: 2000, notes: 'Skin fade', created_at: '2026-02-06T09:00:00Z' },
  { id: 1004, customer_name: 'Sophie Davis', customer_email: 'sophie@example.com', customer_phone: '07700 800004', service_name: 'Treatments', slot_date: '2026-02-10', slot_start: '14:00', slot_end: '15:00', status: 'PENDING', price_pence: 2500, notes: 'Keratin treatment', created_at: '2026-02-07T11:20:00Z' },
  { id: 1005, customer_name: 'Charlotte Evans', customer_email: 'charlotte@example.com', customer_phone: '07700 800005', service_name: 'Bridal & Occasion', slot_date: '2026-03-15', slot_start: '09:00', slot_end: '11:00', status: 'PENDING_PAYMENT', price_pence: 7500, notes: 'Wedding day — trial booked for Feb 28', created_at: '2026-02-01T16:45:00Z' },
  { id: 1006, customer_name: 'Lucy Thomas', customer_email: 'lucy@example.com', customer_phone: '07700 800006', service_name: 'Cut & Style', slot_date: '2026-02-07', slot_start: '15:00', slot_end: '15:45', status: 'COMPLETED', price_pence: 3500, notes: '', created_at: '2026-02-03T08:30:00Z' },
  { id: 1007, customer_name: 'Hannah Roberts', customer_email: 'hannah@example.com', customer_phone: '07700 800007', service_name: 'Colour', slot_date: '2026-02-06', slot_start: '10:00', slot_end: '11:30', status: 'COMPLETED', price_pence: 6500, notes: 'Full head highlights', created_at: '2026-02-02T12:00:00Z' },
  { id: 1008, customer_name: 'Megan Clark', customer_email: 'megan@example.com', customer_phone: '07700 800008', service_name: 'Gents Cut', slot_date: '2026-02-08', slot_start: '11:00', slot_end: '11:30', status: 'CANCELLED', price_pence: 2000, notes: 'Cancelled — feeling unwell', created_at: '2026-02-05T15:00:00Z' },
]

// --- Shifts ---
export const DEMO_SHIFTS: Shift[] = [
  { id: 1, staff_name: 'Jordan Riley', date: '2026-02-09', start_time: '09:00', end_time: '17:00', location: 'Main Floor', duration_hours: 8, notes: '' },
  { id: 2, staff_name: 'Sam Kim', date: '2026-02-09', start_time: '09:00', end_time: '17:00', location: 'Main Floor', duration_hours: 8, notes: '' },
  { id: 3, staff_name: 'Alex Taylor', date: '2026-02-09', start_time: '10:00', end_time: '18:00', location: 'Main Floor', duration_hours: 8, notes: '' },
  { id: 4, staff_name: 'Morgan Patel', date: '2026-02-09', start_time: '09:00', end_time: '13:00', location: 'Main Floor', duration_hours: 4, notes: 'Half day' },
  { id: 5, staff_name: 'Jordan Riley', date: '2026-02-10', start_time: '09:00', end_time: '17:00', location: 'Main Floor', duration_hours: 8, notes: '' },
  { id: 6, staff_name: 'Sam Kim', date: '2026-02-10', start_time: '10:00', end_time: '18:00', location: 'Main Floor', duration_hours: 8, notes: '' },
]

// --- Leave ---
export const DEMO_LEAVE: LeaveRequest[] = [
  { id: 1, staff_name: 'Jordan Riley', leave_type: 'ANNUAL', start_date: '2026-03-16', end_date: '2026-03-20', duration_days: 5, status: 'APPROVED', reason: 'Holiday — visiting family' },
  { id: 2, staff_name: 'Sam Kim', leave_type: 'SICK', start_date: '2026-01-22', end_date: '2026-01-22', duration_days: 1, status: 'APPROVED', reason: 'Flu' },
  { id: 3, staff_name: 'Alex Taylor', leave_type: 'ANNUAL', start_date: '2026-04-10', end_date: '2026-04-11', duration_days: 2, status: 'PENDING', reason: 'Long weekend break' },
  { id: 4, staff_name: 'Morgan Patel', leave_type: 'TRAINING', start_date: '2026-02-10', end_date: '2026-02-10', duration_days: 1, status: 'APPROVED', reason: 'Wella colour workshop' },
]

// --- Training ---
export const DEMO_TRAINING: TrainingRecord[] = [
  { id: 1, staff_name: 'Jordan Riley', title: 'Colour Correction Masterclass', provider: 'Wella Professionals', completed_date: '2025-11-15', expiry_date: null, is_expired: false },
  { id: 2, staff_name: 'Sam Kim', title: 'Health & Safety Level 2', provider: 'City & Guilds', completed_date: '2024-06-01', expiry_date: '2027-06-01', is_expired: false },
  { id: 3, staff_name: 'Alex Taylor', title: 'First Aid at Work', provider: 'St John Ambulance', completed_date: '2023-03-10', expiry_date: '2026-03-10', is_expired: false },
  { id: 4, staff_name: 'Morgan Patel', title: 'Balayage Techniques', provider: "L'Oreal Academy", completed_date: '2025-09-20', expiry_date: null, is_expired: false },
  { id: 5, staff_name: 'Jordan Riley', title: 'Fire Safety Awareness', provider: 'Online CPD', completed_date: '2022-01-15', expiry_date: '2025-01-15', is_expired: true },
]

// --- Chat Channels ---
export const DEMO_CHANNELS: Channel[] = [
  { id: 1, name: 'general', channel_type: 'GENERAL', member_count: 4, unread_count: 2 },
  { id: 2, name: 'front-desk', channel_type: 'TEAM', member_count: 3, unread_count: 0 },
  { id: 3, name: 'training', channel_type: 'TEAM', member_count: 4, unread_count: 1 },
  { id: 4, name: 'Jordan & Sam', channel_type: 'DIRECT', member_count: 2, unread_count: 0 },
]

// --- Chat Messages ---
export const DEMO_MESSAGES: Record<number, ChatMessage[]> = {
  1: [
    { id: 1, channel_id: 1, sender_name: 'Jordan Riley', sender_id: 'u1', body: 'Morning everyone! Product rep visiting at 2pm today.', message_type: 'text', created_at: '2026-02-07T08:15:00Z', read_by: ['u1', 'u2', 'u3', 'u4'], delivered: true },
    { id: 2, channel_id: 1, sender_name: 'Sam Kim', sender_id: 'u2', body: "Thanks Jordan. I'll make sure the colour station is tidy.", message_type: 'text', created_at: '2026-02-07T08:22:00Z', read_by: ['u1', 'u2'], delivered: true },
    { id: 3, channel_id: 1, sender_name: 'Alex Taylor', sender_id: 'u3', body: 'Are they bringing samples? Would love to try the new toner range.', message_type: 'text', created_at: '2026-02-07T08:30:00Z', read_by: ['u1', 'u3'], delivered: true },
    { id: 4, channel_id: 1, sender_name: 'Jordan Riley', sender_id: 'u1', body: 'Yes! Full sample kit. We can test after close.', message_type: 'text', created_at: '2026-02-07T08:35:00Z', read_by: ['u1'], delivered: true },
    { id: 5, channel_id: 1, sender_name: 'Morgan Patel', sender_id: 'u4', body: 'Count me in!', message_type: 'text', created_at: '2026-02-07T08:40:00Z', read_by: ['u4'], delivered: true },
  ],
  2: [
    { id: 6, channel_id: 2, sender_name: 'Sam Kim', sender_id: 'u2', body: 'Walk-in just arrived for a gents cut. Alex, are you free?', message_type: 'text', created_at: '2026-02-07T10:05:00Z', read_by: ['u2', 'u3'], delivered: true },
    { id: 7, channel_id: 2, sender_name: 'Alex Taylor', sender_id: 'u3', body: 'Yep, finishing up now. Send them over in 5.', message_type: 'text', created_at: '2026-02-07T10:07:00Z', read_by: ['u2', 'u3'], delivered: true },
    { id: 8, channel_id: 2, sender_name: 'Morgan Patel', sender_id: 'u4', body: "We're running low on foils — should I add to the order?", message_type: 'text', created_at: '2026-02-07T11:30:00Z', read_by: ['u4'], delivered: true },
  ],
  3: [
    { id: 9, channel_id: 3, sender_name: 'Jordan Riley', sender_id: 'u1', body: 'Reminder: H&S refresher due for everyone by end of March.', message_type: 'text', created_at: '2026-02-05T09:00:00Z', read_by: ['u1', 'u2', 'u3'], delivered: true },
    { id: 10, channel_id: 3, sender_name: 'Alex Taylor', sender_id: 'u3', body: 'Done mine already! Certificate uploaded.', message_type: 'text', created_at: '2026-02-06T14:20:00Z', read_by: ['u1', 'u3'], delivered: true },
  ],
  4: [
    { id: 11, channel_id: 4, sender_name: 'Jordan Riley', sender_id: 'u1', body: 'Sam, can you cover the late shift Thursday?', message_type: 'text', created_at: '2026-02-06T16:00:00Z', read_by: ['u1', 'u2'], delivered: true },
    { id: 12, channel_id: 4, sender_name: 'Sam Kim', sender_id: 'u2', body: 'Sure, no problem. I can stay until 7.', message_type: 'text', created_at: '2026-02-06T16:05:00Z', read_by: ['u1', 'u2'], delivered: true },
  ],
}

// --- CRM Leads ---
export const DEMO_LEADS: Lead[] = [
  { id: 1, name: 'Rebecca Hall', email: 'rebecca@example.com', phone: '07700 700001', source: 'Website', status: 'NEW', value_pence: 6500, notes: 'Enquired about colour services', created_at: '2026-02-07T10:00:00Z' },
  { id: 2, name: 'David Wright', email: 'david@example.com', phone: '07700 700002', source: 'Instagram', status: 'CONTACTED', value_pence: 3500, notes: 'Saw our balayage reel, wants consultation', created_at: '2026-02-06T14:30:00Z' },
  { id: 3, name: 'Sarah Mitchell', email: 'sarah@example.com', phone: '07700 700003', source: 'Referral', status: 'QUALIFIED', value_pence: 7500, notes: 'Referred by Emma Wilson. Bridal enquiry for June wedding.', created_at: '2026-02-05T09:15:00Z' },
  { id: 4, name: 'Tom Baker', email: 'tom@example.com', phone: '07700 700004', source: 'Walk-in', status: 'CONVERTED', value_pence: 2000, notes: 'Walked in for gents cut, now a regular', created_at: '2026-01-20T11:00:00Z' },
  { id: 5, name: 'Lisa Green', email: 'lisa@example.com', phone: '07700 700005', source: 'Google', status: 'LOST', value_pence: 2500, notes: 'Enquired about treatments but went elsewhere', created_at: '2026-01-15T16:00:00Z' },
]

// --- Documents ---
export const DEMO_DOCUMENTS: Document[] = [
  { id: 1, title: 'Public Liability Insurance', category: 'Insurance', uploaded_by: 'Jordan Riley', uploaded_at: '2025-12-01T10:00:00Z', expiry_date: '2026-12-01', file_size: '2.4 MB', tier_access: 'manager' },
  { id: 2, title: 'Health & Safety Policy', category: 'Policy', uploaded_by: 'Jordan Riley', uploaded_at: '2025-10-15T09:00:00Z', expiry_date: null, file_size: '1.1 MB', tier_access: 'staff' },
  { id: 3, title: 'Fire Risk Assessment', category: 'Compliance', uploaded_by: 'Jordan Riley', uploaded_at: '2025-08-20T14:00:00Z', expiry_date: '2026-08-20', file_size: '3.2 MB', tier_access: 'staff' },
  { id: 4, title: 'Sam Kim — First Aid Certificate', category: 'Staff Cert', uploaded_by: 'Sam Kim', uploaded_at: '2025-11-10T11:00:00Z', expiry_date: '2028-11-10', file_size: '540 KB', tier_access: 'staff' },
  { id: 5, title: 'COSHH Assessment — Colour Products', category: 'Compliance', uploaded_by: 'Jordan Riley', uploaded_at: '2025-09-05T10:30:00Z', expiry_date: '2026-09-05', file_size: '890 KB', tier_access: 'staff' },
  { id: 6, title: 'Staff Handbook v3', category: 'Policy', uploaded_by: 'Jordan Riley', uploaded_at: '2026-01-05T08:00:00Z', expiry_date: null, file_size: '4.7 MB', tier_access: 'staff' },
]

// --- HSE Incidents ---
export const DEMO_INCIDENTS: Incident[] = [
  { id: 1, title: 'Minor chemical splash', severity: 'LOW', status: 'RESOLVED', reported_by: 'Sam Kim', reported_at: '2026-01-28T14:30:00Z', description: 'Small splash of developer on hand during mixing. First aid applied, no injury.' },
  { id: 2, title: 'Slip hazard — wet floor', severity: 'MEDIUM', status: 'RESOLVED', reported_by: 'Morgan Patel', reported_at: '2026-01-15T10:00:00Z', description: 'Water spill near basin area. Cleaned immediately, wet floor sign placed.' },
  { id: 3, title: 'Client allergic reaction', severity: 'HIGH', status: 'UNDER_REVIEW', reported_by: 'Jordan Riley', reported_at: '2026-02-03T16:00:00Z', description: 'Client reported mild itching after colour service despite negative patch test. Advised to see GP.' },
]

// --- HSE Risk Assessments ---
export const DEMO_RISK_ASSESSMENTS: RiskAssessment[] = [
  { id: 1, title: 'General Workplace Assessment', site_area: 'Whole Premises', assessor: 'Jordan Riley', assessment_date: '2025-11-01', review_date: '2026-11-01', status: 'CURRENT', findings_count: 8, high_risks: 1 },
  { id: 2, title: 'Chemical Handling — Colour Products', site_area: 'Colour Station', assessor: 'Sam Kim', assessment_date: '2025-09-15', review_date: '2026-09-15', status: 'CURRENT', findings_count: 5, high_risks: 0 },
  { id: 3, title: 'Fire Safety Assessment', site_area: 'Whole Premises', assessor: 'Jordan Riley', assessment_date: '2025-08-20', review_date: '2026-08-20', status: 'REVIEW_DUE', findings_count: 6, high_risks: 1 },
]

// --- HSE Hazard Findings ---
export const DEMO_HAZARD_FINDINGS: HazardFinding[] = [
  { id: 1, assessment_id: 1, category: 'Slips, Trips & Falls', description: 'Wet floor risk near wash basins — no permanent drainage mat', severity: 'MEDIUM', confidence: 0.85, evidence_url: '/evidence/floor-basins.jpg', control_measures: ['Install drainage mats', 'Wet floor signs available', 'Staff briefing on spill protocol'], regulatory_ref: 'HSE INDG225', status: 'IN_PROGRESS' },
  { id: 2, assessment_id: 1, category: 'Chemical Handling', description: 'Colour mixing area lacks eye wash station', severity: 'HIGH', confidence: 0.92, evidence_url: '/evidence/colour-station.jpg', control_measures: ['Install eye wash station', 'PPE available (gloves, apron)', 'COSHH assessment displayed'], regulatory_ref: 'COSHH Reg 7', status: 'OPEN' },
  { id: 3, assessment_id: 1, category: 'Fire Safety', description: 'Fire exit sign partially obscured by storage', severity: 'MEDIUM', confidence: 0.78, evidence_url: '/evidence/fire-exit.jpg', control_measures: ['Clear storage from exit route', 'Replace sign with illuminated version'], regulatory_ref: 'RRO Article 14', status: 'RESOLVED' },
  { id: 4, assessment_id: 2, category: 'Chemical Handling', description: 'Developer bottles stored above head height', severity: 'MEDIUM', confidence: 0.88, evidence_url: '/evidence/storage-high.jpg', control_measures: ['Relocate to lower shelf', 'Label shelves with weight limits'], regulatory_ref: 'COSHH Reg 7', status: 'RESOLVED' },
  { id: 5, assessment_id: 3, category: 'Fire Safety', description: 'Fire extinguisher service overdue by 2 months', severity: 'HIGH', confidence: 0.95, evidence_url: '/evidence/extinguisher.jpg', control_measures: ['Schedule immediate service', 'Set up annual reminder'], regulatory_ref: 'RRO Article 17', status: 'OPEN' },
]

// --- RAMS Documents ---
export const DEMO_RAMS: RAMSDocument[] = [
  { id: 1, title: 'Chemical Handling — Colour Services', version: '2.1', created_by: 'Jordan Riley', created_at: '2025-09-15T10:00:00Z', approved_by: 'Jordan Riley', status: 'APPROVED' },
  { id: 2, title: 'Manual Handling — Stock Deliveries', version: '1.0', created_by: 'Sam Kim', created_at: '2025-11-01T14:00:00Z', approved_by: null, status: 'DRAFT' },
]

// --- Compliance Score ---
export const DEMO_COMPLIANCE_SCORE: ComplianceScore = {
  overall: 78,
  categories: [
    { name: 'Fire Safety', score: 7, max: 10 },
    { name: 'Chemical Handling', score: 8, max: 10 },
    { name: 'Slips, Trips & Falls', score: 7, max: 10 },
    { name: 'Training Compliance', score: 9, max: 10 },
    { name: 'Documentation', score: 8, max: 10 },
    { name: 'Equipment Maintenance', score: 6, max: 10 },
    { name: 'Emergency Procedures', score: 8, max: 10 },
    { name: 'Incident Reporting', score: 9, max: 10 },
  ],
  overdue_actions: 2,
  upcoming_reviews: 1,
}

// --- Equipment ---
export const DEMO_EQUIPMENT: EquipmentItem[] = [
  { id: 1, name: 'Fire Extinguisher — Reception', location: 'Reception', category: 'Fire Safety', last_inspection: '2025-06-15', next_inspection: '2026-06-15', status: 'OVERDUE' },
  { id: 2, name: 'Fire Extinguisher — Kitchen', location: 'Staff Kitchen', category: 'Fire Safety', last_inspection: '2025-08-20', next_inspection: '2026-08-20', status: 'OK' },
  { id: 3, name: 'First Aid Kit', location: 'Reception', category: 'First Aid', last_inspection: '2026-01-10', next_inspection: '2026-04-10', status: 'OK' },
  { id: 4, name: 'PAT Testing — All Appliances', location: 'Whole Premises', category: 'Electrical', last_inspection: '2025-03-01', next_inspection: '2026-03-01', status: 'DUE_SOON' },
  { id: 5, name: 'Eye Wash Station', location: 'Colour Station', category: 'Chemical Safety', last_inspection: '2025-12-01', next_inspection: '2026-06-01', status: 'OK' },
]

// --- Schedule ---
export const DEMO_SCHEDULE: ScheduleDay[] = [
  { day: 'Monday', open: '09:00', close: '17:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Tuesday', open: '09:00', close: '17:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Wednesday', open: '09:00', close: '17:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Thursday', open: '09:00', close: '19:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Friday', open: '09:00', close: '18:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Saturday', open: '09:00', close: '16:00', closed: false, slot_duration_minutes: 30 },
  { day: 'Sunday', open: '', close: '', closed: true, slot_duration_minutes: 30 },
]

// --- Audit Log ---
export const DEMO_AUDIT_LOG: AuditEntry[] = [
  { id: 1, user_name: 'Jordan Riley', user_role: 'owner', action: 'UPDATE', entity_type: 'Service', entity_id: 1, details: 'Updated price from £30.00 to £35.00', timestamp: '2026-02-06T09:00:00Z', ip_address: '192.168.1.10' },
  { id: 2, user_name: 'Sam Kim', user_role: 'manager', action: 'APPROVE', entity_type: 'LeaveRequest', entity_id: 1, details: 'Approved annual leave for Jordan Riley (16-20 Mar)', timestamp: '2026-02-05T14:30:00Z', ip_address: '192.168.1.11' },
  { id: 3, user_name: 'Jordan Riley', user_role: 'owner', action: 'CREATE', entity_type: 'Incident', entity_id: 3, details: 'Reported: Client allergic reaction', timestamp: '2026-02-03T16:00:00Z', ip_address: '192.168.1.10' },
  { id: 4, user_name: 'Alex Taylor', user_role: 'staff', action: 'UPLOAD', entity_type: 'Document', entity_id: 4, details: 'Uploaded First Aid certificate', timestamp: '2026-02-06T14:20:00Z', ip_address: '192.168.1.12' },
  { id: 5, user_name: 'Morgan Patel', user_role: 'staff', action: 'CREATE', entity_type: 'LeaveRequest', entity_id: 3, details: 'Requested annual leave (10-11 Apr)', timestamp: '2026-02-07T08:00:00Z', ip_address: '192.168.1.13' },
]

// --- Helpers ---
export function formatPrice(pence: number, symbol = '£'): string {
  return `${symbol}${(pence / 100).toFixed(2)}`
}

export function generateDemoSlots(dateStr: string, serviceId: number) {
  const times = [
    { h: 9, m: '00' }, { h: 10, m: '00' }, { h: 11, m: '00' },
    { h: 12, m: '00' }, { h: 13, m: '30' }, { h: 14, m: '30' },
    { h: 15, m: '30' }, { h: 16, m: '30' },
  ]
  const svc = DEMO_SERVICES.find(s => s.id === serviceId)
  const dur = svc ? svc.duration_minutes : 45
  return times.map((t, i) => {
    const startMin = t.h * 60 + parseInt(t.m)
    const endMin = startMin + dur
    const endH = Math.floor(endMin / 60)
    const endM = endMin % 60
    return {
      id: i + 1,
      date: dateStr,
      start_time: `${String(t.h).padStart(2, '0')}:${t.m}:00`,
      end_time: `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}:00`,
      has_capacity: Math.random() > 0.15,
      max_bookings: 2,
    }
  })
}
