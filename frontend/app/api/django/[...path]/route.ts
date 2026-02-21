import { NextRequest, NextResponse } from 'next/server'

async function proxyRequest(req: NextRequest) {
  const API_BASE = process.env.DJANGO_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://nbneplatform-production.up.railway.app'
  const url = new URL(req.url)
  const path = url.pathname.replace(/^\/api\/django/, '')

  // Debug: return config info when path is /_debug
  if (path === '/_debug' || path === '/_debug/') {
    return NextResponse.json({
      API_BASE,
      DJANGO_BACKEND_URL: process.env.DJANGO_BACKEND_URL || '(not set)',
      NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || '(not set)',
      NEXT_PUBLIC_TENANT_SLUG: process.env.NEXT_PUBLIC_TENANT_SLUG || '(not set)',
    })
  }

  // Client header overrides env var so demo pages can switch tenant
  const tenantSlug = req.headers.get('x-tenant-slug') || process.env.NEXT_PUBLIC_TENANT_SLUG || ''

  // Build target URL, injecting tenant as query param for reliable resolution
  let target = `${API_BASE}/api${path}${url.search}`
  if (tenantSlug) {
    const sep = target.includes('?') ? '&' : '?'
    target = `${target}${sep}tenant=${tenantSlug}`
  }

  try {
    const headers: Record<string, string> = {}
    const contentType = req.headers.get('content-type')
    if (contentType) headers['Content-Type'] = contentType
    const auth = req.headers.get('authorization')
    if (auth) headers['Authorization'] = auth
    if (tenantSlug) headers['X-Tenant-Slug'] = tenantSlug

    const init: RequestInit = {
      method: req.method,
      headers,
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      try {
        const buf = await req.arrayBuffer()
        if (buf.byteLength > 0) init.body = Buffer.from(buf)
      } catch {
        // no body
      }
    }

    const res = await fetch(target, init)
    const body = await res.arrayBuffer()

    return new NextResponse(Buffer.from(body), {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    })
  } catch (err: any) {
    console.error('[PROXY ERROR]', target, err.message)
    return NextResponse.json(
      { error: 'Proxy error', detail: err.message, target },
      { status: 502 }
    )
  }
}

export const GET = proxyRequest
export const POST = proxyRequest
export const PUT = proxyRequest
export const PATCH = proxyRequest
export const DELETE = proxyRequest
export const OPTIONS = proxyRequest
