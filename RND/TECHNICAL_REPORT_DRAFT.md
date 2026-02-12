# R&D Technical Report — Rev 2: Three-Tier Platform with AI Compliance Engine

## 1. Introduction

This revision advances the NBNE business platform from a flat admin/customer split to a
three-tier architecture with role-based access control, real-time communications, and an
AI-driven health & safety compliance engine.

## 2. Multi-Tier Design

### 2.1 Uncertainty
The primary technical uncertainty is whether a single Next.js application can cleanly
serve three distinct user experiences (public, staff, admin) while maintaining strict
data isolation. The risk is UI bleed — staff components appearing in public routes or
admin data leaking to staff views.

### 2.2 Approach
- Route groups: `(public)`, `(staff)`, `(admin)` with separate layouts
- Middleware-based role gating at the route level
- API endpoints scoped by role with server-side enforcement
- Shared auth context but role-filtered navigation

### 2.3 Challenges
- Session management across tiers (single JWT with role claims)
- Middleware performance with role checks on every request
- Component reuse without leaking tier-specific logic

## 3. Access Control

### 3.1 Uncertainty
Implementing RBAC that is both flexible enough for different business types and strict
enough to prevent privilege escalation.

### 3.2 Approach
- Four roles: customer, staff, manager, owner
- Permission matrix defined per module per role
- Server-side queryset filtering (never trust frontend)
- Automated tests for every endpoint × role combination

### 3.3 Challenges
- Role hierarchy (owner > manager > staff > customer)
- Per-client role customisation
- Audit trail without performance degradation

## 4. Real-Time Chat System

### 4.1 Uncertainty
Whether WebSocket-based real-time messaging can be reliably deployed on Railway/Vercel
infrastructure without dedicated WebSocket servers.

### 4.2 Approach
- Server-Sent Events (SSE) as fallback for environments without WebSocket
- Channel-based architecture (general, team, direct messages)
- Optimistic UI updates with server reconciliation
- Typing indicators, read receipts, online presence

### 4.3 Reference: ChatPlus
Key features to incorporate:
- Real-time message delivery
- Typing and recording indicators
- Image drag-and-drop sharing
- Audio messages with speech-to-text
- Unread message counts
- Message seen status
- Scroll-to-bottom with unread indicator

## 5. AI Health & Safety Engine

### 5.1 Uncertainty
Whether AI vision models can reliably detect workplace hazards from mobile-captured
images with sufficient accuracy for compliance purposes.

### 5.2 Approach
- Guided capture workflow (sector-specific prompts)
- OpenAI Vision API for hazard detection
- Regulatory reasoning layer mapping to UK HSE frameworks
- Automated risk assessment and RAMS document generation
- Risk-to-training mapping

### 5.3 Regulatory Constraints
- AI outputs framed as decision-support, not definitive compliance
- Competent person sign-off required
- Confidence scoring on all findings
- Clear disclaimers on generated documents

### 5.4 Solutions Attempted
- Structured prompts for consistent hazard categorisation
- Severity × likelihood risk matrix
- Template-based document generation with editable outputs
- Evidence linking (annotated images → findings → actions)

## 6. Demo Client Validation

Three exemplar businesses validate the platform:

| Client | Sector | Modules |
|--------|--------|---------|
| Salon X | Hair salon | Bookings, Payments, Staff, Comms, Analytics |
| Vitality Health Club | Fitness | Bookings, Payments, Staff, Comms, Compliance, Documents, Analytics |
| The Kitchen Table | Restaurant | Bookings, Staff, CRM, Analytics |

Each must demonstrate:
- Correct tier separation
- Role-appropriate navigation
- No data leaks between tiers
- Sector-specific branding

## 7. Deployment Architecture

- Frontend: Vercel (Next.js SSR + static)
- Backend API: Railway (Django REST + WebSocket)
- Database: Railway PostgreSQL
- File storage: Railway volume or S3
- Secrets: Per-tier environment variables

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket not supported on hosting | Chat degraded | SSE fallback |
| AI vision accuracy insufficient | HSE findings unreliable | Human-in-the-loop validation |
| RBAC complexity slows development | Delayed delivery | Permission matrix generator |
| Three UIs to maintain | Maintenance burden | Shared component library |
| Regulatory changes | HSE module outdated | Configurable rule engine |

## 9. Iteration Log

### Iteration 1 — Frontend Scaffold (2026-02-08)

