import { NextRequest, NextResponse } from 'next/server'

const API_BASE = 'https://nbnebusiness-production-6853.up.railway.app'

async function proxyRequest(req: NextRequest) {
  const url = new URL(req.url)
  const path = url.pathname.replace(/^\/api\/django/, '')
  const target = `${API_BASE}/api${path}${url.search}`

  try {
    const headers: Record<string, string> = {}
    const contentType = req.headers.get('content-type')
    if (contentType) headers['Content-Type'] = contentType
    const auth = req.headers.get('authorization')
    if (auth) headers['Authorization'] = auth

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
