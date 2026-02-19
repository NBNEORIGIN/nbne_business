<#
.SYNOPSIS
    Deploy a new NBNE client instance on Railway.

.DESCRIPTION
    Creates a new Railway project with Postgres + backend service,
    sets all required env vars, generates a domain, runs migrations,
    and seeds demo data.

.PARAMETER ClientName
    Human-readable name, e.g. "Salon X"

.PARAMETER TenantSlug
    Slug used for tenant resolution, e.g. "salon-x"

.PARAMETER GitRepo
    GitHub repo for the backend service. Default: NBNEORIGIN/nbne_platform

.PARAMETER GitBranch
    Branch or tag to deploy. Default: main

.EXAMPLE
    .\scripts\deploy_client.ps1 -ClientName "Salon X" -TenantSlug "salon-x"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ClientName,

    [Parameter(Mandatory=$true)]
    [string]$TenantSlug,

    [string]$GitRepo = "NBNEORIGIN/nbne_platform",

    [string]$GitBranch = "main"
)

$ErrorActionPreference = "Stop"

# Sanitise project name for Railway
$ProjectName = "nbne-$TenantSlug"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NBNE Client Deployment: $ClientName"   -ForegroundColor Cyan
Write-Host "  Tenant slug: $TenantSlug"              -ForegroundColor Cyan
Write-Host "  Project: $ProjectName"                  -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Create Railway project ──────────────────────────────────────────────
Write-Host "[1/8] Creating Railway project..." -ForegroundColor Yellow
$initJson = railway init --name $ProjectName --json 2>&1 | ConvertFrom-Json
if (-not $initJson.id) {
    Write-Host "ERROR: Failed to create project." -ForegroundColor Red
    Write-Host $initJson
    exit 1
}
$projectId = $initJson.id
Write-Host "  Project ID: $projectId" -ForegroundColor Green

# Link to the new project
railway link -p $ProjectName

# ── 2. Add Postgres database ──────────────────────────────────────────────
Write-Host "[2/8] Adding Postgres database..." -ForegroundColor Yellow
railway add -d postgres
Start-Sleep -Seconds 5  # Give Railway a moment to provision
Write-Host "  Postgres added." -ForegroundColor Green

# ── 3. Add backend service from GitHub ────────────────────────────────────
Write-Host "[3/8] Adding backend service..." -ForegroundColor Yellow
$serviceName = "$TenantSlug-backend"
railway add -s $serviceName -r $GitRepo
Start-Sleep -Seconds 3
Write-Host "  Service '$serviceName' added." -ForegroundColor Green

# Link to the backend service for subsequent commands
railway link -p $ProjectName -s $serviceName

# ── 4. Set environment variables ──────────────────────────────────────────
Write-Host "[4/8] Setting environment variables..." -ForegroundColor Yellow

# Generate a random Django secret key
$chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)'
$secretKey = -join (1..50 | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })

# Core Django settings
railway variable set `
    "DJANGO_SECRET_KEY=$secretKey" `
    "DEBUG=False" `
    "ALLOWED_HOSTS=.up.railway.app,localhost,127.0.0.1" `
    "CSRF_TRUSTED_ORIGINS=https://*.up.railway.app" `
    "CORS_ALLOWED_ORIGINS=https://*.vercel.app" `
    --skip-deploys

# Module flags (all enabled for demo sites)
railway variable set `
    "BOOKINGS_MODULE_ENABLED=True" `
    "PAYMENTS_MODULE_ENABLED=True" `
    "STAFF_MODULE_ENABLED=True" `
    "COMMS_MODULE_ENABLED=True" `
    "COMPLIANCE_MODULE_ENABLED=True" `
    "DOCUMENTS_MODULE_ENABLED=True" `
    "CRM_MODULE_ENABLED=True" `
    "ANALYTICS_MODULE_ENABLED=True" `
    "TENANTS_MODULE_ENABLED=True" `
    --skip-deploys

