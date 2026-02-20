# NBNE Business Platform — Project Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Backend Structure](#backend-structure)
4. [Frontend Structure](#frontend-structure)
5. [Multi-Tenancy](#multi-tenancy)
6. [Module System](#module-system)
7. [Business Type Presets](#business-type-presets)
8. [Authentication & Authorization](#authentication--authorization)
9. [Booking Engine](#booking-engine)
10. [Availability Engine](#availability-engine)
11. [Payments Integration](#payments-integration)
12. [Staff Module](#staff-module)
13. [Communications (Comms)](#communications-comms)
14. [Compliance & Health/Safety](#compliance--healthsafety)
15. [Documents](#documents)
16. [CRM](#crm)
17. [Analytics](#analytics)
18. [Seed Data & Demo Sites](#seed-data--demo-sites)
19. [Deployment](#deployment)
20. [Environment Variables](#environment-variables)
21. [API Reference](#api-reference)
22. [Management Commands](#management-commands)
23. [Known Limitations & Future Work](#known-limitations--future-work)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Vercel (Frontend)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Salon X  │  │ Tavola   │  │ FitHub   │  │ NBNE     │     │
│  │ salon-x  │  │ rest-x   │  │ health-x │  │ nbne     │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       └──────────────┼──────────────┼──────────────┘          │
└──────────────────────┼──────────────┼─────────────────────────┘
                       │              │
              ┌────────▼──────────────▼────────┐
              │     Railway (Backend)           │
              │  Django REST Framework          │
              │  PostgreSQL                     │
              │  Gunicorn + WhiteNoise          │
              │  Background workers             │
              └────────────────────────────────┘
```

- **1 shared Django backend** on Railway — all modules enabled, all tenants in one DB
- **N Vercel frontends** — same Next.js codebase, different `NEXT_PUBLIC_TENANT_SLUG` env var
- Tenant resolution via `X-Tenant-Slug` header (injected by frontend API proxy)
- Media files stored locally or via Cloudflare R2 (S3-compatible)

---

## Tech Stack

### Backend
- **Python 3.11+** / **Django 5.2**
- **Django REST Framework** — API layer
- **SimpleJWT** — JWT authentication
- **dj-database-url** — DATABASE_URL parsing for Railway
- **WhiteNoise** — static file serving
- **Gunicorn** — WSGI server
- **PostgreSQL** — database
- **django-storages + boto3** — R2/S3 media storage (optional)
- **django-cors-headers** — CORS

### Frontend
- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- Inline styles (no Tailwind — design tokens in components)
- No component library — custom UI throughout

---

## Backend Structure

```
backend/
├── accounts/          # Custom User model, auth URLs
├── analytics/         # Analytics dashboard API
├── auditlog/          # Audit trail for admin actions
├── bookings/          # Core booking engine
│   ├── models.py              # Service, Staff, Client, Booking, Session
│   ├── models_availability.py # WorkingPattern, Shifts, Leave, Timesheets
│   ├── models_restaurant.py   # Table, ServiceWindow
│   ├── models_gym.py          # ClassType, ClassSession
│   ├── models_intake.py       # IntakeProfile, Disclaimer
│   ├── models_payment.py      # ClassPackage, ClientCredit, PaymentTransaction
│   ├── api_views.py           # CRUD viewsets
│   ├── api_urls.py            # Router (includes restaurant + gym endpoints)
│   ├── views_restaurant.py    # Restaurant availability API
│   ├── views_gym.py           # Gym timetable API
│   ├── views_availability.py  # Availability engine API
│   ├── views_reports.py       # Reporting endpoints
│   ├── views_stripe.py        # Stripe checkout + webhook
│   └── availability.py        # Slot generation logic
├── comms/             # Team chat (channels, messages)
├── compliance/        # H&S incidents, RAMS documents
├── config/            # Django settings, URLs, WSGI
├── core/              # Auth views, dashboard, command bar, tenant middleware
├── crm/               # Lead management
├── documents/         # Document vault
├── payments/          # Stripe integration module
├── staff/             # Staff profiles, shifts, leave, timesheets, working hours
├── tenants/           # TenantSettings model, serializers, middleware
├── start.sh           # Railway entrypoint (migrate, seed, start gunicorn)
├── Procfile           # Railway process definition
└── requirements.txt   # Python dependencies
```

---

## Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx               # Homepage router (Salon/Restaurant/Gym/NBNE landing)
│   ├── admin/                 # Admin panel
│   │   ├── layout.tsx         # Sidebar + topbar (filters by module + business_type)
│   │   ├── page.tsx           # Dashboard
│   │   ├── bookings/          # Booking management
│   │   ├── services/          # Service CRUD
│   │   ├── staff/             # Staff management (shifts, leave, training)
│   │   ├── clients/           # CRM leads
│   │   ├── reports/           # Revenue & staff reports
│   │   ├── analytics/         # Analytics dashboard
│   │   ├── chat/              # Team chat
│   │   ├── health-safety/     # Compliance (incidents, RAMS, training)
│   │   ├── documents/         # Document vault
│   │   ├── settings/          # Tenant settings editor
│   │   ├── tables/            # Restaurant: table management
│   │   ├── service-windows/   # Restaurant: service window management
│   │   ├── class-types/       # Gym: class type management
│   │   ├── timetable/         # Gym: weekly timetable management
│   │   └── audit/             # Audit log viewer
│   ├── book/                  # Public booking page
│   │   ├── page.tsx           # Booking flow router (salon/restaurant/gym)
│   │   ├── RestaurantBookingFlow.tsx
│   │   └── GymBookingFlow.tsx
│   ├── login/                 # Login page
│   ├── app/                   # Staff portal
│   └── api/                   # Next.js API routes (auth proxy, django proxy)
├── lib/
│   ├── api.ts                 # All API functions (100+ exports)
│   ├── tenant.tsx             # TenantContext, TenantProvider, useTenant()
│   └── auth.ts                # Token management, cookie helpers
├── components/
│   └── CommandBar.tsx         # Global command bar (Ctrl+K)
└── middleware.ts              # RBAC route protection
```

---

## Multi-Tenancy

### How It Works

1. Each Vercel frontend sets `NEXT_PUBLIC_TENANT_SLUG` (e.g. `salon-x`)
2. Frontend API proxy at `/api/django/[...path]` injects `X-Tenant-Slug` header
3. Django middleware (`core/middleware.py`) reads the header and attaches `request.tenant`
4. All querysets filter by `tenant=request.tenant`
5. All creates set `tenant=request.tenant`

### TenantSettings Model

`backend/tenants/models.py` — one row per tenant:

| Field | Purpose |
|-------|---------|
| `slug` | URL-safe identifier (PK for routing) |
| `business_type` | `salon` / `restaurant` / `gym` / `generic` |
| `business_name` | Display name |
| `enabled_modules` | JSON list of enabled module names |
| `colour_primary/secondary/accent/background/text` | Branding colours |
| `font_heading/body/url` | Custom fonts |
| `logo_url`, `favicon_url` | Branding assets |
| `email`, `phone`, `address` | Contact info |
| `booking_staff_label/plural` | e.g. "Stylist"/"Stylists" |
| `booking_lead_time_hours`, `booking_max_advance_days` | Booking policies |
| `deposit_percentage`, `currency`, `currency_symbol` | Payment config |
| `pwa_theme_colour`, `pwa_background_colour`, `pwa_short_name` | PWA manifest |

### Frontend Tenant Context

`frontend/lib/tenant.tsx` provides:
- `TenantProvider` — fetches branding on mount, applies CSS vars
- `useTenant()` — returns `TenantConfig` object
- `hasModule(tenant, 'bookings')` — checks if module is enabled

---

## Module System

Modules are feature-flagged at two levels:

### Backend (Django settings)
```
BOOKINGS_MODULE_ENABLED=True
PAYMENTS_MODULE_ENABLED=True
STAFF_MODULE_ENABLED=True
COMMS_MODULE_ENABLED=True
COMPLIANCE_MODULE_ENABLED=True
DOCUMENTS_MODULE_ENABLED=True
CRM_MODULE_ENABLED=True
ANALYTICS_MODULE_ENABLED=True
TENANTS_MODULE_ENABLED=True
```

URL patterns are conditionally included in `config/urls.py`.

### Frontend (per-tenant)
`TenantSettings.enabled_modules` is a JSON list. The admin sidebar (`admin/layout.tsx`) filters nav items:
```typescript
const visibleNav = NAV_ITEMS.filter(item => {
  if (item.module !== '_always' && !hasModule(tenant, item.module)) return false
  if ('businessType' in item && item.businessType !== tenant.business_type) return false
  return true
})
```

### Module Matrix (Demo Sites)

| Module | Salon X | Tavola | FitHub | Mind Dept | NBNE |
|--------|---------|--------|--------|-----------|------|
| bookings | ✅ | ✅ | ✅ | ✅ | ✅ |
| payments | ✅ | ✅ | ✅ | ✅ | ✅ |
| staff | ✅ | ✅ | ✅ | ✅ | ✅ |
| comms | ✅ | ✅ | ✅ | ❌ | ✅ |
| compliance | ✅ | ✅ | ✅ | ❌ | ✅ |
| documents | ✅ | ✅ | ✅ | ❌ | ✅ |
| crm | ✅ | ✅ | ✅ | ❌ | ✅ |
| analytics | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## Business Type Presets

Added in Wiggum Loop 9. The `business_type` field on `TenantSettings` controls:

### Booking Flow Routing (`/book`)

| Type | Flow | Steps |
|------|------|-------|
| `salon` / `generic` | Original flow | Service → Staff → Date → Time → Details |
| `restaurant` | `RestaurantBookingFlow.tsx` | Party Size → Date → Time Window → Details |
| `gym` | `GymBookingFlow.tsx` | Browse Timetable → Pick Session → Details |

Router in `frontend/app/book/page.tsx`:
```typescript
function BookingFlowRouter() {
  const tenant = useTenant()
  switch (tenant.business_type) {
    case 'restaurant': return <RestaurantBookingFlow />
    case 'gym': return <GymBookingFlow />
    default: return <BookPageInner />  // salon/generic
  }
}
```

### Admin Sidebar

Business-type-specific nav items appear only for matching tenants:
- **Restaurant**: Tables, Service Windows
- **Gym**: Class Types, Timetable

### Restaurant Models

- **`Table`** — name, min/max seats, zone, combinable flag
- **`ServiceWindow`** — name, day_of_week, open/close/last_booking times, turn_time_minutes, max_covers

API endpoints:
- `GET/POST /api/tables/` — CRUD
- `GET/POST /api/service-windows/` — CRUD
- `GET /api/restaurant-availability/?date=YYYY-MM-DD&party_size=N` — slot availability
- `GET /api/restaurant-available-dates/?party_size=N&weeks=4` — available dates

### Gym Models

- **`ClassType`** — name, category, duration, difficulty, max_capacity, colour, price_pence
- **`ClassSession`** — class_type FK, instructor FK, day_of_week, start/end time, room, override_capacity

API endpoints:
- `GET/POST /api/class-types/` — CRUD
- `GET/POST /api/class-sessions/` — CRUD
- `GET /api/gym-timetable/?date=YYYY-MM-DD` — weekly timetable with booking counts
- `GET /api/gym-class-types/` — public list of active class types

---

## Authentication & Authorization

### JWT Flow
1. `POST /api/auth/login/` — returns `{ access, refresh, user }`
2. Access token stored in localStorage + httpOnly cookie
3. Frontend sends `Authorization: Bearer <token>` on API calls
4. Token refresh via `POST /api/auth/token/refresh/`

### User Model
Custom user at `accounts/models.py`:
- `role`: `owner` / `manager` / `staff` / `customer`
- `tenant`: FK to TenantSettings
- `must_change_password`: forces password change on first login

### Frontend Middleware
`frontend/middleware.ts` checks the httpOnly cookie and redirects:
- `/admin/*` → requires `owner` or `manager` role
- `/app/*` → requires any authenticated user
- `/login` → redirects to `/admin` if already authenticated

### Password Reset
- `POST /api/auth/password-reset/` — sends reset email
- `GET /api/auth/validate-token/?token=xxx` — validates token
- `POST /api/auth/set-password-token/` — sets new password

---

## Booking Engine

### Core Models (`bookings/models.py`)

- **Service** — name, category, duration, price, deposit, payment_type, demand_index
- **Staff** — name, email, role, services M2M, break times, photo_url
- **Client** — name, email, phone
- **Booking** — client, service, staff, start/end time, status, payment fields, party_size (restaurant), table FK (restaurant)
- **Session** — group sessions (classes, workshops)

### Booking Statuses
`pending` → `confirmed` → `completed` / `cancelled` / `no_show`

### Smart Booking Engine (SBE)
Risk scoring on bookings:
- `risk_score`, `risk_level` (LOW/MEDIUM/HIGH/CRITICAL)
- `revenue_at_risk`, `recommended_payment_type`
- `recommended_deposit_percent`, `recommended_incentive`
- `optimisation_snapshot` — JSON blob of input metrics

### Service Intelligence
- `demand_index` — normalised 0-100 demand score
- `peak_time_multiplier`, `off_peak_discount_allowed`
- `avg_booking_value`, `cancellation_rate`, `no_show_rate`

---

## Availability Engine

`bookings/models_availability.py`:

- **WorkingPattern** — named pattern (e.g. "Full Time", "Part Time")
- **WorkingPatternRule** — day_of_week, start/end time, linked to pattern
- **AvailabilityOverride** — date-specific overrides (available/unavailable)
- **LeaveRequest** — staff leave with approval workflow
- **BlockedTime** — ad-hoc blocked periods
- **Shift** — actual worked shifts
- **TimesheetEntry** — timesheet records with approval

API:
- `GET /api/availability/?staff_id=N&date=YYYY-MM-DD` — staff availability
- `GET /api/availability/slots/?staff_id=N&service_id=N&date=YYYY-MM-DD` — free slots

---

## Payments Integration

Stripe integration via `payments/` app:

- `POST /api/checkout/create/` — creates Stripe Checkout session
- `POST /api/checkout/webhook/` — Stripe webhook handler
- Service model has `deposit_pence` field
- Booking model has `payment_status`, `payment_id`, `payment_amount`

Feature flags: `PAYMENTS_MODULE_ENABLED`, plus `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`.

---

## Staff Module

`staff/` app — HR management:

- **StaffProfile** — display_name, phone, role, department, hire_date
- **Shift** — date, start/end time, location, notes
- **LeaveRequest** — type (annual/sick/etc), dates, approval status
- **TrainingRecord** — course, date, expiry, certificate
- **WorkingHours** — weekly pattern per staff
- **ProjectCode** — for timesheet categorisation
- **TimesheetEntry** — date, hours, project code, approval

Admin pages: Staff list, shift calendar, leave calendar, training tracker, timesheets.

---

## Communications (Comms)

`comms/` app — team messaging:

- **Channel** — name, type (GENERAL/TEAM/DIRECT), tenant FK
- **ChannelMember** — user + channel link
- **Message** — content, sender, channel, timestamp

Frontend: Real-time-ish chat UI at `/admin/chat`.

---

## Compliance & Health/Safety

`compliance/` app:

- **IncidentReport** — date, type, severity, description, actions taken
- **RAMSDocument** — Risk Assessment & Method Statement documents

Frontend: `/admin/health-safety/` with sub-pages for incidents, documents, register, training.

---

## Documents

`documents/` app — document vault:

- **DocumentTag** — categorisation tags
- Upload/download with R2 or local storage
- Frontend: `/admin/documents`

---

## CRM

`crm/` app — lead management:

- **Lead** — name, email, phone, source, status, notes, client FK
- Status pipeline: NEW → CONTACTED → QUALIFIED → CONVERTED / LOST
- Frontend: `/admin/clients` with lead list, filters, side panel

---

## Analytics

`analytics/` app:

- Dashboard summary endpoint
- Revenue tracking, booking trends
- Frontend: `/admin/analytics`

---

## Seed Data & Demo Sites

### Management Command

```bash
python manage.py seed_demo                    # Seed all tenants
python manage.py seed_demo --tenant salon-x   # Seed one tenant
python manage.py seed_demo --delete-demo      # Delete all demo data
python manage.py seed_demo --tenant salon-x --delete-demo  # Delete one
```

### Demo Tenants

| Slug | Business | Type | Staff Label |
|------|----------|------|-------------|
| `salon-x` | Salon X | `salon` | Stylist |
| `restaurant-x` | Tavola | `restaurant` | Host |
| `health-club-x` | FitHub | `gym` | Trainer |
| `mind-department` | The Mind Department | `generic` | Practitioner |
| `nbne` | NBNE | `generic` | Consultant |

### What Gets Seeded

Per tenant:
- TenantSettings (branding, modules, business_type)
- 4 demo users (owner, manager, staff1, staff2, customer)
- Services (6-18 per tenant)
- Booking staff (3-4 per tenant)
- Demo clients (10-15 per tenant)
- 90 days of historic bookings + 14 days future
- Staff profiles, shifts, leave, training
- Comms channels
- Compliance data
- CRM leads
- **Restaurant-only**: 10 tables, 12 service windows (Tavola)
- **Gym-only**: 6 class types, 27 weekly sessions (FitHub)

### Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| `{slug}-owner` | `admin123` | Owner |
| `{slug}-manager` | `admin123` | Manager |
| `{slug}-staff1` | `admin123` | Staff |
| `{slug}-customer` | `admin123` | Customer |

---

## Deployment

### Backend (Railway)

1. Railway auto-deploys from `main` branch
2. `start.sh` runs on every deploy:
   - `python manage.py migrate --noinput`
   - `python manage.py collectstatic --noinput`
   - If `SEED_TENANT` is set: delete + re-seed demo data
   - `python manage.py setup_production`
   - `python manage.py seed_compliance`
   - `python manage.py seed_document_vault`
   - `python manage.py sync_crm_leads`
   - `python manage.py update_demand_index`
   - `python manage.py backfill_sbe_scores`
   - Start booking reminder worker (background)
   - Start Gunicorn

### Frontend (Vercel)

Each tenant gets its own Vercel project:
- Same repo, same `frontend/` root directory
- Different `NEXT_PUBLIC_TENANT_SLUG` env var
- Auto-deploys on push to `main`

### New Client Deployment

Use `scripts/deploy_client.ps1`:
```powershell
.\scripts\deploy_client.ps1 -ClientName "My Salon" -TenantSlug "my-salon"
```

This creates a Railway project, Postgres, sets env vars, and seeds data.

---

## Environment Variables

### Backend (Railway)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Auto-set by Railway Postgres |
| `DJANGO_SECRET_KEY` | Yes | Random secret key |
| `DEBUG` | No | `False` in production |
| `ALLOWED_HOSTS` | Yes | `.up.railway.app,localhost` |
| `CORS_ALLOWED_ORIGINS` | Yes | Comma-separated Vercel URLs |
| `CSRF_TRUSTED_ORIGINS` | Yes | Same as CORS |
| `SEED_TENANT` | No | Tenant slug to auto-seed on deploy |
| `STRIPE_SECRET_KEY` | No | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `EMAIL_HOST` | No | SMTP host (default: smtp.ionos.co.uk) |
| `EMAIL_HOST_USER` | No | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | SMTP password |
| `R2_ACCESS_KEY_ID` | No | Cloudflare R2 access key |
| `R2_SECRET_ACCESS_KEY` | No | Cloudflare R2 secret |
| `R2_ENDPOINT_URL` | No | R2 S3 endpoint |
| `R2_PUBLIC_URL` | No | R2 public URL |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_TENANT_SLUG` | Yes | Tenant identifier (e.g. `salon-x`) |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Railway backend URL |
| `DJANGO_BACKEND_URL` | Yes | Same as above (for server-side) |

---

## API Reference

### Auth
- `POST /api/auth/login/` — JWT login
- `GET /api/auth/me/` — current user
- `POST /api/auth/me/set-password/` — change password
- `POST /api/auth/password-reset/` — request reset email
- `POST /api/auth/set-password-token/` — reset with token
- `POST /api/auth/invite/` — send staff invite email

### Tenant
- `GET /api/tenant/branding/` — public branding config
- `GET /api/tenant/` — full tenant settings (authenticated)
- `PATCH /api/tenant/` — update tenant settings

### Bookings
- `GET/POST /api/services/` — service CRUD
- `GET/POST /api/staff/` — booking staff CRUD
- `GET/POST /api/clients/` — client CRUD
- `GET/POST /api/bookings/` — booking CRUD
- `POST /api/bookings/{id}/confirm/` — confirm booking
- `POST /api/bookings/{id}/cancel/` — cancel booking
- `POST /api/bookings/{id}/complete/` — complete booking
- `GET /api/bookings/slots/` — available time slots
- `GET /api/availability/` — staff availability
- `GET /api/availability/slots/` — free slots for staff+service+date

### Restaurant
- `GET/POST /api/tables/` — table CRUD
- `GET/POST /api/service-windows/` — service window CRUD
- `GET /api/restaurant-availability/?date=&party_size=` — slot availability
- `GET /api/restaurant-available-dates/?party_size=&weeks=` — date list

### Gym
- `GET/POST /api/class-types/` — class type CRUD
- `GET/POST /api/class-sessions/` — timetable session CRUD
- `GET /api/gym-timetable/?date=` — weekly timetable with spots
- `GET /api/gym-class-types/` — public class type list

### Reports
- `GET /api/reports/overview/`
- `GET /api/reports/daily/`
- `GET /api/reports/monthly/`
- `GET /api/reports/staff/`
- `GET /api/reports/insights/`
- `GET /api/reports/staff-hours/`
- `GET /api/reports/leave/`

### Payments
- `POST /api/checkout/create/` — Stripe checkout session
- `POST /api/checkout/webhook/` — Stripe webhook

### Staff Module
- `GET/POST /api/staff-module/profiles/`
- `GET/POST /api/staff-module/shifts/`
- `GET/POST /api/staff-module/leave/`
- `GET/POST /api/staff-module/training/`

### Comms
- `GET/POST /api/comms/channels/`
- `GET/POST /api/comms/messages/`

### CRM
- `GET/POST /api/crm/leads/`

### Documents
- `GET/POST /api/documents/`

---

## Management Commands

| Command | Description |
|---------|-------------|
| `seed_demo` | Seed/delete demo data for all or specific tenants |
| `seed_compliance` | Seed UK compliance baseline data |
| `seed_document_vault` | Seed document vault structure |
| `setup_production` | Production setup (create superuser, etc.) |
| `sync_crm_leads` | Sync CRM leads from booking clients |
| `update_demand_index` | Update service demand indices |
| `backfill_sbe_scores` | Backfill Smart Booking Engine risk scores |
| `send_booking_reminders` | Send 24h/1h booking reminder emails (runs in loop) |
| `seed_staff_availability_demo` | Seed availability engine demo data |

---

## Known Limitations & Future Work

### Current Limitations
- Restaurant booking flow creates a generic booking (no table auto-assignment yet)
- Gym booking flow creates a generic booking (no class session FK on Booking yet)
- No real-time WebSocket for chat — polling-based
- No email verification on public booking
- SBE risk scoring is rule-based, not ML
- No multi-currency support (GBP only)

### Planned Improvements
- Table auto-assignment algorithm for restaurant bookings
- Class session FK on Booking for proper gym booking tracking
- WebSocket chat via Django Channels
- Nightly demo data reset cron job
- Client self-service portal (view/cancel bookings)
- SMS notifications (Twilio)
- Google Calendar sync
- Multi-language support
