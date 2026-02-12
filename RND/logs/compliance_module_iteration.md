# R&D Log — UK Health & Safety Compliance Module

## Date: 2026-02-12
## Module: compliance (NBNE Platform Rev 2)
## Author: Principal Engineer (Cascade)

---

## 1. Architecture Decisions

### Data Model Design
- **ComplianceCategory** acts as the grouping layer with `legal_requirement` flag to distinguish statutory obligations from best practice.
- **ComplianceItem** is the core scheduling unit with `frequency_type` enum covering UK standard intervals (weekly fire alarm tests, annual reviews, 3-year first aid, 5-year EICR).
- **TrainingRecord** is separate from ComplianceItem because training has a different lifecycle (per-user, certificate-based, provider-tracked) vs compliance items (per-business, action-based).
- **DocumentVault** implements version chaining via `supersedes` FK rather than a separate version table — simpler, avoids orphan cleanup.
- **ComplianceActionLog** provides a unified audit trail across all compliance actions, separate from the platform-wide AuditEntry to allow compliance-specific filtering.

### RBAC Enforcement
- **Tier 2 (Staff)**: Can report incidents, upload evidence, view own training, view assigned actions.
- **Tier 3 (Manager/Owner)**: Full CRUD on all compliance entities, dashboard, calendar, CSV export, document vault, training management.
- All permission checks are server-side via DRF `@permission_classes`. No client-side gating relied upon.

### Scheduling Engine
- `update_compliance_status` management command designed for daily cron execution.
- Status transitions are deterministic: overdue if `next_due_date < today`, due_soon if within 30 days, compliant otherwise.
- `mark_completed()` auto-calculates next due date based on frequency, creating a perpetual compliance cycle.

---

## 2. UK Regulation Interpretation — Uncertainties

### RIDDOR Reporting
- **Uncertainty**: The system flags incidents as `riddor_reportable` (boolean) but does NOT auto-submit to HSE. RIDDOR 2013 requires reporting within specific timeframes (10 days for most, immediate for fatalities/specified injuries). The system records the flag but the actual HSE notification remains a manual process.
- **Decision**: Flag-only approach. Auto-submission would require HSE API integration which is out of scope and carries legal liability risk.

### Frequency Assumptions
- **Fire alarm test**: Set to weekly per BS 5839-1. Some premises may test fortnightly — the `custom_days` option covers this.
- **PAT testing**: Set to annual as a conservative default. IET Code of Practice actually varies by equipment type and environment (office equipment may be 2-4 years). Users can override via custom frequency.
- **First Aid requalification**: Set to 3 years per HSE guidance. Annual refresher courses are recommended but not mandatory — not tracked separately.
- **EICR (fixed wiring)**: Set to 5 years per BS 7671. Commercial premises may require more frequent testing.

### Status Thresholds
- **30-day "due soon" window**: This is an assumption. UK law doesn't specify a warning period. 30 days was chosen as a reasonable lead time for arranging inspections/training. This is configurable by changing the threshold in `update_status()`.
- **Uncertainty**: Some items (e.g., weekly fire alarm tests) will transition to "due soon" almost immediately after completion. This is technically correct but may cause alert fatigue. Future improvement: make threshold proportional to frequency.

### Employers' Liability Insurance
- **Legal requirement**: Employers' Liability (Compulsory Insurance) Act 1969 requires display of certificate. The system tracks expiry but cannot verify the certificate is physically displayed. This remains a manual check.

---

## 3. Reminder Timing Logic

### Trigger Points
- 30 days before due (planning window)
- 7 days before due (action required)
- 1 day before due (urgent)
- Daily for overdue items (escalation)

### Uncertainty
- Email delivery depends on SMTP configuration. If email fails, the `ComplianceActionLog` still records the attempt.
- Push notifications (PWA) are not yet implemented — would require service worker integration with the existing comms module's push subscription system.
- **Risk**: Over-notification for weekly items. A fire alarm test due every 7 days would trigger a "due soon" reminder almost immediately. Future improvement: suppress reminders for items with frequency < 30 days.

---

## 4. Known Limitations

1. **No tenant FK on models**: Current implementation does not add tenant FK to compliance models. In the current deployment, each Railway instance serves one tenant, so isolation is at the infrastructure level. If multi-tenant-per-database is needed, tenant FK must be added to all models and all querysets must filter by tenant.

2. **No offline incident drafts**: The PWA offline capability for incident reporting (saving drafts in IndexedDB and syncing when online) is not implemented. This requires service worker modifications.

3. **No file upload from frontend**: The document vault and training certificate upload endpoints exist in the API but the frontend forms don't yet include file upload widgets. The incident photo upload API is wired but needs camera integration on mobile.

4. **Calendar is list-based**: The calendar view is a sorted event list, not a visual calendar grid. A proper calendar component (e.g., FullCalendar) would improve UX.

5. **No automated risk classification**: The system relies on manual severity/status assignment. AI-assisted risk classification was considered but deferred due to regulatory interpretation concerns.

---

## 5. Next Improvements

1. **Proportional reminder thresholds** — Scale "due soon" window based on item frequency.
2. **PWA push notifications** — Integrate with existing `PushSubscription` model in comms module.
3. **Visual calendar** — Replace list view with FullCalendar or similar.
4. **File upload UI** — Add drag-and-drop upload for documents and training certificates.
5. **Offline incident drafts** — IndexedDB + service worker sync.
6. **Tenant FK** — Add when multi-tenant-per-database is required.
7. **Dashboard PDF export** — Generate compliance summary PDF for regulatory inspections.
8. **COSHH assessment module** — Dedicated sub-module for COSHH with substance register.

---

## 6. Baseline Items Created (15 items, 6 categories)

| Category | Legal | Items |
|----------|-------|-------|
| Fire Safety | Yes | Fire Risk Assessment, Fire Extinguisher Inspection, Fire Alarm Test, Emergency Lighting Test, Fire Marshal Training |
| Electrical Safety | Yes | Fixed Wiring Inspection (EICR), PAT Testing |
| Training | Yes | First Aid at Work Certificate, Manual Handling Training |
| General Compliance | Yes | H&S Policy Review, Risk Assessment Review, Employers Liability Insurance |
| Equipment | No | Gas Safety Check |
| Hygiene & Welfare | No | Workplace Welfare Facilities Check, COSHH Assessment Review |

---

## 7. Test Coverage

- **Model tests**: Frequency calculation, status transitions, mark_completed, auto-save next_due
- **Training tests**: Expired/expiring_soon/valid status properties
- **Document tests**: Version chaining, is_current flag management
- **RBAC tests**: 13 endpoint access tests across customer/staff/manager/owner roles
- **Action log tests**: Creation, completion, and incident logging verified
- **Baseline tests**: Seed idempotency, minimum item count verification
