'use client'

import { useEffect, useState } from 'react'
import { getTenantSettings } from '@/lib/api'
import { useTenant, TENANT_SLUG } from '@/lib/tenant'

export default function AdminSettingsPage() {
  const tenant = useTenant()
  const [config, setConfig] = useState({
    businessName: '',
    email: '',
    phone: '',
    address: '',
    depositEnabled: true,
    defaultDepositPct: 30,
    bookingLeadDays: 14,
    cancellationHours: 24,
    primaryColour: '#2563eb',
    secondaryColour: '#f59e0b',
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getTenantSettings({ tenant: TENANT_SLUG }).then(r => {
      if (r.data) {
        setConfig({
          businessName: r.data.business_name || '',
          email: r.data.email || '',
          phone: r.data.phone || '',
          address: r.data.address || '',
          depositEnabled: (r.data.deposit_percentage || 0) > 0,
          defaultDepositPct: r.data.deposit_percentage || 30,
          bookingLeadDays: 14,
          cancellationHours: 24,
          primaryColour: r.data.colour_primary || '#2563eb',
          secondaryColour: r.data.colour_secondary || '#f59e0b',
        })
      }
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="empty-state">Loading settings…</div>

  return (
    <div>
      <div className="page-header"><h1>System Settings</h1><span className="badge badge-danger">Tier 3 — Owner Only</span></div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>Business Details</h2>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div><label>Business Name</label><input value={config.businessName} onChange={e => setConfig({ ...config, businessName: e.target.value })} /></div>
            <div><label>Email</label><input type="email" value={config.email} onChange={e => setConfig({ ...config, email: e.target.value })} /></div>
            <div><label>Phone</label><input value={config.phone} onChange={e => setConfig({ ...config, phone: e.target.value })} /></div>
            <div><label>Address</label><textarea rows={2} value={config.address} onChange={e => setConfig({ ...config, address: e.target.value })} /></div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>Booking Rules</h2>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input type="checkbox" checked={config.depositEnabled} onChange={e => setConfig({ ...config, depositEnabled: e.target.checked })} /> Require deposit on booking
            </label>
            {config.depositEnabled && (
              <div><label>Default Deposit %</label><input type="number" min={0} max={100} value={config.defaultDepositPct} onChange={e => setConfig({ ...config, defaultDepositPct: +e.target.value })} /></div>
            )}
            <div><label>Booking Lead Days</label><input type="number" value={config.bookingLeadDays} onChange={e => setConfig({ ...config, bookingLeadDays: +e.target.value })} /></div>
            <div><label>Cancellation Notice (hours)</label><input type="number" value={config.cancellationHours} onChange={e => setConfig({ ...config, cancellationHours: +e.target.value })} /></div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>Branding</h2>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div><label>Primary Colour</label><div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}><input type="color" value={config.primaryColour} onChange={e => setConfig({ ...config, primaryColour: e.target.value })} style={{ width: 50, height: 36, padding: 2 }} /><input value={config.primaryColour} onChange={e => setConfig({ ...config, primaryColour: e.target.value })} /></div></div>
            <div><label>Secondary Colour</label><div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}><input type="color" value={config.secondaryColour} onChange={e => setConfig({ ...config, secondaryColour: e.target.value })} style={{ width: 50, height: 36, padding: 2 }} /><input value={config.secondaryColour} onChange={e => setConfig({ ...config, secondaryColour: e.target.value })} /></div></div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>Module Status</h2>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'].map(mod => {
              const enabled = tenant.enabled_modules.length === 0 || tenant.enabled_modules.includes(mod)
              return (
                <div key={mod} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{mod}</span>
                  <span className={`badge ${enabled ? 'badge-success' : 'badge-neutral'}`}>{enabled ? 'Enabled' : 'Disabled'}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
        <button className="btn btn-primary">Save Settings</button>
      </div>
    </div>
  )
}
