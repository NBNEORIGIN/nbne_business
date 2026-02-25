import { NextRequest, NextResponse } from 'next/server'

async function proxyRequest(req: NextRequest) {
  const API_BASE = process.env.DJANGO_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://nbneplatform-production.up.railway.app'
  const url = new URL(req.url)
  const path = url.pathname.replace(/^\/api\/django/, '')
  // Client header overrides env var so demo pages can switch tenant
  // Also read tenant from query param (sent by TenantProvider cache-bust URL)
  const tenantSlug = req.headers.get('x-tenant-slug') || url.searchParams.get('tenant') || process.env.NEXT_PUBLIC_TENANT_SLUG || ''
  console.log('[PROXY]', req.method, path, 'tenant:', tenantSlug, 'env:', process.env.NEXT_PUBLIC_TENANT_SLUG, 'header:', req.headers.get('x-tenant-slug'), 'qp:', url.searchParams.get('tenant'))

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
    // Don't forward auth for branding/tenant endpoints — they're public and
    // auth can cause the backend to resolve wrong tenant from user.tenant
    const isTenantEndpoint = path.startsWith('/tenant/')
    const auth = req.headers.get('authorization')
    if (auth && !isTenantEndpoint) headers['Authorization'] = auth
    if (tenantSlug) headers['X-Tenant-Slug'] = tenantSlug

    const init: RequestInit = {
      method: req.method,
      headers,
      cache: 'no-store',
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

    // Debug: log what the backend actually returned for tenant requests
    if (isTenantEndpoint) {
      const bodyText = new TextDecoder().decode(body)
      console.log('[PROXY TENANT RESPONSE]', path, 'target:', target, 'status:', res.status, 'body:', bodyText.substring(0, 200))
    }

    const respHeaders: Record<string, string> = {
      'Content-Type': res.headers.get('content-type') || 'application/json',
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
      'Pragma': 'no-cache',
    }
    const disposition = res.headers.get('content-disposition')
    if (disposition) respHeaders['Content-Disposition'] = disposition

    return new NextResponse(Buffer.from(body), {
      status: res.status,
      headers: respHeaders,
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
