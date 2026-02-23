'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { useTenant, hasModule, TENANT_SLUG } from '@/lib/tenant'
import CommandBar from '@/components/CommandBar'
import '../app/staff.css'

const NAV_ITEMS = [
  { href: '/admin', label: 'Dashboard', icon: '📊', module: '_always' },
  { href: '/admin/bookings', label: 'Bookings', icon: '📅', module: 'bookings' },
  { href: '/admin/reports', label: 'Reports', icon: '💰', module: 'bookings' },
  { href: '/admin/services', label: 'Services', icon: '💇', module: 'bookings' },
  { href: '/admin/tables', label: 'Tables', icon: '🍽️', module: 'bookings', businessType: 'restaurant' },
  { href: '/admin/service-windows', label: 'Service Windows', icon: '🕐', module: 'bookings', businessType: 'restaurant' },
  { href: '/admin/class-types', label: 'Class Types', icon: '🏋️', module: 'bookings', businessType: 'gym' },
  { href: '/admin/timetable', label: 'Timetable', icon: '📆', module: 'bookings', businessType: 'gym' },
  { href: '/admin/staff', label: 'Staff', icon: '👥', module: 'staff' },
  { href: '/admin/clients', label: 'CRM', icon: '📋', module: 'crm' },
  { href: '/admin/chat', label: 'Team Chat', icon: '💬', module: 'comms' },
  { href: '/admin/health-safety', label: 'Health & Safety', icon: '🛡️', module: 'compliance' },
  { href: '/admin/documents', label: 'Documents', icon: '📁', module: 'documents' },
  { href: '/admin/audit', label: 'Audit Log', icon: '🔍', module: '_always' },
  { href: '/admin/settings', label: 'Settings', icon: '⚙️', module: '_always' },
] as const

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const tenant = useTenant()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const visibleNav = NAV_ITEMS.filter(item => {
    if (item.module !== '_always' && !hasModule(tenant, item.module)) return false
    if ('businessType' in item && item.businessType && item.businessType !== tenant.business_type) return false
    return true
  })

  async function handleLogout() {
    localStorage.removeItem('nbne_access')
    localStorage.removeItem('nbne_refresh')
    await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'logout' }),
    })
    router.push('/login')
  }

  // Live tenants (nbne) never show demo banner — check both runtime and build-time slug
  const isDemo = TENANT_SLUG !== 'nbne' && tenant.slug !== 'nbne' && !!tenant.slug

  return (
    <div className="shell">
      {isDemo && (
        <div style={{
          background: '#2563eb', color: '#fff', textAlign: 'center',
          padding: '0.35rem 1rem', fontSize: '0.78rem', fontWeight: 500,
        }}>
          This is a demo. Data resets nightly. <a href="/" style={{ color: '#bfdbfe', marginLeft: '0.5rem' }}>Back to site</a>
        </div>
      )}
      <header className="topbar" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <button className="btn btn-ghost" onClick={() => setSidebarOpen(!sidebarOpen)} style={{ flexShrink: 0 }}>☰</button>
        <span className="topbar-title" style={{ flexShrink: 0, marginRight: '0.5rem' }}>{tenant.business_name}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <CommandBar />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexShrink: 0 }}>
          <button className="btn btn-ghost" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`} style={{ background: '#1e293b' }}>
        <div className="sidebar-header">
          <h2>Admin Panel</h2>
          <div style={{ fontSize: '0.75rem', opacity: 0.6, marginTop: '0.25rem' }}>Owner / Manager</div>
        </div>
        <nav className="sidebar-nav">
          {visibleNav.map(item => (
            <a
              key={item.href}
              href={item.href}
              className={`nav-item ${item.href === '/admin' ? (pathname === '/admin' ? 'active' : '') : pathname.startsWith(item.href) ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <a href="/app" className="nav-item" style={{ opacity: 0.6, fontSize: '0.8rem' }}>
            <span className="nav-icon">👤</span>
            <span>Staff Portal</span>
          </a>
        </div>
      </aside>

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <main className="main-content">{children}</main>
    </div>
  )
}
