# Deployment Guide — 3 Exemplar Demo Sites

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Vercel          │     │  Vercel          │     │  Vercel          │
│  salon-x         │     │  restaurant-x    │     │  health-club-x   │
│  TENANT=salon-x  │     │  TENANT=rest...  │     │  TENANT=health.. │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                        ┌─────────▼─────────┐
                        │  Railway           │
                        │  Django API        │
                        │  (all modules on)  │
                        │  PostgreSQL        │
                        └───────────────────┘
```

- **1 shared Django backend** on Railway with Postgres — all modules enabled
- **3 Vercel frontends** — same codebase, different `NEXT_PUBLIC_TENANT_SLUG` env var
- Each frontend fetches its tenant config (branding, enabled modules) from the API
- Nav items are hidden/shown based on the tenant's `enabled_modules` list

## Module Matrix

| Module      | Salon X | Restaurant X | Health Club X |
|-------------|---------|--------------|---------------|
| bookings    | ✅      | ✅           | ✅            |
| payments    | ✅      | ❌           | ✅            |
| staff       | ✅      | ✅           | ✅            |
| comms       | ✅      | ❌           | ✅            |
| compliance  | ✅      | ✅           | ✅            |
| documents   | ❌      | ❌           | ✅            |
| crm         | ❌      | ✅           | ❌            |
| analytics   | ✅      | ✅           | ✅            |

## Step 1: Deploy Backend to Railway

1. Create a new Railway project
2. Add a **PostgreSQL** service
3. Add a **GitHub repo** service pointing to the `backend/` directory
4. Set the **Root Directory** to `backend`
5. Set environment variables (see `backend/.env.example`):
   - `DJANGO_SECRET_KEY` — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=.railway.app`
   - `DATABASE_URL` — auto-set by Railway Postgres addon
   - `CORS_ALLOWED_ORIGINS` — comma-separated Vercel URLs (add after creating Vercel projects)
   - `CSRF_TRUSTED_ORIGINS` — same as CORS
6. Railway will detect the `Procfile` and run migrations + collectstatic on deploy
7. After first deploy, run seed command via Railway CLI or shell:
   ```
   python manage.py seed_demo
   ```

## Step 2: Deploy Frontends to Vercel

For each of the 3 sites:

1. Create a new Vercel project from the same repo
2. Set **Root Directory** to `frontend`
3. Set environment variables:
   - `NEXT_PUBLIC_API_BASE_URL` = Railway backend URL (e.g. `https://nbne-api.railway.app`)
   - `NEXT_PUBLIC_TENANT_SLUG` = `salon-x` / `restaurant-x` / `health-club-x`
4. Deploy

### Suggested Vercel project names:
- `salon-x-demo` → `salon-x-demo.vercel.app`
- `restaurant-x-demo` → `restaurant-x-demo.vercel.app`
- `health-club-x-demo` → `health-club-x-demo.vercel.app`

## Step 3: Update CORS on Railway

After creating all 3 Vercel projects, update the Railway env vars:

```
CORS_ALLOWED_ORIGINS=https://salon-x-demo.vercel.app,https://restaurant-x-demo.vercel.app,https://health-club-x-demo.vercel.app
CSRF_TRUSTED_ORIGINS=https://salon-x-demo.vercel.app,https://restaurant-x-demo.vercel.app,https://health-club-x-demo.vercel.app
```

## Demo Credentials

All 3 sites share the same demo accounts:

| Email                  | Password  | Role    |
|------------------------|-----------|---------|
| owner@demo.local       | admin123  | Owner   |
| manager@demo.local     | admin123  | Manager |
| staff1@demo.local      | admin123  | Staff   |

## Updating Sites

Since all 3 frontends use the same codebase, pushing to the repo will trigger all 3 Vercel deploys automatically. The only difference between them is the `NEXT_PUBLIC_TENANT_SLUG` env var.

Backend changes (new features, date pickers, etc.) deploy once to Railway and all 3 sites pick them up immediately.
