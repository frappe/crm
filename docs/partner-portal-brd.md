# BRD — Partner Portal Integration
**Version:** 1.1  
**Date:** 2026-07-31  
**Author:** Salim  
**Status:** Draft — awaiting stakeholder review

**Changelog:**
- v1.1 — OQ-1 resolved (partners can create/manage Contacts). OQ-3 resolved (deal_owner auto-assigned per partner). Contact scope and user stories added.

---

## 1. Background & Business Context

Tiberbu operates a network of subcontracted **Partners** — external agents authorised to act on Tiberbu's behalf. Partners onboard new customers (Leads and Deals) through their own portal (the *Partner Portal*) and are expected to manage those customers' lifecycle stages over time.

Currently the CRM has no concept of a Partner. All Leads and Deals are internally owned. There is no audit trail linking a record to the partner who originated it, no scoped visibility for partners, and no structured API surface for external partner systems to push or pull data.

This BRD captures the full scope of what must be built inside Tiberbu CRM to support the Partner Portal integration.

---

## 2. Goals

| # | Goal |
|---|------|
| G1 | Partners can create Leads, Contacts, and Deals in the CRM on behalf of Tiberbu. |
| G2 | Every Lead and Deal created by a partner is permanently attributed to that partner. |
| G3 | Partners can update the lifecycle status of records they own. |
| G4 | Partners can query the current state of their records. |
| G5 | Tiberbu internal staff retain full visibility and override capability. |
| G6 | A partner cannot see or modify records owned by another partner. |
| G7 | The integration contract is stable, versioned, and documented in a single markdown the Partner Portal team can consume. |

---

## 3. Stakeholders

| Role | Person / Team | Interest |
|------|--------------|----------|
| Product Owner | Salim | Approval, scope |
| CRM Engineering | Tiberbu CRM team | Implementation |
| Partner Portal team | External / integration team | Consumer of the API |
| Partners | External agents | End-users of the portal |
| Sales Management | Tiberbu internal | Oversight, reporting |

---

## 4. Scope

### 4.1 In Scope