# Email (using NBNE IONOS for now — can be overridden per client)
railway variable set `
    "EMAIL_HOST=smtp.ionos.co.uk" `
    "EMAIL_PORT=587" `
    "EMAIL_HOST_USER=toby@nbnesigns.com" `
    "EMAIL_HOST_PASSWORD=!49Monkswood" `
    "DEFAULT_FROM_EMAIL=toby@nbnesigns.com" `
    "EMAIL_BRAND_NAME=$ClientName" `
    "REMINDER_EMAIL_HOST=smtp.ionos.co.uk" `
    "REMINDER_EMAIL_PORT=465" `
    "REMINDER_EMAIL_USE_SSL=True" `
    "REMINDER_EMAIL_HOST_USER=toby@nbnesigns.com" `
    "REMINDER_EMAIL_HOST_PASSWORD=!49Monkswood" `
    "REMINDER_FROM_EMAIL=toby@nbnesigns.com" `
    --skip-deploys

Write-Host "  Environment variables set." -ForegroundColor Green

# ── 5. Generate Railway domain ────────────────────────────────────────────
Write-Host "[5/8] Generating domain..." -ForegroundColor Yellow
$domainOutput = railway domain -s $serviceName 2>&1
Write-Host "  $domainOutput" -ForegroundColor Green

# Update ALLOWED_HOSTS and CSRF with the actual domain
# (The wildcard *.up.railway.app should cover it, but we can refine later)

# ── 6. Wait for first deployment ──────────────────────────────────────────
Write-Host "[6/8] Triggering deployment..." -ForegroundColor Yellow
Write-Host "  Waiting for build + deploy (this may take 2-5 minutes)..." -ForegroundColor DarkGray

# Trigger a redeploy now that env vars are set
railway redeploy -s $serviceName 2>$null

# Poll for deployment status
$maxWait = 300  # 5 minutes
$elapsed = 0
$deployed = $false
while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds 15
    $elapsed += 15
    $statusOutput = railway service status 2>&1
    if ($statusOutput -match "SUCCESS|RUNNING|ACTIVE") {
        $deployed = $true
        break
    }
    Write-Host "  Still deploying... ($elapsed`s)" -ForegroundColor DarkGray
}

if (-not $deployed) {
    Write-Host "  WARNING: Deployment may still be in progress. Check Railway dashboard." -ForegroundColor Yellow
    Write-Host "  Continuing with remaining steps..." -ForegroundColor Yellow
}

# ── 7. Run migrations ────────────────────────────────────────────────────
Write-Host "[7/8] Running migrations..." -ForegroundColor Yellow
# We need to use the public DATABASE_URL for local execution
# Get it from the Postgres service
$pgVars = railway variable list --kv -s Postgres 2>&1
$publicUrl = ($pgVars | Select-String "DATABASE_PUBLIC_URL=(.+)").Matches.Groups[1].Value

if ($publicUrl) {
    $env:DATABASE_URL = $publicUrl
    python backend/manage.py migrate --no-input
    Write-Host "  Migrations complete." -ForegroundColor Green

    # ── 8. Seed demo data ─────────────────────────────────────────────────
    Write-Host "[8/8] Seeding demo data for $TenantSlug..." -ForegroundColor Yellow
    python backend/manage.py seed_demo --tenant $TenantSlug
    Write-Host "  Seed complete." -ForegroundColor Green
} else {
    Write-Host "  WARNING: Could not get DATABASE_PUBLIC_URL. Run manually:" -ForegroundColor Yellow
    Write-Host "    railway run python manage.py migrate" -ForegroundColor White
    Write-Host "    railway run python manage.py seed_demo --tenant $TenantSlug" -ForegroundColor White
}

# ── Summary ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Railway project: $ProjectName"
Write-Host "  Project ID:      $projectId"
Write-Host "  Tenant slug:     $TenantSlug"
Write-Host "  Backend domain:  (check Railway dashboard)"
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create a Vercel project pointing to the same GitHub repo"
Write-Host "  2. Set NEXT_PUBLIC_TENANT_SLUG=$TenantSlug"
Write-Host "  3. Set NEXT_PUBLIC_API_BASE_URL=https://<railway-domain>"
Write-Host "  4. Set DJANGO_BACKEND_URL=https://<railway-domain>"
Write-Host "  5. Update CORS_ALLOWED_ORIGINS on Railway with the Vercel URL"
Write-Host "  6. Update FRONTEND_URL on Railway with the Vercel URL"
Write-Host ""
