# NBNE Platform — Versioning & Release Discipline

## Principles

1. **Single core repo** — no per-client forks.
2. **Tenants isolated by data** (separate Railway projects / DBs), not by code divergence.
3. **Deployments pinned to immutable tags**, never moving branch heads.
4. **Customisation via tenant settings + feature flags**, never `if tenant == X` code.

---

## Branch Model

| Branch    | Purpose                        | Deploys to        |
|-----------|--------------------------------|-------------------|
| `main`    | Active development             | Never (dev only)  |
| `release` | Stable integration             | Via tags only      |

### Rules

- All feature work happens on `main`.
- Only validated changes merge from `main → release` (via PR).
- **Never deploy any client directly from `main`.**
- `release` is only deployed via immutable tags.

---

## Tagged Releases

Tags are created **from the `release` branch only**.

```
v0.9.0   ← first production candidate
v0.9.1   ← patch / hotfix
v1.0.0   ← major milestone
```

- Follow [Semantic Versioning](https://semver.org/): `vMAJOR.MINOR.PATCH`
- Tags are **immutable** — never delete or move a tag.
- Every tag must have a short annotation describing what changed.

---

## Client Deployment Model

Each client (tenant) has:

| Resource         | Isolation                                      |
|------------------|------------------------------------------------|
| Railway project  | Own project, own env vars, own deploy settings |
| PostgreSQL DB    | Own database instance                          |
| Vercel frontend  | Own Vercel project (optional custom domain)    |
| Git tag          | Pinned to a specific release tag               |

This enables **independent upgrade cadence**:
- Client A stays on `v0.9.1` while Client B upgrades to `v0.9.2`.
- Roll out a tag to one client first, validate, then roll out to others.

### Railway Configuration Per Client

Each Railway project needs:
- **Source**: GitHub repo `NBNEORIGIN/nbne_platform`
- **Branch**: (not used — deploy from tag)
- **Root directory**: `backend`
- **Environment variables**: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, plus module flags and email config.

To deploy a specific tag on Railway:
1. In the Railway project dashboard, go to **Settings → Deploy**.
2. Set the deploy reference to the tag (e.g. `v0.9.1`).
3. Trigger a redeploy.

Alternatively, use the Railway CLI:
```bash
railway up --ref v0.9.1
```

---

## Feature Flags & Tenant Settings

The platform has **three layers** of feature control:

### 1. Environment Variable Flags (per Railway project)
In `config/settings.py`:
```python
BOOKINGS_MODULE_ENABLED = config('BOOKINGS_MODULE_ENABLED', default=True, cast=bool)
STAFF_MODULE_ENABLED    = config('STAFF_MODULE_ENABLED', default=True, cast=bool)
# ... etc for all 9 modules
```
These control whether Django apps are even loaded.

### 2. Config Model (DB key-value store)
`core.Config` with `category='features'` — runtime feature flags editable via admin.

### 3. TenantSettings.enabled_modules (per-tenant JSON)
`tenants.TenantSettings.enabled_modules` — list of module slugs the frontend should show for that tenant.

**Rule**: Never write `if tenant.slug == 'salon-x'` in code. All behaviour differences must flow through these three layers.

---

## Release Process Checklist

### 1. Develop on `main`
```bash
git checkout main
# ... make changes, commit, push
```

### 2. Validate
```bash
cd backend
python manage.py test --parallel          # run tests
python manage.py makemigrations --check   # no missing migrations
python manage.py check --deploy           # Django deployment checks
```

### 3. Merge `main → release` (via PR)
```bash
git checkout release
git pull origin release
git merge main
# Resolve any conflicts
git push origin release
```
Or create a PR on GitHub: `main → release`, review, merge.

### 4. Tag the release
```bash
git checkout release
git pull origin release
git tag -a v0.9.1 -m "v0.9.1: brief description of changes"
git push origin v0.9.1
```

### 5. Deploy to a tenant
- Go to the client's Railway project.
- Set deploy reference to `v0.9.1`.
- Trigger redeploy.
- Verify: migrations run, seed commands pass, Gunicorn starts.

### 6. Roll out to other tenants
- Once validated on the first tenant, repeat step 5 for each additional client.

### 7. Hotfixes
```bash
git checkout release
git checkout -b hotfix/fix-description
# ... make fix, commit
git checkout release
git merge hotfix/fix-description
git tag -a v0.9.2 -m "v0.9.2: hotfix — description"
git push origin release v0.9.2
# Deploy to affected tenant(s)
```

---

## How We Deploy a New Tenant

1. **Create Railway project** — new project in Railway, connect to `NBNEORIGIN/nbne_platform` repo.
2. **Provision database** — add PostgreSQL plugin or connect external DB.
3. **Set environment variables** — copy from template (see `DEPLOY.md`), customise `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, DB credentials, `SECRET_KEY`.
4. **Set root directory** to `backend`.
5. **Pin to a tag** — set deploy reference to the latest stable tag (e.g. `v0.9.1`).
6. **Deploy** — Railway builds and runs `start.sh` (migrations, seeds, Gunicorn).
7. **Create Vercel frontend** (if needed) — new Vercel project from same repo, root directory `frontend`, set `NEXT_PUBLIC_API_BASE_URL` to the Railway URL.
8. **Seed tenant data** — `seed_demo` creates the tenant row, or manually create via Django admin.
9. **Verify** — hit `/api/tenant/branding/` to confirm tenant settings are returned.

---

## Current State

| Item                  | Status                                              |
|-----------------------|-----------------------------------------------------|
| Repo                  | `github.com/NBNEORIGIN/nbne_platform`              |
| Branch model          | `main` only (need to create `release`)              |
| Tags                  | None yet (first tag after `release` branch created) |
| Railway (shared dev)  | `nbneplatform-production.up.railway.app`            |
| Demo tenants          | Salon X, Restaurant X, Health Club X, TMD, NBNE     |
| Feature flags         | 3-layer system in place                             |