- New `CRM Partner` DocType — stores partner identity, API credentials, and metadata.
- `partner` (Link → CRM Partner) column on `CRM Lead` and `CRM Deal` — attribution field.
- New role **CRM Partner** — read/write scoped to own records only.
- API key + secret authentication for partner systems (uses Frappe's native API key auth).
- Whitelisted REST endpoints for: create/get/list leads, update lead status, convert lead to deal, create/get/list deals, update deal status, create/get/list/link contacts.
- `permission_query_conditions` enforcing partner scoping.
- Webhook dispatch on key lifecycle events (Won, Lost, Status Changed) — configurable per partner.
- Migration/fixture to seed the new role and DocType.
- Integration markdown for the Partner Portal team.

### 4.2 Out of Scope

- Partner Portal UI inside Tiberbu CRM (portal is external).
- OAuth2 / OIDC for partners (API key/secret is sufficient for a server-to-server integration).
- Partner billing or commission tracking.
- Real-time WebSocket push to partners (webhooks cover this).
- Contact ownership scoping — Contacts are shared/global across all Tiberbu users; partners can create and link them but do not have exclusive read/write access to Contact records.

---

## 5. User Stories

### US-01 — Partner creates a lead
> As a Partner Portal system, I want to POST a new lead to the CRM so that Tiberbu staff can work it, with the originating partner permanently recorded.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.create_lead` with valid API key creates a `CRM Lead`.
- `lead.partner` is set to the authenticated partner's name (server-side — not caller-supplied).
- `lead.source` is auto-set to `"Partner"` if no source is provided.
- `lead.lead_owner` is auto-set to `CRM Partner.default_deal_owner` if configured; otherwise left blank for manual/round-robin assignment.
- Response returns the new lead name and initial status.

### US-02 — Partner reads its leads
> As a Partner Portal system, I want to GET a list and detail of leads that belong to my partner account.

**Acceptance Criteria:**
- `GET /api/method/crm.api.partner.get_leads` returns only leads where `partner == authenticated_partner`.
- Supports pagination, status filter, date range.
- `GET /api/method/crm.api.partner.get_lead` returns a single lead, 403 if not owned.

### US-03 — Partner updates lead lifecycle
> As a Partner Portal system, I want to PATCH a lead's status so that the CRM reflects the customer's current stage.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.update_lead_status` accepts `lead_name` + `status`.
- Status must exist in `CRM Lead Status`. Invalid status returns 422.
- Partner can only update leads it owns. 403 otherwise.
- Change is recorded in `status_change_log` (existing mechanism).

### US-04 — Partner converts a lead to a deal
> As a Partner Portal system, I want to signal that a lead has progressed to a qualified deal.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.convert_lead` triggers the existing `convert_to_deal` logic.
- Resulting deal inherits `partner` from the originating lead.
- Response returns the new deal name.

### US-05 — Partner creates a deal directly
> As a Partner Portal system, I want to create a Deal directly (when the customer is already known/qualified).

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.create_deal` creates a `CRM Deal` with `partner` set.

### US-06 — Partner reads its deals
> As a Partner Portal system, I want to list and retrieve deals belonging to my account.

**Acceptance Criteria:**
- `GET /api/method/crm.api.partner.get_deals` and `get_deal` — partner-scoped, same pagination as leads.

### US-07 — Partner updates deal lifecycle
> As a Partner Portal system, I want to advance or regress a deal's status.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.update_deal_status` — validates status, enforces ownership.
- Lost deals require `lost_reason`; endpoint enforces this.

### US-08 — Partner creates a contact
> As a Partner Portal system, I want to create a Contact (a named individual associated with an organisation) so that multiple contacts at one company can be tracked against a Deal.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.create_contact` creates a Frappe `Contact` record.
- Contacts are shared/global — a contact may be linked to deals owned by different partners or by internal staff.
- Response returns the new contact `name` (Frappe Contact ID).
- Optional: immediately link the new contact to a deal via `deal_name` in the same request.

### US-09 — Partner links a contact to a deal
> As a Partner Portal system, I want to attach an existing contact to one of my deals.

**Acceptance Criteria:**
- `POST /api/method/crm.api.partner.add_contact_to_deal` adds the contact to the deal's `contacts` child table.
- Partner must own the deal; 403 otherwise.
- Duplicate link (contact already on deal) returns 200 idempotently without error.
- Optionally set the contact as primary (`set_primary=true`).

### US-10 — Partner reads contacts on a deal
> As a Partner Portal system, I want to retrieve all contacts associated with one of my deals.

**Acceptance Criteria:**
- `GET /api/method/crm.api.partner.get_deal_contacts` returns all contacts linked to the deal.
- Partner must own the deal; 403 otherwise.

### US-12 — Tiberbu staff sees partner attribution
> As a Tiberbu Sales Manager, I want to see which partner sourced a Lead or Deal so I can measure partner performance.

**Acceptance Criteria:**
- `partner` field visible in Lead and Deal list views and detail views.
- Filterable from the CRM UI.
- Reportable via the dashboard.

### US-13 — Partner receives webhooks on lifecycle events
> As a Partner Portal system, I want to receive a POST callback when a lead or deal I own changes status.

**Acceptance Criteria:**
- `CRM Partner` has a `webhook_url` + `webhook_secret` field.
- On `CRM Lead.on_update` and `CRM Deal.on_update`, if `status` changed and record has a partner, enqueue a signed POST to `partner.webhook_url`.
- Payload is HMAC-SHA256 signed with `webhook_secret` in `X-Tiberbu-Signature` header.
- Delivery is retried up to 3 times with exponential back-off.

### US-14 — Partner credential management
> As a Tiberbu System Manager, I want to issue and revoke API credentials for each partner.

**Acceptance Criteria:**
- `CRM Partner` DocType has `api_key` and `api_secret` fields (or links to Frappe's `User` with API key).
- Manager can disable a partner account; all subsequent requests from that partner return 403.
- Partner records are not deletable if they have associated Leads or Deals (Link validation).

---

## 6. Data Model Changes

### 6.1 New DocType: `CRM Partner`

| Field | Type | Notes |
|-------|------|-------|
| partner_name | Data | Required, unique, title field |
| status | Select | Active / Inactive |
| email | Data (Email) | Primary contact email |
| phone | Data (Phone) | |
| website | Data | |
| territory | Link → CRM Territory | Optional scoping |
| webhook_url | Data | HTTPS only |
| webhook_secret | Password | Auto-generated on save |
| default_deal_owner | Link → User | Tiberbu user auto-assigned as lead_owner/deal_owner for this partner's records |
| api_user | Link → User | Frappe user that holds the API key/secret |
| notes | Text | Internal notes |

**Roles:** System Manager — full CRUD. CRM Partner — read own record only.

### 6.2 Modified DocType: `CRM Lead`

| New Field | Type | Notes |
|-----------|------|-------|
| partner | Link → CRM Partner | In list view, in standard filter, search index |
| partner_ref | Data | Partner's own reference ID (idempotency key) |

### 6.3 Modified DocType: `CRM Deal`

| New Field | Type | Notes |
|-----------|------|-------|
| partner | Link → CRM Partner | In list view, in standard filter, search index |
| partner_ref | Data | Partner's own reference ID |

### 6.4 Contacts

No new fields on the Frappe `Contact` DocType. Partners create standard Contact records. The `add_contact_to_deal` endpoint writes to the `CRM Contacts` child table on `CRM Deal` (existing mechanism used internally by `crm.fcrm.doctype.crm_deal.crm_deal.add_contact`).

### 6.5 New Source Seed

Add `"Partner"` to `CRM Lead Source` fixture so all partner-originated records are reportable by source.

---

## 7. Permission Model

### 7.1 New Role: `CRM Partner`

- Granted to the Frappe `User` linked from `CRM Partner.api_user`.
- `CRM Lead`: read, write, create — scoped to `partner == current_partner_name`.
- `CRM Deal`: read, write, create — scoped to `partner == current_partner_name`.
- `Contact`: create, read — global (no partner scoping; contacts are shared).
- `CRM Partner`: read own record only.
- No access to CRM Settings, User management, Dashboard, Notifications, or any other doctype.

### 7.2 `permission_query_conditions` (Python)

```python
# crm/permissions/partner_scoping.py
def partner_lead_conditions(user):
    partner = get_partner_for_user(user)
    if not partner:
        return ""  # fall through to org_hierarchy scoping
    return f"`tabCRM Lead`.`partner` = {frappe.db.escape(partner)}"

def partner_deal_conditions(user):
    partner = get_partner_for_user(user)
    if not partner:
        return ""
    return f"`tabCRM Deal`.`partner` = {frappe.db.escape(partner)}"
```

Registered in `hooks.py` under `permission_query_conditions` alongside the existing org hierarchy conditions.

### 7.3 API authentication

Partners authenticate using Frappe's native API key/secret mechanism:
```
Authorization: token <api_key>:<api_secret>
```
The `api_user` linked from `CRM Partner` holds the credentials. The `get_partner_for_user()` helper resolves `frappe.session.user → CRM Partner.api_user → CRM Partner`.

---

## 8. New API Module: `crm/api/partner.py`

All endpoints are whitelisted under `crm.api.partner.*`. Each enforces:
1. Caller is a valid CRM Partner (helper raises 403 otherwise).
2. Record-level ownership (partner on record == caller's partner).

| Method | HTTP | Endpoint | Description |
|--------|------|----------|-------------|
| POST | POST | `crm.api.partner.create_lead` | Create a new lead attributed to caller |
| GET | GET | `crm.api.partner.get_lead` | Get single lead detail |
| GET | GET | `crm.api.partner.get_leads` | Paginated list of caller's leads |
| POST | POST | `crm.api.partner.update_lead_status` | Update lead lifecycle status |
| POST | POST | `crm.api.partner.convert_lead` | Convert lead to deal |
| POST | POST | `crm.api.partner.create_deal` | Create a new deal attributed to caller |
| GET | GET | `crm.api.partner.get_deal` | Get single deal detail |
| GET | GET | `crm.api.partner.get_deals` | Paginated list of caller's deals |
| POST | POST | `crm.api.partner.update_deal_status` | Update deal lifecycle status |
| POST | POST | `crm.api.partner.create_contact` | Create a new Contact (optionally link to a deal) |
| GET | GET | `crm.api.partner.get_deal_contacts` | List all contacts on a partner-owned deal |
| POST | POST | `crm.api.partner.add_contact_to_deal` | Link an existing contact to a partner-owned deal |
| GET | GET | `crm.api.partner.get_lead_statuses` | List all valid lead statuses |
| GET | GET | `crm.api.partner.get_deal_statuses` | List all valid deal statuses |

---

## 9. Webhooks

| Event | Trigger | Payload fields |
|-------|---------|---------------|
| `lead.status_changed` | CRM Lead on_update, status changed | lead_name, partner_ref, old_status, new_status, timestamp |
| `lead.converted` | CRM Lead converted=1 | lead_name, partner_ref, deal_name, timestamp |
| `deal.status_changed` | CRM Deal on_update, status changed | deal_name, partner_ref, old_status, new_status, timestamp |
| `deal.won` | Deal status type == Won | deal_name, partner_ref, deal_value, closed_date, timestamp |
| `deal.lost` | Deal status type == Lost | deal_name, partner_ref, lost_reason, timestamp |

Delivery: `frappe.enqueue` → background job → HTTP POST with 10-second timeout. Retry 3× at 30s, 120s, 300s. Failed delivery logged in a `CRM Partner Webhook Log` child table (or standalone DocType).

Signature header: `X-Tiberbu-Signature: sha256=<hmac-hex>`

---

## 10. Non-Functional Requirements

| NFR | Requirement |
|-----|------------|
| Security | API key/secret transmitted only over HTTPS. Webhook secret never returned in API responses after creation. |
| Idempotency | `partner_ref` is a unique index per partner on both Lead and Deal. Duplicate `partner_ref` on create returns the existing record name with HTTP 200 rather than creating a duplicate. |
| Rate limiting | 300 requests/minute per API key (enforced at reverse proxy / Frappe rate limiter). |
| Audit | All partner API calls logged in Frappe's `Access Log`. |
| Backward compatibility | Existing internal users and API callers are unaffected. `partner` field is nullable; all existing permission logic is unchanged for non-partner users. |

---

## 11. Out-of-scope Decisions Deferred

- Partner performance reporting / dashboard — Phase 2.
- Partner-to-partner referral chain — Phase 2.
- Self-service partner registration (Partners created by Tiberbu Admin only in v1).

---

## 12. Acceptance Criteria (Story of Record)

The feature is **done** when:
1. `CRM Partner` DocType exists and is accessible to System Manager.
2. `partner` field visible on Lead and Deal list views, filterable.
3. A partner API key can create a Lead; `partner` on the record equals the authenticated partner.
4. Lead `lead_owner` and Deal `deal_owner` are auto-assigned to `CRM Partner.default_deal_owner` when set.
5. A partner cannot read or modify another partner's records (403).
6. `update_lead_status` and `update_deal_status` write to `status_change_log`.
7. `convert_lead` produces a Deal inheriting `partner`.
8. A partner can create a Contact and link it to their Deal; contact is visible to all internal users.
9. A webhook POST is delivered (or logged-failed-and-retried) on status change.
10. `partner_ref` deduplication works — second create with same ref returns existing record name.
11. Internal Sales Manager sees all records regardless of `partner`.
12. `pnpm build` and `tsc --noEmit` pass (for any frontend changes).

---

## 13. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| OQ-1 | Should partners be able to create Contacts, or only Leads/Deals? | Salim | **Resolved — Yes.** Partners are full sales agents; Contact creation is in scope. |
| OQ-2 | Is there a maximum number of Leads a partner can create per day (quota)? | Salim | Open |
| OQ-3 | Should `deal_owner` auto-assign to a specific Tiberbu user per partner? | Sales Mgmt | **Resolved — Yes.** `CRM Partner.default_deal_owner` field added; auto-assigned on lead/deal create. |
| OQ-4 | Which Lead/Deal fields are writeable by a partner on update (beyond status)? | Salim | Open |
| OQ-5 | Should the Partner Portal receive full deal value on `deal.won` or only status? | Partner Portal team | **Resolved — Full value.** `deal_value` and `currency` included in `deal.won` webhook payload. |
