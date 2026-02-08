# NBNE Business Platform — Revision 2

## Version
2.0.0

## Date
2026-02-08

## Goals

### Architecture
- Three-tier separation: Public (T1), Staff (T2), Owner/Admin (T3)
- Unified auth with RBAC (customer, staff, manager, owner roles)
- Server-side permission enforcement on all endpoints
- Next.js 14 frontend with scoped route groups

### Tier 1 — Public / Customer
- Marketing website with branding
- Online booking with Stripe payments
- Reviews and feedback forms
- Mobile-first responsive design

### Tier 2 — Staff / Operations
- Rotas and shift management
- Leave requests and approvals
- HSE compliance (AI-guided assessments, hazard detection, RAMS)
- Training records and reminders
- CRM lead management
- Real-time team chat (ChatPlus-inspired: channels, typing indicators, read receipts, media)
- Job/task management

### Tier 3 — Owner / Management
- Staff administration and permissions
- Opening hours and deposit rules
- Compliance oversight and audit logs
- System configuration
- Analytics dashboard
- Full visibility across all tiers

### Chat System (ChatPlus-inspired)
- Real-time messaging with WebSocket
- Channel-based conversations (general, team, direct)
- Typing indicators and online status
- Read receipts and unread counts
- Image and file sharing with drag-and-drop
- Audio messages with speech-to-text
- Message search
- Mobile-optimised PWA interface

### HSE Module (R&D)
- AI-guided workplace video/photo assessments
- Automated hazard detection with severity scoring
- Regulatory reasoning engine (UK HSE mapping)
- Risk assessment and RAMS generation
- Risk-to-training mapping
- Compliance dashboard with scoring
- Action and remediation workflows
- Equipment inspection scheduling
- Incident and near-miss reporting
- Evidence and audit trail system

### Demo Clients
- **Salon X** — bookings, payments, staff, comms, analytics
- **Vitality Health Club** — bookings, payments, staff, comms, compliance, documents, analytics
- **The Kitchen Table** — bookings, staff, CRM, analytics

## Risks
- Real-time chat requires WebSocket infrastructure (Railway supports this)
- AI hazard detection requires external API integration (OpenAI Vision)
- Three-tier RBAC adds complexity to every endpoint
- HSE regulatory mapping needs ongoing maintenance
- Mobile PWA push notifications require service worker complexity
