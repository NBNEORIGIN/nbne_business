'use client'

import { TenantProvider } from '@/lib/tenant'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <TenantProvider>
      {children}
    </TenantProvider>
  )
}
