import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { COOKIE_NAME } from './lib/auth'
import type { UserRole } from './lib/types'
import { hasMinRole } from './lib/types'

// Route → minimum role required
const PROTECTED_ROUTES: { prefix: string; minRole: UserRole }[] = [
  { prefix: '/admin', minRole: 'manager' },
  { prefix: '/app', minRole: 'staff' },
]

// Decode JWT payload without verification (cookie is httpOnly, Django enforces real auth)
const EXPECTED_TENANT = process.env.NEXT_PUBLIC_TENANT_SLUG || ''

function decodeJwtPayload(token: string): { sub?: string; user_id?: number; role?: string; name?: string; email?: string; exp?: number; tenant_slug?: string } | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(b64)
    return JSON.parse(json)
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Force no-cache on all page responses to prevent Chrome from serving stale tenant data
  function withNoCacheHeaders(res: NextResponse) {
    res.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
    res.headers.set('Pragma', 'no-cache')
    res.headers.set('Expires', '0')
    return res
  }

  // Find matching protected route
  const route = PROTECTED_ROUTES.find(r => pathname.startsWith(r.prefix))
  if (!route) return withNoCacheHeaders(NextResponse.next())

  // Check for session token
  const token = request.cookies.get(COOKIE_NAME)?.value
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return withNoCacheHeaders(NextResponse.redirect(loginUrl))
  }

  // Decode token payload
  const payload = decodeJwtPayload(token)
  if (!payload) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete(COOKIE_NAME)
    return withNoCacheHeaders(response)
  }

  // Check expiry
  if (payload.exp && payload.exp * 1000 < Date.now()) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete(COOKIE_NAME)
    return withNoCacheHeaders(response)
  }

  // Reject cross-tenant sessions (e.g. stale Mind Department cookie on NBNE app)
  if (EXPECTED_TENANT && payload.tenant_slug && payload.tenant_slug !== EXPECTED_TENANT) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete(COOKIE_NAME)
    return withNoCacheHeaders(response)
  }

  const role = (payload.role || 'customer') as UserRole

  // Enforce minimum role
  if (!hasMinRole(role, route.minRole)) {
    if (route.minRole === 'manager' && hasMinRole(role, 'staff')) {
      return withNoCacheHeaders(NextResponse.redirect(new URL('/app', request.url)))
    }
    return withNoCacheHeaders(NextResponse.redirect(new URL('/', request.url)))
  }

  // Attach user info to headers for downstream use
  const response = NextResponse.next()
  response.headers.set('x-user-id', String(payload.user_id || payload.sub || ''))
  response.headers.set('x-user-role', role)
  response.headers.set('x-user-name', payload.name || '')
  return withNoCacheHeaders(response)
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icons|sw.js).*)'],
}
