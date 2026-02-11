'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { getTenantBranding } from './api'

export interface TenantConfig {
  slug: string
  business_name: string
  enabled_modules: string[]
  tagline: string
  colour_primary: string
  colour_secondary: string
  colour_background: string
  colour_text: string
  currency_symbol: string
  logo_url: string
  favicon_url: string
  font_heading: string
  font_body: string
  font_url: string
}

const DEFAULT_CONFIG: TenantConfig = {
  slug: 'default',
  business_name: 'Business',
  enabled_modules: [],
  tagline: '',
  colour_primary: '#2563eb',
  colour_secondary: '#1e40af',
  colour_background: '#ffffff',
  colour_text: '#333333',
  currency_symbol: '£',
  logo_url: '',
  favicon_url: '',
  font_heading: '',
  font_body: '',
  font_url: '',
}

const TenantContext = createContext<TenantConfig>(DEFAULT_CONFIG)

export function useTenant() {
  return useContext(TenantContext)
}

export function hasModule(tenant: TenantConfig, mod: string): boolean {
  return tenant.enabled_modules.length === 0 || tenant.enabled_modules.includes(mod)
}

export const TENANT_SLUG = 'mind-department'

export function TenantProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<TenantConfig>(DEFAULT_CONFIG)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    getTenantBranding({ tenant: TENANT_SLUG }).then(r => {
      if (r.data) {
        setConfig({ ...DEFAULT_CONFIG, ...r.data })
      }
      setReady(true)
    }).catch(() => setReady(true))
  }, [])

  useEffect(() => {
    if (config.slug === 'default') return
    const root = document.documentElement
    root.style.setProperty('--color-primary', config.colour_primary)
    root.style.setProperty('--color-primary-dark', config.colour_secondary)
    root.style.setProperty('--color-bg', config.colour_background)
    root.style.setProperty('--color-text', config.colour_text)
    if (config.font_heading) root.style.setProperty('--font-heading', config.font_heading)
    if (config.font_body) root.style.setProperty('--font-body', config.font_body)
    if (config.font_url) {
      const existing = document.querySelector('link[data-tenant-font]')
      if (!existing) {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = config.font_url
        link.setAttribute('data-tenant-font', 'true')
        document.head.appendChild(link)
      }
    }
    if (config.favicon_url) {
      const link = document.querySelector("link[rel~='icon']") as HTMLLinkElement
      if (link) link.href = config.favicon_url
    }
    document.title = config.business_name
  }, [config])

  if (!ready) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <p>Loading…</p>
      </div>
    )
  }

  return (
    <TenantContext.Provider value={config}>
      {children}
    </TenantContext.Provider>
  )
}