**Completed:**
- Next.js 14 project with TypeScript, ESLint, path aliases
- JWT-based auth with cookie sessions and demo user authentication
- Middleware enforcing RBAC on `/app/*` (staff+) and `/admin/*` (manager/owner)
- Three-tier UI shell:
  - **Tier 1 (Public):** Service listing, date/time picker, booking form with confirmation
  - **Tier 2 (Staff):** Dashboard, shifts, leave, training, documents, team chat, HSE compliance
  - **Tier 3 (Admin):** Dashboard, bookings, services (editable), staff management, schedule (editable), CRM, team chat, HSE (full access), document vault, analytics, audit log, settings
- ChatPlus-inspired chat with channels, typing indicators, read receipts, auto-replies
- HSE compliance dashboard with score circle, category bars, tabbed views (assessments, findings, equipment, incidents, RAMS)
- Comprehensive demo data covering all modules with interconnected records
- Global CSS design system with variables, responsive grid, cards, badges, tables, modals, tabs
- Production build passes cleanly (25 pages, 0 errors)

**Findings:**
- Single Next.js app successfully serves three distinct UIs via route-based separation
- Middleware role gating adds negligible latency (~2ms per request)
- CSS-only design system avoids Tailwind dependency while maintaining consistency
- Demo data as first-class module enables offline development and testing

**Next Steps:**
- Backend API integration (Django REST) ✅ (see Iteration 2)
- WebSocket/SSE for real-time chat
- AI vision integration for HSE hazard detection
- Demo client branding (Salon X, Vitality, Kitchen Table)

### Iteration 2 — Backend API Integration (2026-02-08)

**Completed:**
- Django 4.2 project with custom User model (`accounts.User`) and 4-role RBAC
- JWT authentication via `djangorestframework-simplejwt` with role/tier claims in tokens
- RBAC permission classes: `IsOwner`, `IsManagerOrAbove`, `IsStaffOrAbove`, `role_required()`
- Audit log module with auto-logging middleware (captures all write operations + logins)
- All 9 optional modules ported from master-blank with RBAC enforcement:
  - **tenants** — public read, owner-only write
  - **bookings** — public service/slot listing, staff+ booking management, server-side deposit calc
  - **payments** — Stripe checkout + webhook integration (unchanged from master-blank)
  - **staff** — staff see own data, managers see all, managers create shifts/training/absence
  - **comms** — staff+ channel access, managers see all channels
  - **compliance** — staff+ incident reporting, manager+ status changes and sign-offs
  - **documents** — tier-based access filtering (customer/staff/manager/owner)
  - **crm** — manager+ only (leads, notes, follow-ups, CSV export)
  - **analytics** — manager+ cross-module dashboard with recommendation engine
- SQLite for dev (PostgreSQL-ready via `dj-database-url`)
- `seed_demo` management command populating all modules with interconnected demo data
- API smoke test: 17/17 endpoints passing, RBAC verified (staff blocked from CRM)

**Findings:**
- Custom User model with role field is cleaner than separate StaffProfile roles
- JWT claims (role, tier, name) enable frontend to make UI decisions without extra API calls
- Audit middleware auto-captures 90%+ of significant actions without per-view code
- SQLite sufficient for demo/dev; PostgreSQL swap is a single env var change

**Next Steps:**
- Wire frontend to consume Django API instead of demo data ✅ (see Iteration 3)
- WebSocket/SSE for real-time chat
- AI vision integration for HSE hazard detection

### Iteration 3 — UK Health & Safety Compliance Module (2026-02-12)

**Completed (9 phases):**

1. **Data Models** — 5 new models with tenant isolation patterns:
   - `ComplianceCategory` — grouping layer with `legal_requirement` flag for statutory vs best-practice
   - `ComplianceItem` — core scheduling unit with 9 frequency types (weekly → 5-year + custom), auto-calculated `next_due_date`, RAG status engine
   - `TrainingRecord` — per-user certificate tracking with expiry, provider, certificate number
   - `DocumentVault` — version-chained document storage with `supersedes` FK, `is_current` flag, expiry tracking
   - `ComplianceActionLog` — unified compliance audit trail (created, completed, status_changed, reminder_sent)
   - Extended `IncidentReport` with UK RIDDOR fields (`injury_type`, `riddor_reportable`, `riddor_reference`, `body_part_injured`, `first_aid_given`, `witnesses`)

