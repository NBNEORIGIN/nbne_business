'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams } from 'next/navigation'
import { getRamsDetail, updateRams, runRamsAiReview } from '@/lib/api'

// ── Section metadata ──
const ALL_SECTIONS = [
  { key: 'job_details', label: 'Job Details', icon: '📋' },
  { key: 'personnel', label: 'Personnel', icon: '👷' },
  { key: 'equipment', label: 'Equipment', icon: '🔧' },
  { key: 'hazards', label: 'Hazards & Controls', icon: '⚠️' },
  { key: 'method_statement', label: 'Method Statement', icon: '📝' },
  { key: 'emergency_procedures', label: 'Emergency Procedures', icon: '🚑' },
  { key: 'environmental', label: 'Environmental', icon: '🌿' },
  { key: 'permits', label: 'Permits', icon: '📄' },
  { key: 'monitoring', label: 'Monitoring & Review', icon: '🔍' },
]

const RISK_LABELS: Record<number, string> = { 1: 'Very Low', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Very High' }
const RISK_COLOURS: Record<string, string> = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', 'very high': '#991b1b',
}

function riskScore(l: number, s: number) { return l * s }
function riskLevel(score: number): string {
  if (score <= 4) return 'low'
  if (score <= 9) return 'medium'
  if (score <= 16) return 'high'
  return 'very high'
}
function riskColour(score: number): string {
  return RISK_COLOURS[riskLevel(score)] || '#94a3b8'
}

const emptyHazard = () => ({
  description: '', controls: '',
  initial_likelihood: 3, initial_severity: 3,
  residual_likelihood: 1, residual_severity: 2,
})

const emptyPerson = () => ({ name: '', role: '', qualifications: '', responsibilities: '' })
const emptyEquipment = () => ({ name: '', inspection_date: '', cert_ref: '', notes: '' })
const emptyStep = (n: number) => ({ step_number: n, description: '', responsible: '', hazard_refs: '' })
const emptyPermit = () => ({ type: '', reference: '', issued_by: '', expiry: '' })

// Track which sections are expanded in the editor
type ExpandedSections = Record<string, boolean>

