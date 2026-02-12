'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function HSERedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/admin/health-safety') }, [router])
  return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Redirecting...</div>
}
