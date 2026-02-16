# Tenant Isolation — Micro-Loop Implementation Spec

## Objective
Add full tenant isolation to the NBNE Business Platform so each tenant (Salon X, Restaurant X, Health Club X, Mind Department, NBNE) has completely separate data. No data leaks between tenants. Each Vercel frontend passes `NEXT_PUBLIC_TENANT_SLUG` which the backend uses to scope all queries.

## Architecture

### Tenant Resolution
1. **Add `tenant` FK to `User`** — `ForeignKey(TenantSettings, null=True, on_delete=SET_NULL)`
2. **Tenant middleware** — for authenticated requests, set `request.tenant = request.user.tenant`. For unauthenticated, resolve from `X-Tenant-Slug` header (frontend proxy adds this from `NEXT_PUBLIC_TENANT_SLUG`).
3. **Frontend proxy** — add `X-Tenant-Slug` header to all proxied requests.

### Models Needing `tenant` FK
Root models that don't chain to a User and need direct tenant FK:

| App | Model | Notes |
|-----|-------|-------|
| bookings | Service | Root — no user FK |
| bookings | Staff (bookings app) | Root — no user FK |
| bookings | Client | Root — no user FK |
| bookings | Booking | Has client/staff FK but needs tenant for direct queries |
| staff | StaffProfile | Has user FK but needs tenant for list queries |
| comms | Channel | Root — no user FK |
| crm | Lead | Root — no user FK |
| documents | DocumentTag | Root — no user FK (make unique per tenant) |
| documents | Document | Has uploaded_by FK but needs tenant for list queries |
| compliance | ComplianceCategory | Root — no user FK |
| compliance | ComplianceItem | Has category FK but needs tenant for direct queries |
| compliance | IncidentReport | Has reported_by FK but needs tenant |
| compliance | RiskAssessment | Has created_by FK but needs tenant |
| compliance | Equipment | Root — no user FK |
| compliance | AccidentReport | Has reported_by FK but needs tenant |
| compliance | RAMSDocument | Has created_by FK but needs tenant |
| compliance | PeaceOfMindScore | Singleton per tenant |
| analytics | Recommendation | Root — no user FK |
| core | BusinessEvent | Has performed_by FK but needs tenant for dashboard |
| payments | Customer | Root — no user FK |
| payments | PaymentSession | Has customer FK but needs tenant |

### Models That DON'T Need tenant FK (chain via parent)
- `Shift` → via `StaffProfile.tenant`
- `LeaveRequest` → via `StaffProfile.tenant`
- `TrainingRecord` → via `StaffProfile.tenant`
- `WorkingHours` → via `StaffProfile.tenant`
- `TimesheetEntry` → via `StaffProfile.tenant`
- `AbsenceRecord` → via `StaffProfile.tenant`
- `ChannelMember` → via `Channel.tenant`
- `Message` → via `Channel.tenant`
- `MessageAttachment` → via `Message.channel.tenant`
- `IncidentPhoto` → via `IncidentReport.tenant`
- `SignOff` → via `IncidentReport.tenant`
- `HazardFinding` → via `RiskAssessment.tenant`
- `EquipmentInspection` → via `Equipment.tenant`
- `ScoreAuditLog` → via `PeaceOfMindScore.tenant`
- `IntakeProfile` → via `Client` (if we add tenant to Client)
- `IntakeWellbeingDisclaimer` → global (shared across tenants, or per-tenant)
- `ClassPackage`, `ClientCredit`, `PaymentTransaction` → via booking/client chain
- `PasswordToken` → via User.tenant
- `AuditLogEntry` → via User.tenant

## Implementation Loops

### Loop 1: User.tenant + Middleware
1. Add `tenant = ForeignKey(TenantSettings, null=True, blank=True, on_delete=SET_NULL)` to `accounts.User`
2. Create migration
3. Create `core/middleware_tenant.py`:
   - For authenticated requests: `request.tenant = request.user.tenant`
   - For unauthenticated: resolve from `X-Tenant-Slug` header
   - Fallback: first tenant (backward compat)
4. Add middleware to `MIDDLEWARE` in settings
5. Update `_get_role` to embed `tenant_slug` in JWT
6. Update frontend proxy to send `X-Tenant-Slug` header

### Loop 2: Root Model Migrations
1. Add `tenant = ForeignKey(TenantSettings, null=True, blank=True, on_delete=CASCADE)` to all root models listed above
2. Create migrations (one per app)
3. Write a data migration to assign existing records to the correct tenant (based on user relationships where possible, or default to first tenant)

### Loop 3: View Filtering — Bookings App
1. Update `ServiceViewSet.get_queryset()` to filter by `request.tenant`
2. Update `StaffViewSet.get_queryset()` to filter by `request.tenant`
3. Update `BookingViewSet.get_queryset()` to filter by `request.tenant`
4. Update `ClientViewSet.get_queryset()` to filter by `request.tenant`
5. Update all `perform_create` methods to set `tenant=request.tenant`
6. Update dashboard, reports, demo views

### Loop 4: View Filtering — Staff Module
1. Update `staff_list` to filter by `request.tenant`
2. Update `staff_create` to set `tenant` on StaffProfile and User
3. Update `staff_update`, `staff_delete` to scope by tenant
4. Update shift, leave, training, working hours, timesheet views

### Loop 5: View Filtering — Other Modules
1. Comms: filter channels by tenant
2. CRM: filter leads by tenant
3. Documents: filter by tenant
4. Compliance: filter all by tenant
5. Analytics: filter recommendations by tenant
6. Core: filter BusinessEvents by tenant
7. Payments: filter by tenant

### Loop 6: Seed Update
1. Create per-tenant users with unique usernames (e.g. `salon-x-owner`, `salon-x-manager`)
2. Assign `user.tenant` on creation
3. Set `tenant` on all seeded models
4. Remove shared demo users pattern

### Loop 7: Frontend Proxy Update
1. Add `X-Tenant-Slug` header from `NEXT_PUBLIC_TENANT_SLUG` env var to proxy requests
2. Ensure auth route also sends tenant slug

### Loop 8: Testing & Verification
1. Run migrations locally
2. Run seed locally
3. Verify tenant isolation: login as salon-x owner, confirm only salon-x data visible
4. Verify NBNE data separate
5. Build frontend, push, verify on Vercel

## Railway Storage Volume
Separate from tenant isolation:
1. Add a Railway volume mounted at `/data/media`
2. Set `MEDIA_ROOT=/data/media` in Django settings
3. Documents, chat attachments, compliance photos stored there
4. Persistent across deploys

## Nightly Reset (Future)
- Railway cron job: `python manage.py seed_demo --tenant=salon-x` at 03:00 UTC
- Only resets demo tenants, not NBNE (real data)
