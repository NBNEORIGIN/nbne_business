import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/demo/reset?key=DEMO_RESET_KEY
 * 
 * Nightly reset endpoint — called by Vercel Cron at 03:00 Europe/London.
 * Proxies to the Django backend's demo seed endpoint which wipes and reseeds data.
 */
export async function GET(request: NextRequest) {
  const key = request.nextUrl.searchParams.get('key')
  const expectedKey = process.env.DEMO_RESET_KEY || 'sorted-reset-2024'

  if (key !== expectedKey) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://nbneplatform-production.up.railway.app'
  const tenantSlug = process.env.NEXT_PUBLIC_TENANT_SLUG || 'salon-x'

  try {
    // Call the Django demo seed endpoint which is idempotent (wipes + reseeds)
    const res = await fetch(`${apiBase}/api/demo/seed/?tenant=${tenantSlug}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })

    const data = await res.json().catch(() => ({}))

    return NextResponse.json({
      success: true,
      message: `Demo reset completed for ${tenantSlug}`,
      backend_response: data,
      timestamp: new Date().toISOString(),
    })
  } catch (err: any) {
    return NextResponse.json({
      success: false,
      error: err.message || 'Failed to reset demo',
      timestamp: new Date().toISOString(),
    }, { status: 500 })
  }
}