export default function RamsEditorPage() {
  const params = useParams()
  const ramsId = Number(params.id)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [rams, setRams] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)

  // Expanded accordion sections
  const [expanded, setExpanded] = useState<ExpandedSections>({ job_details: true })
  const toggleExpand = (key: string) => setExpanded(prev => ({ ...prev, [key]: !prev[key] }))
  const scrollToSection = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: true }))
    setTimeout(() => document.getElementById(`section-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  // Form data
  const [applicableSections, setApplicableSections] = useState<string[]>([])
  const [jobDetails, setJobDetails] = useState<any>({})
  const [personnel, setPersonnel] = useState<any[]>([emptyPerson()])
  const [equipment, setEquipment] = useState<any[]>([emptyEquipment()])
  const [hazards, setHazards] = useState<any[]>([emptyHazard()])
  const [methodStatement, setMethodStatement] = useState<any[]>([emptyStep(1)])
  const [emergencyProcedures, setEmergencyProcedures] = useState<any>({})
  const [environmental, setEnvironmental] = useState<any>({})
  const [permits, setPermits] = useState<any[]>([emptyPermit()])
  const [monitoring, setMonitoring] = useState<any>({})
  const [aiReview, setAiReview] = useState<any>(null)
  const [title, setTitle] = useState('')
  const [refNumber, setRefNumber] = useState('')
  const [ramsStatus, setRamsStatus] = useState('DRAFT')
  const [showPreview, setShowPreview] = useState(true)
  const [reviewHistory, setReviewHistory] = useState<any[]>([])
  const [appliedFlash, setAppliedFlash] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getRamsDetail(ramsId)
    if (res.data) {
      const d = res.data
      setRams(d)
      setTitle(d.title || '')
      setRefNumber(d.reference_number || '')
      setRamsStatus(d.status || 'DRAFT')
      setApplicableSections(d.applicable_sections?.length ? d.applicable_sections : ALL_SECTIONS.map(s => s.key))
      setJobDetails(d.job_details || {})
      setPersonnel(d.personnel?.length ? d.personnel : [emptyPerson()])
      setEquipment(d.equipment?.length ? d.equipment : [emptyEquipment()])
      setHazards(d.hazards?.length ? d.hazards : [emptyHazard()])
      setMethodStatement(d.method_statement?.length ? d.method_statement : [emptyStep(1)])
      setEmergencyProcedures(d.emergency_procedures || {})
      setEnvironmental(d.environmental || {})
      setPermits(d.permits?.length ? d.permits : [emptyPermit()])
      setMonitoring(d.monitoring || {})
      setAiReview(d.ai_review || null)
    }
    setLoading(false)
  }, [ramsId])

  useEffect(() => { load() }, [load])

  async function handleSave() {
    setSaving(true)
    setSaved(false)
    await updateRams(ramsId, {
      title, reference_number: refNumber, status: ramsStatus,
      applicable_sections: applicableSections,
      job_details: jobDetails,
      personnel, equipment, hazards,
      method_statement: methodStatement,
      emergency_procedures: emergencyProcedures,
      environmental, permits, monitoring,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  async function handleAiReview() {
    setSaving(true)
    await updateRams(ramsId, {
      title, reference_number: refNumber, status: ramsStatus,
      applicable_sections: applicableSections,
      job_details: jobDetails,
      personnel, equipment, hazards,
      method_statement: methodStatement,
      emergency_procedures: emergencyProcedures,
      environmental, permits, monitoring,
    })
    setSaving(false)
    setAiLoading(true)
    const res = await runRamsAiReview(ramsId)
    if (res.data) {
      // Keep review history for comparison
      if (aiReview) setReviewHistory(prev => [...prev, { score: aiReview.score, at: aiReview.reviewed_at }])
      setAiReview(res.data)
    }
    setAiLoading(false)
    // Reload full document to capture any server-side changes
    const fresh = await getRamsDetail(ramsId)
    if (fresh.data) setRams(fresh.data)
  }

  function toggleSection(key: string) {
    setApplicableSections(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  function isApplicable(key: string) { return applicableSections.includes(key) }

  // Hazard helpers
  function updateHazard(idx: number, field: string, value: any) {
    setHazards(prev => prev.map((h, i) => i === idx ? { ...h, [field]: value } : h))
  }
  function addHazard() { setHazards(prev => [...prev, emptyHazard()]) }
  function removeHazard(idx: number) { setHazards(prev => prev.filter((_, i) => i !== idx)) }

  // Personnel helpers
  function updatePerson(idx: number, field: string, value: string) {
    setPersonnel(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p))
  }
  function addPerson() { setPersonnel(prev => [...prev, emptyPerson()]) }
  function removePerson(idx: number) { setPersonnel(prev => prev.filter((_, i) => i !== idx)) }

  // Equipment helpers
  function updateEquip(idx: number, field: string, value: string) {
    setEquipment(prev => prev.map((e, i) => i === idx ? { ...e, [field]: value } : e))
  }
  function addEquip() { setEquipment(prev => [...prev, emptyEquipment()]) }
  function removeEquip(idx: number) { setEquipment(prev => prev.filter((_, i) => i !== idx)) }

  // Method statement helpers
  function updateStep(idx: number, field: string, value: string) {
    setMethodStatement(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s))
  }
  function addStep() { setMethodStatement(prev => [...prev, emptyStep(prev.length + 1)]) }
  function removeStep(idx: number) {
    setMethodStatement(prev => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_number: i + 1 })))
  }

  // Permit helpers
  function updatePermit(idx: number, field: string, value: string) {
    setPermits(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p))
  }
  function addPermit() { setPermits(prev => [...prev, emptyPermit()]) }
  function removePermit(idx: number) { setPermits(prev => prev.filter((_, i) => i !== idx)) }

  // Apply AI suggested content to a section
  function applySuggestion(section: string, content: string) {
    const append = (prev: string, next: string) => prev ? `${prev}\n\n${next}` : next
    switch (section) {
      case 'job_details':
        setJobDetails((p: any) => ({ ...p, job_description: append(p.job_description || '', content) }))
        break
      case 'personnel':
        setPersonnel(prev => {
          const first = prev[0]
          if (first && !first.name && !first.role) return [{ ...first, name: content.split(',')[0]?.trim() || content, responsibilities: content }, ...prev.slice(1)]
          return [...prev, { ...emptyPerson(), name: 'AI Suggestion', responsibilities: content }]
        })
        break
      case 'equipment':
        setEquipment(prev => {
          const first = prev[0]
          if (first && !first.name) return [{ ...first, name: 'See notes', notes: content }, ...prev.slice(1)]
          return [...prev, { ...emptyEquipment(), name: 'See notes', notes: content }]
        })
        break
      case 'hazards':
        setHazards(prev => {
          const first = prev[0]
          if (first && !first.description && !first.controls) return [{ ...first, description: content }, ...prev.slice(1)]
          return [...prev, { ...emptyHazard(), description: content }]
        })
        break
      case 'method_statement':
        setMethodStatement(prev => {
          const first = prev[0]
          if (first && !first.description) return [{ ...first, description: content }, ...prev.slice(1)]
          return [...prev, { ...emptyStep(prev.length + 1), description: content }]
        })
        break
      case 'emergency_procedures':
        setEmergencyProcedures((p: any) => ({ ...p, evacuation_procedure: append(p.evacuation_procedure || '', content) }))
        break
      case 'environmental':
        setEnvironmental((p: any) => ({ ...p, waste_disposal: append(p.waste_disposal || '', content) }))
        break
      case 'permits':
        setPermits(prev => {
          const first = prev[0]
          if (first && !first.type) return [{ ...first, type: content }, ...prev.slice(1)]
          return [...prev, { ...emptyPermit(), type: content }]
        })
        break
      case 'monitoring':
        setMonitoring((p: any) => ({ ...p, review_schedule: append(p.review_schedule || '', content) }))
        break
    }
    scrollToSection(section)
    // Flash confirmation
    const label = ALL_SECTIONS.find(s => s.key === section)?.label || section
    setAppliedFlash(`Applied to ${label}`)
    setTimeout(() => setAppliedFlash(null), 2000)
  }

  // Section completion check
  function sectionHasContent(key: string): boolean {
    switch (key) {
      case 'job_details': return !!(jobDetails.client_name || jobDetails.site_address || jobDetails.job_description)
      case 'personnel': return personnel.some(p => p.name || p.role)
      case 'equipment': return equipment.some(e => e.name)
      case 'hazards': return hazards.some(h => h.description || h.controls)
      case 'method_statement': return methodStatement.some(s => s.description)
      case 'emergency_procedures': return !!(emergencyProcedures.emergency_contact || emergencyProcedures.evacuation_procedure)
      case 'environmental': return !!(environmental.waste_disposal || environmental.noise)
      case 'permits': return permits.some(p => p.type)
      case 'monitoring': return !!(monitoring.review_schedule || monitoring.signoff)
      default: return false
    }
  }

  if (loading) return <div className="empty-state">Loading RAMS…</div>
  if (!rams) return <div className="empty-state">RAMS document not found</div>

  const completedCount = ALL_SECTIONS.filter(s => isApplicable(s.key) && sectionHasContent(s.key)).length
  const totalApplicable = ALL_SECTIONS.filter(s => isApplicable(s.key)).length

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <a href="/admin/health-safety/rams" style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', textDecoration: 'none' }}>← RAMS</a>
          <span style={{ color: 'var(--color-text-muted)' }}>/</span>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="RAMS title" style={{ ...inputStyle, fontWeight: 700, fontSize: '1.05rem', border: 'none', borderBottom: '1px solid #e2e8f0', borderRadius: 0, padding: '0.2rem 0.4rem', maxWidth: 340 }} />
          <select value={ramsStatus} onChange={e => setRamsStatus(e.target.value)} style={{ ...inputSm, width: 'auto' }}>
            <option value="DRAFT">Draft</option>
            <option value="ACTIVE">Active</option>
            <option value="EXPIRED">Expired</option>
            <option value="ARCHIVED">Archived</option>
          </select>
          <input value={refNumber} onChange={e => setRefNumber(e.target.value)} placeholder="Ref #" style={{ ...inputSm, width: 100 }} />
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{completedCount}/{totalApplicable} sections</span>
          {saved && <span style={{ fontSize: '0.78rem', color: '#22c55e', fontWeight: 600 }}>✓ Saved</span>}
          {appliedFlash && <span style={{ fontSize: '0.78rem', color: '#6366f1', fontWeight: 600 }}>✨ {appliedFlash}</span>}
          <button className="btn btn-outline btn-sm" onClick={() => setShowPreview(p => !p)}>
            {showPreview ? '📝 Hide Preview' : '📄 Show Preview'}
          </button>
          <button className="btn btn-outline btn-sm" onClick={handleAiReview} disabled={aiLoading}>
            {aiLoading ? '🤖 Reviewing…' : '🤖 AI Review'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {/* ═══ AI Review Panel (always visible when available) ═══ */}
      {aiReview && (
        <div style={{ marginBottom: '1rem', padding: '1rem', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fafbfc' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.2rem', fontWeight: 800,
              background: (aiReview.score || 0) >= 7 ? '#dcfce7' : (aiReview.score || 0) >= 4 ? '#fef3c7' : '#fef2f2',
              color: (aiReview.score || 0) >= 7 ? '#15803d' : (aiReview.score || 0) >= 4 ? '#92400e' : '#991b1b',
            }}>
              {aiReview.score || '?'}/10
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', lineHeight: 1.3 }}>{aiReview.summary}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 3, flexWrap: 'wrap' }}>
                {aiReview.reviewed_at && <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Reviewed: {new Date(aiReview.reviewed_at).toLocaleString()}</span>}
                {aiReview.ai_powered === false && <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>Rule-based</span>}
                {reviewHistory.length > 0 && (
                  <span style={{ fontSize: '0.72rem', color: '#6366f1', fontWeight: 600 }}>
                    History: {reviewHistory.map((h, i) => `${h.score}/10`).join(' → ')} → {aiReview.score}/10
                  </span>
                )}
              </div>
            </div>
            {/* Mini risk matrix */}
            {(aiReview.overall_likelihood || aiReview.overall_severity) && (() => {
              const oL = aiReview.overall_likelihood || 3
              const oS = aiReview.overall_severity || 3
              const sc = oL * oS
              return (
                <div style={{ textAlign: 'center', flexShrink: 0 }}>
                  <div style={{ display: 'inline-block', padding: '0.3rem 0.75rem', borderRadius: 6, background: riskColour(sc), color: '#fff', fontWeight: 800, fontSize: '1rem' }}>
                    {sc}
                  </div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: riskColour(sc), textTransform: 'uppercase', marginTop: 2 }}>{riskLevel(sc)} risk</div>
                  <div style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>L{oL} × S{oS}</div>
                </div>
              )
            })()}
            <button className="btn btn-outline btn-sm" style={{ flexShrink: 0 }} onClick={handleAiReview} disabled={aiLoading}>
              {aiLoading ? '🤖 …' : '🔄 Re-run'}
            </button>
          </div>
          {/* Compact findings */}
          {aiReview.findings?.filter((f: any) => !f._dismissed).length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {aiReview.findings.map((f: any, i: number) => {
                if (f._dismissed) return null
                const sm = ALL_SECTIONS.find(s => s.key === f.section)
                return (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.3rem 0.5rem', borderRadius: 6, fontSize: '0.75rem',
                    background: f.severity === 'high' ? '#fef2f2' : f.severity === 'medium' ? '#fffbeb' : '#f8fafc',
                    border: `1px solid ${f.severity === 'high' ? '#fecaca' : f.severity === 'medium' ? '#fed7aa' : '#e2e8f0'}`,
                    cursor: 'pointer',
                  }} onClick={() => scrollToSection(f.section)} title={f.issue}>
                    <span style={{ fontWeight: 700, fontSize: '0.65rem', color: f.severity === 'high' ? '#991b1b' : f.severity === 'medium' ? '#92400e' : '#475569' }}>
                      {f.severity.toUpperCase()}
                    </span>
                    <span>{sm?.icon} {sm?.label || f.section}</span>
                    {f.suggested_content && (
                      <button className="btn btn-primary btn-sm" style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem', marginLeft: 4, fontWeight: 700 }}
                        onClick={(e) => { e.stopPropagation(); applySuggestion(f.section, f.suggested_content) }}
                        title={`Apply suggestion: ${f.suggested_content.slice(0, 80)}…`}>
                        ✨ Apply
                      </button>
                    )}
                    <button style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.7rem', color: 'var(--color-text-muted)', padding: 0 }}
                      onClick={(e) => { e.stopPropagation(); setAiReview({ ...aiReview, findings: aiReview.findings.map((ff: any, fi: number) => fi === i ? { ...ff, _dismissed: true } : ff) }) }}>✕</button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ═══ SPLIT PANE: Editor + Preview ═══ */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        {/* ── LEFT: Editor (accordion sections) ── */}
        <div style={{ flex: showPreview ? '0 0 55%' : 1, minWidth: 0 }}>

          {!aiReview && !aiLoading && (
            <div style={{ padding: '1rem', background: '#eff6ff', borderRadius: 8, border: '1px solid #bfdbfe', marginBottom: '1rem', fontSize: '0.85rem', color: '#1e40af' }}>
              <strong>💡 Getting started:</strong> Fill in the Job Details below with a description of the work. Then click <strong>🤖 AI Review</strong> — the AI will analyse what you&apos;ve written and suggest content for every section. You can apply suggestions with one click and keep iterating until the risk is acceptable.
            </div>
          )}

          {ALL_SECTIONS.map(sec => {
            if (!isApplicable(sec.key)) return null
            const isOpen = expanded[sec.key]
            const hasContent = sectionHasContent(sec.key)
            const finding = aiReview?.findings?.find((f: any) => f.section === sec.key && !f._dismissed)

            return (
              <div key={sec.key} id={`section-${sec.key}`} style={{ marginBottom: '0.5rem' }}>
                {/* Accordion header */}
                <button onClick={() => toggleExpand(sec.key)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '0.6rem 0.85rem', background: isOpen ? '#fff' : '#f8fafc',
                  border: `1px solid ${finding ? (finding.severity === 'high' ? '#fecaca' : '#fed7aa') : '#e2e8f0'}`,
                  borderRadius: isOpen ? '8px 8px 0 0' : 8, cursor: 'pointer', fontFamily: 'inherit',
                  borderLeft: finding ? `4px solid ${finding.severity === 'high' ? '#ef4444' : '#f59e0b'}` : '4px solid transparent',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ color: hasContent ? '#22c55e' : '#cbd5e1', fontSize: '0.85rem' }}>{hasContent ? '✓' : '○'}</span>
                    <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{sec.icon} {sec.label}</span>
                    {finding && <span className="badge badge-danger" style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem' }}>!</span>}
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}>▼</span>
                </button>
                {/* Accordion body */}
                {isOpen && (
                  <div style={{ border: '1px solid #e2e8f0', borderTop: 'none', borderRadius: '0 0 8px 8px', padding: '0.85rem', background: '#fff' }}>
                    {/* Finding banner if exists */}
                    {finding && (
                      <div style={{ padding: '0.5rem 0.65rem', marginBottom: '0.65rem', borderRadius: 6, fontSize: '0.8rem',
                        background: finding.severity === 'high' ? '#fef2f2' : '#fffbeb',
                        border: `1px solid ${finding.severity === 'high' ? '#fecaca' : '#fed7aa'}`,
                      }}>
                        <div style={{ fontWeight: 600, marginBottom: 2 }}>{finding.issue}</div>
                        <div style={{ color: '#475569', fontSize: '0.78rem' }}>💡 {finding.recommendation}</div>
                        {finding.suggested_content && (
                          <button className="btn btn-primary btn-sm" style={{ marginTop: '0.4rem', fontSize: '0.72rem' }}
                            onClick={() => applySuggestion(sec.key, finding.suggested_content)}>
                            ✨ Apply AI suggestion
                          </button>
                        )}
                      </div>
                    )}

                    {/* Section fields */}
                    {sec.key === 'job_details' && (
                      <>
                        <FormRow label="Client / Company Name"><input value={jobDetails.client_name || ''} onChange={e => setJobDetails((p: any) => ({ ...p, client_name: e.target.value }))} style={inputStyle} placeholder="e.g. Acme Construction Ltd" /></FormRow>
                        <FormRow label="Site Address"><textarea value={jobDetails.site_address || ''} onChange={e => setJobDetails((p: any) => ({ ...p, site_address: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Full site address" /></FormRow>
                        <FormRow label="Job Description"><textarea value={jobDetails.job_description || ''} onChange={e => setJobDetails((p: any) => ({ ...p, job_description: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={3} placeholder="Describe the scope of work — be as specific as possible for a better AI review" /></FormRow>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                          <FormRow label="Start Date"><input type="date" value={jobDetails.start_date || ''} onChange={e => setJobDetails((p: any) => ({ ...p, start_date: e.target.value }))} style={inputStyle} /></FormRow>
                          <FormRow label="End Date"><input type="date" value={jobDetails.end_date || ''} onChange={e => setJobDetails((p: any) => ({ ...p, end_date: e.target.value }))} style={inputStyle} /></FormRow>
                        </div>
                        <FormRow label="Principal Contractor"><input value={jobDetails.principal_contractor || ''} onChange={e => setJobDetails((p: any) => ({ ...p, principal_contractor: e.target.value }))} style={inputStyle} placeholder="If applicable" /></FormRow>
                      </>
                    )}
                    {sec.key === 'personnel' && (
                      <>
                        {personnel.map((p, idx) => (
                          <div key={idx} style={{ padding: '0.5rem', marginBottom: '0.4rem', background: '#f8fafc', borderRadius: 6 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>Person {idx + 1}</span>
                              {personnel.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', fontSize: '0.72rem' }} onClick={() => removePerson(idx)}>✕</button>}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                              <input placeholder="Name" value={p.name} onChange={e => updatePerson(idx, 'name', e.target.value)} style={inputStyle} />
                              <input placeholder="Role / Trade" value={p.role} onChange={e => updatePerson(idx, 'role', e.target.value)} style={inputStyle} />
                              <input placeholder="Qualifications" value={p.qualifications} onChange={e => updatePerson(idx, 'qualifications', e.target.value)} style={inputStyle} />
                              <input placeholder="Responsibilities" value={p.responsibilities} onChange={e => updatePerson(idx, 'responsibilities', e.target.value)} style={inputStyle} />
                            </div>
                          </div>
                        ))}
                        <button className="btn btn-outline btn-sm" onClick={addPerson}>+ Add Person</button>
                      </>
                    )}
                    {sec.key === 'equipment' && (
                      <>
                        {equipment.map((eq, idx) => (
                          <div key={idx} style={{ padding: '0.5rem', marginBottom: '0.4rem', background: '#f8fafc', borderRadius: 6 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>Item {idx + 1}</span>
                              {equipment.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', fontSize: '0.72rem' }} onClick={() => removeEquip(idx)}>✕</button>}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                              <input placeholder="Equipment name" value={eq.name} onChange={e => updateEquip(idx, 'name', e.target.value)} style={inputStyle} />
                              <input placeholder="Inspection date" type="date" value={eq.inspection_date} onChange={e => updateEquip(idx, 'inspection_date', e.target.value)} style={inputStyle} />
                              <input placeholder="Certificate ref" value={eq.cert_ref} onChange={e => updateEquip(idx, 'cert_ref', e.target.value)} style={inputStyle} />
                              <input placeholder="Notes" value={eq.notes} onChange={e => updateEquip(idx, 'notes', e.target.value)} style={inputStyle} />
                            </div>
                          </div>
                        ))}
                        <button className="btn btn-outline btn-sm" onClick={addEquip}>+ Add Equipment</button>
                      </>
                    )}
                    {sec.key === 'hazards' && (
                      <>
                        {hazards.map((h, idx) => {
                          const initSc = riskScore(h.initial_likelihood, h.initial_severity)
                          const resSc = riskScore(h.residual_likelihood, h.residual_severity)
                          return (
                            <div key={idx} style={{ padding: '0.65rem', marginBottom: '0.5rem', borderRadius: 6, borderLeft: `4px solid ${riskColour(resSc)}`, background: '#f8fafc' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                                <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Hazard #{idx + 1}</span>
                                <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
                                  <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', borderRadius: 3, background: riskColour(initSc), color: '#fff', fontWeight: 600 }}>Init: {initSc}</span>
                                  <span style={{ fontSize: '0.7rem' }}>→</span>
                                  <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', borderRadius: 3, background: riskColour(resSc), color: '#fff', fontWeight: 600 }}>Res: {resSc}</span>
                                  {hazards.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', fontSize: '0.72rem' }} onClick={() => removeHazard(idx)}>✕</button>}
                                </div>
                              </div>
                              <textarea placeholder="Describe the hazard…" value={h.description} onChange={e => updateHazard(idx, 'description', e.target.value)} style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.3rem' }} rows={2} />
                              <textarea placeholder="Controls in place…" value={h.controls} onChange={e => updateHazard(idx, 'controls', e.target.value)} style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.3rem' }} rows={2} />
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                <div>
                                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 2 }}>Initial Risk</div>
                                  <div style={{ display: 'flex', gap: '0.3rem' }}>
                                    <RiskSelect label="L" value={h.initial_likelihood} onChange={v => updateHazard(idx, 'initial_likelihood', v)} />
                                    <RiskSelect label="S" value={h.initial_severity} onChange={v => updateHazard(idx, 'initial_severity', v)} />
                                  </div>
                                </div>
                                <div>
                                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 2 }}>Residual Risk</div>
                                  <div style={{ display: 'flex', gap: '0.3rem' }}>
                                    <RiskSelect label="L" value={h.residual_likelihood} onChange={v => updateHazard(idx, 'residual_likelihood', v)} />
                                    <RiskSelect label="S" value={h.residual_severity} onChange={v => updateHazard(idx, 'residual_severity', v)} />
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                        <button className="btn btn-outline btn-sm" onClick={addHazard}>+ Add Hazard</button>
                      </>
                    )}
                    {sec.key === 'method_statement' && (
                      <>
                        {methodStatement.map((s, idx) => (
                          <div key={idx} style={{ padding: '0.5rem', marginBottom: '0.4rem', background: '#f8fafc', borderRadius: 6 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>Step {idx + 1}</span>
                              {methodStatement.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', fontSize: '0.72rem' }} onClick={() => removeStep(idx)}>✕</button>}
                            </div>
                            <textarea placeholder="Describe this step…" value={s.description} onChange={e => updateStep(idx, 'description', e.target.value)} style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.3rem' }} rows={2} />
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                              <input placeholder="Responsible" value={s.responsible} onChange={e => updateStep(idx, 'responsible', e.target.value)} style={inputStyle} />
                              <input placeholder="Hazard #s" value={s.hazard_refs} onChange={e => updateStep(idx, 'hazard_refs', e.target.value)} style={inputStyle} />
                            </div>
                          </div>
                        ))}
                        <button className="btn btn-outline btn-sm" onClick={addStep}>+ Add Step</button>
                      </>
                    )}
                    {sec.key === 'emergency_procedures' && (
                      <>
                        <FormRow label="Emergency Contact"><input value={emergencyProcedures.emergency_contact || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, emergency_contact: e.target.value }))} style={inputStyle} placeholder="Name and phone number" /></FormRow>
                        <FormRow label="First Aider(s)"><input value={emergencyProcedures.first_aiders || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, first_aiders: e.target.value }))} style={inputStyle} placeholder="Qualified first aiders on site" /></FormRow>
                        <FormRow label="Nearest Hospital / A&E"><input value={emergencyProcedures.nearest_hospital || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, nearest_hospital: e.target.value }))} style={inputStyle} placeholder="Name and address" /></FormRow>
                        <FormRow label="Evacuation Procedure"><textarea value={emergencyProcedures.evacuation_procedure || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, evacuation_procedure: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Describe the evacuation procedure" /></FormRow>
                        <FormRow label="Assembly Point"><input value={emergencyProcedures.assembly_point || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, assembly_point: e.target.value }))} style={inputStyle} /></FormRow>
                      </>
                    )}
                    {sec.key === 'environmental' && (
                      <>
                        <FormRow label="Waste Disposal"><textarea value={environmental.waste_disposal || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, waste_disposal: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="How waste will be managed" /></FormRow>
                        <FormRow label="Noise / Vibration"><textarea value={environmental.noise || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, noise: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Noise/vibration mitigations" /></FormRow>
                        <FormRow label="Protected Areas"><textarea value={environmental.protected_areas || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, protected_areas: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Watercourses, wildlife, etc." /></FormRow>
                        <FormRow label="Dust / Emissions"><textarea value={environmental.dust || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, dust: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Dust suppression" /></FormRow>
                      </>
                    )}
                    {sec.key === 'permits' && (
                      <>
                        {permits.map((p, idx) => (
                          <div key={idx} style={{ padding: '0.5rem', marginBottom: '0.4rem', background: '#f8fafc', borderRadius: 6 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>Permit {idx + 1}</span>
                              {permits.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', fontSize: '0.72rem' }} onClick={() => removePermit(idx)}>✕</button>}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
                              <input placeholder="Permit type" value={p.type} onChange={e => updatePermit(idx, 'type', e.target.value)} style={inputStyle} />
                              <input placeholder="Reference" value={p.reference} onChange={e => updatePermit(idx, 'reference', e.target.value)} style={inputStyle} />
                              <input placeholder="Issued by" value={p.issued_by} onChange={e => updatePermit(idx, 'issued_by', e.target.value)} style={inputStyle} />
                              <input placeholder="Expiry" type="date" value={p.expiry} onChange={e => updatePermit(idx, 'expiry', e.target.value)} style={inputStyle} />
                            </div>
                          </div>
                        ))}
                        <button className="btn btn-outline btn-sm" onClick={addPermit}>+ Add Permit</button>
                      </>
                    )}
                    {sec.key === 'monitoring' && (
                      <>
                        <FormRow label="Review Schedule"><textarea value={monitoring.review_schedule || ''} onChange={e => setMonitoring((p: any) => ({ ...p, review_schedule: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="How often will this RAMS be reviewed?" /></FormRow>
                        <FormRow label="Sign-off Requirements"><textarea value={monitoring.signoff || ''} onChange={e => setMonitoring((p: any) => ({ ...p, signoff: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Who needs to sign off?" /></FormRow>
                        <FormRow label="Toolbox Talk Records"><textarea value={monitoring.toolbox_talks || ''} onChange={e => setMonitoring((p: any) => ({ ...p, toolbox_talks: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Record of toolbox talks" /></FormRow>
                      </>
                    )}
                  </div>
                )}
              </div>
            )
          })}

          {/* Disclaimer */}
          <div style={{ marginTop: '1rem', padding: '0.65rem', borderRadius: 6, background: '#fffbeb', border: '1px solid #fcd34d', fontSize: '0.78rem', color: '#92400e' }}>
            <strong>⚠️ Important:</strong> This tool generates RAMS documents based on your input. All documents must be reviewed by a competent H&amp;S professional before use.
          </div>
        </div>

        {/* ── RIGHT: Live Document Preview ── */}
        {showPreview && (
          <div style={{ flex: '0 0 43%', position: 'sticky', top: 80, maxHeight: 'calc(100vh - 100px)', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 8, background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <div style={{ padding: '1.25rem', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
              {/* Document header */}
              <div style={{ textAlign: 'center', borderBottom: '2px solid #1e293b', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
                <h1 style={{ fontSize: '1.1rem', margin: '0 0 0.2rem', fontFamily: 'inherit', fontWeight: 800 }}>Risk Assessment &amp; Method Statement</h1>
                <h2 style={{ fontSize: '0.95rem', margin: 0, color: '#475569', fontFamily: 'inherit', fontWeight: 400 }}>{title || 'Untitled Document'}</h2>
                {refNumber && <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>Reference: {refNumber}</div>}
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>Status: {ramsStatus} | Generated: {new Date().toLocaleDateString('en-GB')}</div>
              </div>

              {/* AI Risk Rating */}
              {aiReview && (aiReview.overall_likelihood || aiReview.overall_severity) && (() => {
                const oL = aiReview.overall_likelihood || 3
                const oS = aiReview.overall_severity || 3
                const sc = oL * oS
                return (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', padding: '0.5rem', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.78rem' }}>Overall Risk:</span>
                    <span style={{ padding: '0.15rem 0.5rem', borderRadius: 4, background: riskColour(sc), color: '#fff', fontWeight: 700, fontSize: '0.8rem' }}>{sc}</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: riskColour(sc), textTransform: 'uppercase' }}>{riskLevel(sc)}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Score: {aiReview.score}/10</span>
                  </div>
                )
              })()}

              {/* Section previews */}
              {isApplicable('job_details') && (jobDetails.client_name || jobDetails.job_description) && (
                <PreviewSection title="1. Job Details">
                  {jobDetails.client_name && <PreviewField label="Client" value={jobDetails.client_name} />}
                  {jobDetails.site_address && <PreviewField label="Site" value={jobDetails.site_address} />}
                  {jobDetails.job_description && <PreviewField label="Description" value={jobDetails.job_description} />}
                  {(jobDetails.start_date || jobDetails.end_date) && <PreviewField label="Duration" value={`${jobDetails.start_date || '?'} to ${jobDetails.end_date || '?'}`} />}
                  {jobDetails.principal_contractor && <PreviewField label="Principal Contractor" value={jobDetails.principal_contractor} />}
                </PreviewSection>
              )}

              {isApplicable('personnel') && personnel.some(p => p.name) && (
                <PreviewSection title="2. Personnel">
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                    <thead><tr style={{ borderBottom: '1px solid #e2e8f0' }}><th style={pTh}>Name</th><th style={pTh}>Role</th><th style={pTh}>Qualifications</th></tr></thead>
                    <tbody>{personnel.filter(p => p.name).map((p, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}><td style={pTd}>{p.name}</td><td style={pTd}>{p.role}</td><td style={pTd}>{p.qualifications}</td></tr>
                    ))}</tbody>
                  </table>
                </PreviewSection>
              )}

              {isApplicable('equipment') && equipment.some(e => e.name) && (
                <PreviewSection title="3. Equipment">
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                    <thead><tr style={{ borderBottom: '1px solid #e2e8f0' }}><th style={pTh}>Equipment</th><th style={pTh}>Cert Ref</th><th style={pTh}>Inspection</th></tr></thead>
                    <tbody>{equipment.filter(e => e.name).map((e, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}><td style={pTd}>{e.name}</td><td style={pTd}>{e.cert_ref}</td><td style={pTd}>{e.inspection_date}</td></tr>
                    ))}</tbody>
                  </table>
                </PreviewSection>
              )}

              {isApplicable('hazards') && hazards.some(h => h.description) && (
                <PreviewSection title="4. Hazards & Controls">
                  {hazards.filter(h => h.description).map((h, i) => (
                    <div key={i} style={{ marginBottom: '0.5rem', paddingLeft: '0.5rem', borderLeft: `3px solid ${riskColour(riskScore(h.residual_likelihood, h.residual_severity))}` }}>
                      <div style={{ fontWeight: 600, fontSize: '0.78rem' }}>Hazard {i + 1}: {h.description}</div>
                      {h.controls && <div style={{ fontSize: '0.75rem', color: '#475569' }}>Controls: {h.controls}</div>}
                      <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                        Risk: {h.initial_likelihood}×{h.initial_severity}={riskScore(h.initial_likelihood, h.initial_severity)} → {h.residual_likelihood}×{h.residual_severity}={riskScore(h.residual_likelihood, h.residual_severity)}
                      </div>
                    </div>
                  ))}
                </PreviewSection>
              )}

              {isApplicable('method_statement') && methodStatement.some(s => s.description) && (
                <PreviewSection title="5. Method Statement">
                  {methodStatement.filter(s => s.description).map((s, i) => (
                    <div key={i} style={{ fontSize: '0.78rem', marginBottom: '0.3rem' }}>
                      <strong>Step {i + 1}:</strong> {s.description}
                      {s.responsible && <span style={{ color: '#64748b' }}> ({s.responsible})</span>}
                    </div>
                  ))}
                </PreviewSection>
              )}

              {isApplicable('emergency_procedures') && (emergencyProcedures.emergency_contact || emergencyProcedures.evacuation_procedure) && (
                <PreviewSection title="6. Emergency Procedures">
                  {emergencyProcedures.emergency_contact && <PreviewField label="Contact" value={emergencyProcedures.emergency_contact} />}
                  {emergencyProcedures.first_aiders && <PreviewField label="First Aiders" value={emergencyProcedures.first_aiders} />}
                  {emergencyProcedures.nearest_hospital && <PreviewField label="Nearest A&E" value={emergencyProcedures.nearest_hospital} />}
                  {emergencyProcedures.evacuation_procedure && <PreviewField label="Evacuation" value={emergencyProcedures.evacuation_procedure} />}
                  {emergencyProcedures.assembly_point && <PreviewField label="Assembly Point" value={emergencyProcedures.assembly_point} />}
                </PreviewSection>
              )}

              {isApplicable('environmental') && (environmental.waste_disposal || environmental.noise) && (
                <PreviewSection title="7. Environmental">
                  {environmental.waste_disposal && <PreviewField label="Waste" value={environmental.waste_disposal} />}
                  {environmental.noise && <PreviewField label="Noise" value={environmental.noise} />}
                  {environmental.protected_areas && <PreviewField label="Protected Areas" value={environmental.protected_areas} />}
                  {environmental.dust && <PreviewField label="Dust" value={environmental.dust} />}
                </PreviewSection>
              )}

              {isApplicable('permits') && permits.some(p => p.type) && (
                <PreviewSection title="8. Permits to Work">
                  {permits.filter(p => p.type).map((p, i) => (
                    <div key={i} style={{ fontSize: '0.78rem', marginBottom: 2 }}>{p.type} — Ref: {p.reference || '—'} (Expires: {p.expiry || '—'})</div>
                  ))}
                </PreviewSection>
              )}

              {isApplicable('monitoring') && (monitoring.review_schedule || monitoring.signoff) && (
                <PreviewSection title="9. Monitoring & Review">
                  {monitoring.review_schedule && <PreviewField label="Review" value={monitoring.review_schedule} />}
                  {monitoring.signoff && <PreviewField label="Sign-off" value={monitoring.signoff} />}
                  {monitoring.toolbox_talks && <PreviewField label="Toolbox Talks" value={monitoring.toolbox_talks} />}
                </PreviewSection>
              )}

              {/* 5×5 Risk Matrix */}
              {hazards.some(h => h.description) && (
                <PreviewSection title="Risk Matrix (5×5)">
                  <RiskMatrix5x5 hazards={hazards} />
                </PreviewSection>
              )}

              {/* Empty state */}
              {!sectionHasContent('job_details') && !sectionHasContent('hazards') && (
                <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                  Start filling in sections on the left — the document preview will appear here as you type.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Sub-components ──

function PreviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '0.85rem' }}>
      <h3 style={{ fontSize: '0.82rem', fontWeight: 700, margin: '0 0 0.35rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.2rem', fontFamily: 'inherit' }}>{title}</h3>
      {children}
    </div>
  )
}

const LIKELIHOOD_LABELS: Record<number, string> = { 1: 'Rare', 2: 'Unlikely', 3: 'Possible', 4: 'Likely', 5: 'Almost Certain' }
const SEVERITY_LABELS: Record<number, string> = { 1: 'Minor', 2: 'Low', 3: 'Moderate', 4: 'Major', 5: 'Catastrophic' }

function matrixBandColour(score: number): string {
  if (score <= 5) return '#22c55e'  // green — Low
  if (score <= 10) return '#eab308' // yellow — Moderate
  if (score <= 16) return '#f97316' // orange — High
  return '#ef4444'                  // red — Very High
}
function RiskMatrix5x5({ hazards }: { hazards: any[] }) {
  // Build set of hazard risk scores to highlight on matrix
  const initialScores = new Set<number>()
  const residualScores = new Set<number>()
  hazards.filter(h => h.description).forEach(h => {
    initialScores.add(h.initial_likelihood * h.initial_severity)
    residualScores.add(h.residual_likelihood * h.residual_severity)
  })

  const cellSize = 36
  const headerW = 62
  const mc: React.CSSProperties = {
    width: cellSize, height: cellSize, display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 700, fontSize: '0.72rem', color: '#fff', border: '1px solid rgba(255,255,255,0.3)',
    position: 'relative',
  }

  return (
    <div>
      <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '0.4rem' }}>Risk Rating = Likelihood × Severity</div>
      <div style={{ display: 'flex' }}>
        {/* Y-axis label */}
        <div style={{ width: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', fontSize: '0.62rem', fontWeight: 700, color: '#475569', letterSpacing: 1 }}>LIKELIHOOD</span>
        </div>
        <div>
          {/* Header row */}
          <div style={{ display: 'flex', marginLeft: headerW }}>
            {[1,2,3,4,5].map(s => (
              <div key={s} style={{ width: cellSize, textAlign: 'center', fontSize: '0.58rem', fontWeight: 600, color: '#475569', lineHeight: 1.2, padding: '0 1px' }}>
                {s}<br/><span style={{ fontWeight: 400 }}>{SEVERITY_LABELS[s]}</span>
              </div>
            ))}
          </div>
          {/* Matrix rows: likelihood 5 down to 1 */}
          {[5,4,3,2,1].map(l => (
            <div key={l} style={{ display: 'flex' }}>
              <div style={{ width: headerW, display: 'flex', alignItems: 'center', fontSize: '0.58rem', fontWeight: 600, color: '#475569', paddingRight: 4, justifyContent: 'flex-end', lineHeight: 1.2 }}>
                <span>{l} {LIKELIHOOD_LABELS[l]}</span>
              </div>
              {[1,2,3,4,5].map(s => {
                const score = l * s
                const bg = matrixBandColour(score)
                const isInitial = initialScores.has(score)
                const isResidual = residualScores.has(score)
                return (
                  <div key={s} style={{ ...mc, background: bg }}>
                    {score}
                    {isInitial && <span style={{ position: 'absolute', top: 1, right: 2, fontSize: '0.5rem', color: '#fff', fontWeight: 800 }}>●</span>}
                    {isResidual && <span style={{ position: 'absolute', bottom: 1, left: 2, fontSize: '0.5rem', color: '#fff', fontWeight: 800 }}>○</span>}
                  </div>
                )
              })}
            </div>
          ))}
          {/* X-axis label */}
          <div style={{ textAlign: 'center', marginLeft: headerW, fontSize: '0.62rem', fontWeight: 700, color: '#475569', marginTop: 2, letterSpacing: 1 }}>SEVERITY</div>
        </div>
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.5rem', flexWrap: 'wrap', fontSize: '0.65rem' }}>
        {[
          { label: 'Low (1–5)', color: '#22c55e' },
          { label: 'Moderate (6–10)', color: '#eab308' },
          { label: 'High (12–16)', color: '#f97316' },
          { label: 'Very High (20–25)', color: '#ef4444' },
        ].map(b => (
          <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: b.color }} />
            <span style={{ color: '#475569' }}>{b.label}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <span style={{ fontWeight: 800, color: '#475569' }}>●</span>
          <span style={{ color: '#475569' }}>Initial</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <span style={{ fontWeight: 800, color: '#475569' }}>○</span>
          <span style={{ color: '#475569' }}>Residual</span>
        </div>
      </div>
    </div>
  )
}

function PreviewField({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ fontSize: '0.78rem', marginBottom: '0.2rem' }}>
      <strong>{label}:</strong> <span style={{ color: '#475569', whiteSpace: 'pre-wrap' }}>{value}</span>
    </div>
  )
}

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '0.55rem' }}>
      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.2rem' }}>{label}</label>
      {children}
    </div>
  )
}

function RiskSelect({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', marginBottom: 1 }}>{label}</div>
      <select
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ ...inputStyle, fontSize: '0.78rem', padding: '0.3rem 0.4rem' }}
      >
        {[1,2,3,4,5].map(n => (
          <option key={n} value={n}>{n} — {RISK_LABELS[n]}</option>
        ))}
      </select>
    </div>
  )
}

// ── Styles ──
const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.4rem 0.6rem', borderRadius: 6,
  border: '1px solid #e2e8f0', fontSize: '0.82rem', fontFamily: 'inherit',
  outline: 'none', boxSizing: 'border-box',
}

const inputSm: React.CSSProperties = {
  ...inputStyle, fontSize: '0.78rem', padding: '0.3rem 0.5rem',
}

const matrixCell: React.CSSProperties = {
  padding: '0.25rem 0.4rem', border: '1px solid #e2e8f0', fontSize: '0.72rem',
}

const pTh: React.CSSProperties = { textAlign: 'left', padding: '0.25rem 0.3rem', fontSize: '0.72rem', fontWeight: 600 }
const pTd: React.CSSProperties = { padding: '0.2rem 0.3rem', fontSize: '0.72rem' }