2. **Scheduling Engine** — `update_compliance_status` management command:
   - Deterministic status transitions: overdue (past due), due_soon (≤30 days), compliant (>30 days)
   - Training expiry detection with auto-status update
   - Dry-run mode for safe preview
   - Designed for daily cron execution

3. **DRF API Layer** — 20+ endpoints with strict RBAC:
   - **Tier 2 (Staff):** incident reporting, own training view, assigned actions
   - **Tier 3 (Manager/Owner):** full CRUD, dashboard with compliance score, calendar feed, CSV export, document vault, training management, action logs
   - Dashboard computes per-category compliance percentages and overall score
   - Calendar merges compliance items, training expiry, and document expiry into unified timeline

4. **Frontend** — Live API HSE page replacing demo data:
   - 8 tabs: Dashboard, Register, Training, Documents, Incidents, Calendar, RAMS, Audit Log
   - RAG colour coding (green ≥80%, amber ≥60%, red <60%)
   - Compliance score circle with per-category progress bars
   - Incident reporting form with RIDDOR fields, severity, injury type
   - Status filter buttons on compliance register
   - CSV export link

5. **UK Baseline Template** — `seed_uk_baseline` command:
   - 6 categories: Fire Safety, Electrical Safety, Training, General Compliance, Equipment, Hygiene & Welfare
   - 15 items with UK-specific frequencies and legal references (BS 5839-1, BS 7671, EICR, PAT, COSHH, RIDDOR 2013)
   - Idempotent (safe to re-run)

6. **Email Reminders** — `send_compliance_reminders` command:
   - Threshold triggers at 30, 7, 1 days before due + daily for overdue
   - Training expiry reminders at 30, 7, 1 days
   - Legal requirement items flagged with regulatory consequence warning
   - Dry-run mode

7. **Audit & Security:**
   - `ComplianceActionLog` entries on all create/update/complete/status-change operations
   - Document versioning with `upload_new_version()` method (marks old as non-current)
   - RBAC enforced server-side on every endpoint
   - Audit middleware updated to recognise new compliance entity types

8. **R&D Log** — `RND/logs/compliance_module_iteration.md`:
   - Architecture decisions documented
   - UK regulation interpretation uncertainties (RIDDOR auto-submission, PAT frequency, status thresholds)
   - Known limitations (no tenant FK, no offline drafts, no file upload UI, list-based calendar)
   - Next improvements prioritised

9. **Testing** — 32 tests, all passing:
   - Model logic: frequency calculation, status transitions, mark_completed, auto-save next_due
   - Training: expired/expiring_soon/valid status properties
   - Document vault: version chaining, is_current flag management
   - RBAC: 13 endpoint × role tests (customer/staff/manager/owner)
   - Action logging: creation, completion, incident logging verified
   - Baseline seed: idempotency, minimum count verification

**Findings:**
- Frequency-based scheduling with auto-calculated next_due_date eliminates manual diary management — the system perpetually cycles compliance items
- 30-day "due soon" threshold works well for annual/3-year items but causes near-immediate alerts for weekly items (fire alarm tests) — proportional thresholds needed
- RIDDOR flag-only approach is correct; auto-submission to HSE carries legal liability and requires their API integration
- Document version chaining via `supersedes` FK is simpler than a separate version table and avoids orphan cleanup
- UK baseline seed provides immediate value on tenant creation — new businesses get a compliant starting point without manual setup
- ComplianceActionLog separate from platform AuditEntry allows compliance-specific filtering and reporting without polluting the general audit trail

**Uncertainties Resolved:**
- ✅ Single Django app can serve both staff and manager compliance views via RBAC permission classes
- ✅ Scheduling engine handles all UK standard frequencies (weekly fire tests through 5-year EICR)
- ✅ Frontend can display live compliance data with RAG indicators using existing CSS design system

**Uncertainties Remaining:**
- ❓ Whether proportional reminder thresholds (scaled to frequency) reduce alert fatigue for weekly items
- ❓ Whether PWA push notifications (via existing comms PushSubscription) improve compliance completion rates vs email-only
- ❓ Whether AI vision can reliably detect compliance gaps from workplace photos (Phase 5.2 of original plan)
- ❓ Multi-tenant-per-database isolation — current approach uses infrastructure isolation (one Railway instance per tenant)

**Next Steps:**
- PWA push notifications for compliance reminders
- Visual calendar component (FullCalendar or similar)
- File upload UI for documents and training certificates
- AI vision hazard detection integration
- Offline incident draft capability (IndexedDB + service worker sync)
