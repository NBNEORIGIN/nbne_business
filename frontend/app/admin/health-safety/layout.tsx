'use client'

import { usePathname } from 'next/navigation'

const HSE_NAV = [
  { href: '/admin/health-safety', label: 'Overview', exact: true },
  { href: '/admin/health-safety/register', label: 'Compliance Register' },
  { href: '/admin/health-safety/training', label: 'Staff Training' },
  { href: '/admin/health-safety/incidents', label: 'Incidents' },
  { href: '/admin/health-safety/documents', label: 'Documents' },
]

export default function HealthSafetyLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  function isActive(item: typeof HSE_NAV[0]) {
    if (item.exact) return pathname === item.href
    return pathname.startsWith(item.href)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Health &amp; Safety</h1>
      </div>

      <nav className="hse-subnav">
        {HSE_NAV.map(item => (
          <a
            key={item.href}
            href={item.href}
            className={`hse-subnav-item ${isActive(item) ? 'active' : ''}`}
          >
            {item.label}
          </a>
        ))}
      </nav>

      {children}
    </div>
  )
}
