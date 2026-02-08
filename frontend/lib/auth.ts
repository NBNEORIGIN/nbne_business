// ============================================================
// NBNE Platform Rev 2 — Auth Utilities
// ============================================================

import { SignJWT, jwtVerify } from 'jose'
import type { User, UserRole } from './types'
import { DEMO_USERS } from './demo-data'

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET || 'nbne-dev-secret-change-in-production')

export interface TokenPayload {
  sub: string
  email: string
  name: string
  role: UserRole
  iat: number
  exp: number
}

export async function createToken(user: User): Promise<string> {
  return new SignJWT({
    sub: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('8h')
    .sign(JWT_SECRET)
}

export async function verifyToken(token: string): Promise<TokenPayload | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET)
    return payload as unknown as TokenPayload
  } catch {
    return null
  }
}

// Demo login: match email + password against demo users
// In production this would hit the Django backend
export function authenticateDemoUser(email: string, password: string): User | null {
  const DEMO_CREDENTIALS: Record<string, string> = {
    'owner@demo.local': 'admin123',
    'manager@demo.local': 'admin123',
    'staff1@demo.local': 'admin123',
    'staff2@demo.local': 'admin123',
    'emma@example.com': 'customer123',
    'olivia@example.com': 'customer123',
  }
  if (DEMO_CREDENTIALS[email] !== password) return null
  return DEMO_USERS.find(u => u.email === email) || null
}

export const COOKIE_NAME = 'nbne_session'
