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
function decodeJwtPayload(token: string): { sub?: string; user_id?: number; role?: string; name?: string; email?: string; exp?: number } | null {
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

  // Find matching protected route
  const route = PROTECTED_ROUTES.find(r => pathname.startsWith(r.prefix))
  if (!route) return NextResponse.next()

  // Check for session token
  const token = request.cookies.get(COOKIE_NAME)?.value
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Decode token payload
  const payload = decodeJwtPayload(token)
  if (!payload) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete(COOKIE_NAME)
    return response
  }

  // Check expiry
  if (payload.exp && payload.exp * 1000 < Date.now()) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete(COOKIE_NAME)
    return response
  }

  const role = (payload.role || 'customer') as UserRole

  // Enforce minimum role
  if (!hasMinRole(role, route.minRole)) {
    if (route.minRole === 'manager' && hasMinRole(role, 'staff')) {
      return NextResponse.redirect(new URL('/app', request.url))
    }
    return NextResponse.redirect(new URL('/', request.url))
  }

  // Attach user info to headers for downstream use
  const response = NextResponse.next()
  response.headers.set('x-user-id', String(payload.user_id || payload.sub || ''))
  response.headers.set('x-user-role', role)
  response.headers.set('x-user-name', payload.name || '')
  return response
}

export const config = {
  matcher: ['/admin/:path*', '/app/:path*'],
}
