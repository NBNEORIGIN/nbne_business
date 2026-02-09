import { NextRequest, NextResponse } from 'next/server'
import { COOKIE_NAME } from '@/lib/auth'

const DJANGO_API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { action } = body

  // Logout
  if (action === 'logout') {
    const response = NextResponse.json({ ok: true })
    response.cookies.set(COOKIE_NAME, '', { maxAge: 0, path: '/' })
    return response
  }

  // Login — proxy to Django JWT endpoint
  // Frontend sends email but Django expects username; the seed uses email-based usernames
  // so we try the email prefix as username, or the full email
  const username = body.username || body.email?.split('@')[0] || ''
  const password = body.password || ''

  try {
    const djangoRes = await fetch(`${DJANGO_API}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!djangoRes.ok) {
      const err = await djangoRes.json().catch(() => ({}))
      return NextResponse.json(
        { ok: false, error: err.detail || 'Invalid credentials' },
        { status: 401 }
      )
    }

    const data = await djangoRes.json()
    // data = { access, refresh, user: { id, role, tier, ... } }

    const response = NextResponse.json({
      ok: true,
      user: data.user,
      must_change_password: data.user?.must_change_password || false,
      access: data.access,
      refresh: data.refresh,
    })

    // Store access token in httpOnly cookie for middleware RBAC
    response.cookies.set(COOKIE_NAME, data.access, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 8,
    })

    return response
  } catch {
    return NextResponse.json(
      { ok: false, error: 'Backend unavailable' },
      { status: 503 }
    )
  }
}
