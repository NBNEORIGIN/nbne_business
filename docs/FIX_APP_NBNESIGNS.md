# Fix: app.nbnesigns.co.uk

## Problem

`app.nbnesigns.co.uk` should serve the NBNE internal tenant (Toby Fletcher / Jo Tompkins data) but may be misconfigured — either pointing to the wrong backend, wrong tenant slug, or missing real user data.

## Architecture

```
app.nbnesigns.co.uk (custom domain on Vercel)
  → Vercel project (frontend)
  → NEXT_PUBLIC_TENANT_SLUG=nbne
  → NEXT_PUBLIC_API_BASE_URL=https://nbneplatform-production.up.railway.app
  → Railway backend (shared, all tenants)
```

## Step-by-Step Fix

### 1. Verify Vercel Environment Variables

Go to the Vercel dashboard for the project that has `app.nbnesigns.co.uk` as a custom domain.

**Required env vars:**

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_TENANT_SLUG` | `nbne` |
| `NEXT_PUBLIC_API_BASE_URL` | `https://nbneplatform-production.up.railway.app` |
| `DJANGO_BACKEND_URL` | `https://nbneplatform-production.up.railway.app` |

If any of these are wrong or missing, set them and redeploy.

### 2. Verify CORS on Railway

The Railway backend must allow `https://app.nbnesigns.co.uk` in CORS. Check the `CORS_ALLOWED_ORIGINS` env var on Railway.

It's already in the code defaults at `backend/config/settings.py:218`:
```python
'https://app.nbnesigns.co.uk',
```

But if the Railway env var `CORS_ALLOWED_ORIGINS` is set (overriding defaults), make sure `https://app.nbnesigns.co.uk` is in the comma-separated list.

### 3. Verify the `nbne` Tenant Exists in the Database

SSH into Railway or use the Railway CLI:

```bash
railway run python manage.py shell -c "
from tenants.models import TenantSettings
try:
    t = TenantSettings.objects.get(slug='nbne')
    print(f'Found: {t.business_name} (type={t.business_type})')
except TenantSettings.DoesNotExist:
    print('NOT FOUND — run seed_demo')
"
```

If not found, seed it:
```bash
railway run python manage.py seed_demo --tenant nbne
```

### 4. Create Real Staff Users (Toby Fletcher / Jo Tompkins)

The seed data creates generic demo users. For the real NBNE instance, you need real users:

```bash
railway run python manage.py shell -c "
from django.contrib.auth import get_user_model
from tenants.models import TenantSettings
User = get_user_model()
tenant = TenantSettings.objects.get(slug='nbne')

# Create Toby Fletcher (owner)
toby, created = User.objects.get_or_create(
    username='toby',
    defaults={
        'email': 'toby@nbnesigns.com',
        'first_name': 'Toby',
        'last_name': 'Fletcher',
        'role': 'owner',
        'is_staff': True,
        'is_superuser': True,
        'tenant': tenant,
    }
)
if created:
    toby.set_password('CHANGE_ME_ON_FIRST_LOGIN')
    toby.save()
    print(f'Created Toby Fletcher')
else:
    print(f'Toby already exists (tenant={toby.tenant})')

# Create Jo Tompkins (manager)
jo, created = User.objects.get_or_create(
    username='jo',
    defaults={
        'email': 'jo@nbnesigns.com',
        'first_name': 'Jo',
        'last_name': 'Tompkins',
        'role': 'manager',
        'is_staff': True,
        'tenant': tenant,
    }
)
if created:
    jo.set_password('CHANGE_ME_ON_FIRST_LOGIN')
    jo.save()
    print(f'Created Jo Tompkins')
else:
    print(f'Jo already exists (tenant={jo.tenant})')
"
```

**Important:** Replace `CHANGE_ME_ON_FIRST_LOGIN` with a real password, or have them use the password reset flow.

### 5. Verify the API Responds

```bash
curl https://nbneplatform-production.up.railway.app/api/config/branding/?tenant=nbne
```

Should return JSON with `business_name: "NBNE"`, `business_type: "generic"`, etc.

### 6. Redeploy Vercel

After env var changes, trigger a redeploy:
- Go to Vercel dashboard → project → Deployments → Redeploy

### 7. Test

1. Visit `https://app.nbnesigns.co.uk` — should show NBNE landing page
2. Visit `https://app.nbnesigns.co.uk/login` — login as Toby or Jo
3. Visit `https://app.nbnesigns.co.uk/admin` — should show admin panel with NBNE branding

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Loading..." forever | API URL wrong or CORS blocked | Check `NEXT_PUBLIC_API_BASE_URL` and CORS |
| Shows "Salon X" branding | `NEXT_PUBLIC_TENANT_SLUG` is `salon-x` | Change to `nbne` |
| 401 on login | User not in `nbne` tenant | Create users with `tenant=nbne` |
| Shows demo data | Only seed data exists | Create real users per step 4 |
