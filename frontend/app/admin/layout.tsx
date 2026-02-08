'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { useTenant, hasModule } from '@/lib/tenant'
import '../app/staff.css'

const NAV_ITEMS = [
  { href: '/admin', label: 'Dashboard', icon: '📊', module: '_always' },
  { href: '/admin/bookings', label: 'Bookings', icon: '📅', module: 'bookings' },
  { href: '/admin/services', label: 'Services', icon: '💇', module: 'bookings' },
  { href: '/admin/staff', label: 'Staff', icon: '👥', module: 'staff' },
  { href: '/admin/schedule', label: 'Schedule', icon: '🕐', module: 'bookings' },
  { href: '/admin/clients', label: 'CRM', icon: '📋', module: 'crm' },
  { href: '/admin/chat', label: 'Team Chat', icon: '💬', module: 'comms' },
  { href: '/admin/hse', label: 'Health & Safety', icon: '🛡️', module: 'compliance' },
  { href: '/admin/documents', label: 'Documents', icon: '📁', module: 'documents' },
  { href: '/admin/analytics', label: 'Analytics', icon: '📈', module: 'analytics' },
  { href: '/admin/audit', label: 'Audit Log', icon: '🔍', module: '_always' },
  { href: '/admin/settings', label: 'Settings', icon: '⚙️', module: '_always' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const tenant = useTenant()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const visibleNav = NAV_ITEMS.filter(item => item.module === '_always' || hasModule(tenant, item.module))

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

  return (
    <div className="shell">
      <header className="topbar">
        <button className="btn btn-ghost" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
        <span className="topbar-title">{tenant.business_name} — Admin</span>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span className="badge badge-danger">Tier 3</span>
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
              className={`nav-item ${pathname === item.href ? 'active' : ''}`}
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
