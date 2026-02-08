# Prior Lessons — Extracted from Rev 1 (nbne_business)

## Architecture Lessons

### 1. Module-per-feature works well
- Rev 1 used 9 Django modules (tenants, bookings, payments, staff, comms, compliance, documents, crm, analytics)
- Each module is self-contained: models, serializers, views, urls, admin, tests, migrations
- Feature flags in CLIENT_CONFIG.json enable/disable modules per client
- **Carry forward:** Keep modular architecture, add RBAC layer on top

### 2. Frontend was vanilla HTML/CSS/JS — needs upgrading
- Rev 1 frontend: booking.html, staff.html, comms.html with plain JS controllers
- No component reuse, no shared state management, no SSR
- Demo fallback data was bolted on after the fact
- **Lesson:** Move to Next.js with React components, shared state, and proper routing
- **Lesson:** Demo data should be first-class from day one

### 3. Auth was single-password gate — insufficient for three tiers
- Rev 1 used a single ADMIN_PASSWORD env var with cookie-based auth
- No user model, no roles, no permission matrix
- Staff and owner shared the same access level
- **Lesson:** Need unified User model with role system (customer, staff, manager, owner)
- **Lesson:** Every API endpoint must enforce roles server-side

### 4. No real-time features
- Rev 1 comms module used REST polling for messages
- No WebSocket, no typing indicators, no presence
- **Lesson:** Chat needs WebSocket for real-time UX (ChatPlus reference)

### 5. HSE/Compliance was basic incident reporting only
- Rev 1 compliance module: IncidentReport, IncidentPhoto, SignOff, RAMSDocument
- No AI-guided assessments, no hazard detection, no regulatory reasoning
- **Lesson:** HSE module needs significant expansion per R&D Summary

### 6. Setup tooling was effective
- setup_client.py scaffolds clients from config, removes disabled modules
- validate_template.py catches forbidden strings, hardcoded values
- sync_modules.py keeps modules in sync
- **Carry forward:** Keep tooling approach, extend for three-tier validation

## UX Lessons

### 7. Mobile-first CSS worked but was inconsistent
- Each page had its own CSS file with duplicated patterns
- No design system or component library
- **Lesson:** Use Tailwind CSS or a consistent CSS architecture with shared variables

### 8. Navigation was flat — no tier awareness
- All admin pages were siblings in a single sidebar
- No concept of "staff sees X, owner sees Y"
- **Lesson:** Navigation must be role-scoped with three distinct UI contexts

## Deployment Lessons

### 9. Vercel + Railway split works
- Frontend on Vercel, backend on Railway
- API rewrites in next.config.js proxy requests
- **Carry forward:** Same deployment model, add per-tier domain routing

### 10. Secrets management was minimal
- Single .env.local with all secrets
- No separation between tiers
- **Lesson:** Separate secrets per tier, use environment-specific configs

## Security Lessons

### 11. No privilege escalation testing existed
- Rev 1 had no automated tests for access control
- A staff user could theoretically access owner endpoints
- **Lesson:** Implement automated RBAC tests for every endpoint

### 12. No audit trail
- No logging of who did what and when
- **Lesson:** Add audit log model and middleware for all write operations

## Data Lessons

### 13. Demo data was an afterthought
- Added to frontend JS files after initial build
- Not structured or comprehensive
- **Lesson:** Demo data should be a first-class module with realistic, interconnected records

### 14. Three example clients validated the template approach
- hair-salon, restaurant, health-club all scaffolded and validated
- Proves the multi-client architecture works
- **Carry forward:** Rebuild all three with tier separation
