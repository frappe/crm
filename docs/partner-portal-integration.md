# Tiberbu CRM — Partner Portal Integration Reference
**Version:** 1.1  
**Base URL:** `https://crm.tiberbu.app`  
**Protocol:** HTTPS only  
**Auth:** Token (API Key + Secret)  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Error Responses](#2-error-responses)
3. [Rate Limits](#3-rate-limits)
4. [Leads(Prospects)](#4-leads)
   - [Create Lead](#41-create-lead)
   - [Get Lead](#42-get-lead)
   - [List Leads](#43-list-leads)
   - [Update Lead Status](#44-update-lead-status)
   - [Convert Lead to Deal](#45-convert-lead-to-deal)
5. [Deals(Customer)](#5-deals)
   - [Create Deal](#51-create-deal)
   - [Get Deal](#52-get-deal)
   - [List Deals](#53-list-deals)
   - [Update Deal Status](#54-update-deal-status)
6. [Contacts](#6-contacts)
   - [Create Contact](#61-create-contact)
   - [Get Deal Contacts](#62-get-deal-contacts)
   - [Add Contact to Deal](#63-add-contact-to-deal)
7. [Reference Data](#7-reference-data)
   - [Lead Statuses](#71-lead-statuses)
   - [Deal Statuses](#72-deal-statuses)
8. [Webhooks](#8-webhooks)
   - [Webhook Events](#81-webhook-events)
   - [Payload Structure](#82-payload-structure)
   - [Signature Verification](#83-signature-verification)
   - [Retry Policy](#84-retry-policy)
9. [Field Reference](#9-field-reference)
   - [Lead Object](#91-lead-object)
   - [Deal Object](#92-deal-object)
   - [Contact Object](#93-contact-object)
10. [Idempotency](#10-idempotency)
11. [Lifecycle Diagrams](#11-lifecycle-diagrams)
12. [Changelog](#12-changelog)

---

## 1. Authentication

All requests must include an `Authorization` header using your API key and secret, separated by a colon:

```
Authorization: token <api_key>:<api_secret>
```

**Example:**
```http
GET /api/method/crm.api.partner.get_leads HTTP/1.1
Host: crm.tiberbu.com
Authorization: token abc123key:xyz789secret
```

Credentials are issued by Tiberbu and tied to your partner account. Contact your Tiberbu account manager to receive credentials or to rotate a compromised secret.

> **Security:** Never embed credentials in client-side code or share them across partner organisations. All calls must originate from your backend.

> **Owner assignment:** Each partner account has a configured Tiberbu internal user (`default_deal_owner`). All leads and deals you create are automatically assigned to that user for follow-up. If no owner is configured for your account, records are left unassigned until a Tiberbu manager allocates them.

---

## 2. Error Responses

All errors follow a consistent envelope:

```json
{
  "exc_type": "ValidationError",
  "exception": "crm.exceptions.PartnerAuthError",
  "message": "Human-readable description of the error"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| `200 OK` | Success |
| `400 Bad Request` | Missing or malformed parameter |
| `403 Forbidden` | Invalid credentials, inactive partner, or record not owned by caller |
| `404 Not Found` | Requested record does not exist |
| `409 Conflict` | Duplicate `partner_ref` (idempotency hit — see §9) |
| `422 Unprocessable Entity` | Business rule violation (e.g. invalid status value) |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error — contact Tiberbu support |

All successful responses wrap the payload in a `message` key (Frappe convention):

```json
{
  "message": { /* payload */ }
}
```

---

## 3. Rate Limits

| Limit | Value |
|-------|-------|
| Requests per minute (per API key) | 300 |
| Burst | Up to 50 requests in a 1-second window |

When exceeded, the server returns `429` with:
```json
{ "message": "Too many requests. Retry after 15 seconds." }
```

Honour the `Retry-After` response header when present.

---

## 4. Leads

A **Lead** represents an individual or organisation that has been identified as a potential customer but has not yet been formally qualified into a sales opportunity.

### 4.1 Create Lead

```
POST /api/method/crm.api.partner.create_lead
```

Creates a new CRM Lead attributed to the authenticated partner. The `partner` field on the record is set server-side from your API credentials — you cannot set it manually.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | Yes | Lead's first name |
| `last_name` | string | No | Lead's last name |
| `email` | string (email) | Yes | Primary email address |
| `mobile_no` | string | No | Mobile number (E.164 recommended) |
| `phone` | string | No | Landline number |
| `organization` | string | No | Company / organisation name |
| `job_title` | string | No | Lead's job title |
| `website` | string | No | Company website URL |
| `territory` | string | No | Territory name (must match a `CRM Territory` record) |
| `industry` | string | No | Industry name (must match a `CRM Industry` record) |
| `source` | string | No | Lead source — defaults to `"Partner"` if omitted |
| `annual_revenue` | number | No | Estimated annual revenue |
| `no_of_employees` | string | No | One of: `1-10`, `11-50`, `51-200`, `201-500`, `501-1000`, `1000+` |
| `partner_ref` | string | No | Your internal reference ID (idempotency key — see §9) |
| `products` | array | No | List of product objects `[{"item_code": "...", "qty": 1}]` |

**Example request:**
```json
{
  "first_name": "Amina",
  "last_name": "Wanjiku",
  "email": "amina.wanjiku@example.co.ke",
  "mobile_no": "+254712345678",
  "organization": "Savanna Tech Ltd",
  "job_title": "CEO",
  "website": "https://savannatech.co.ke",
  "territory": "East Africa",
  "industry": "Technology",
  "partner_ref": "PP-LEAD-2026-0042"
}
```

**Example response (201):**
```json
{
  "message": {
    "name": "CRM-LEAD-2026-00187",
    "status": "New Lead",
    "status_type": "Open",
    "partner": "Acme Partners Ltd",
    "partner_ref": "PP-LEAD-2026-0042",
    "lead_name": "Amina Wanjiku",
    "email": "amina.wanjiku@example.co.ke"
  }
}
```

---

### 4.2 Get Lead

```
GET /api/method/crm.api.partner.get_lead
```

Returns the full detail of a single lead owned by your partner account.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_name` | string | Yes* | CRM Lead ID (e.g. `CRM-LEAD-2026-00187`) |
| `partner_ref` | string | Yes* | Your internal reference ID |

*Either `lead_name` or `partner_ref` is required.

**Example request:**
```
GET /api/method/crm.api.partner.get_lead?lead_name=CRM-LEAD-2026-00187
```

**Example response (200):**
```json
{
  "message": {
    "name": "CRM-LEAD-2026-00187",
    "lead_name": "Amina Wanjiku",
    "first_name": "Amina",
    "last_name": "Wanjiku",
    "email": "amina.wanjiku@example.co.ke",
    "mobile_no": "+254712345678",
    "organization": "Savanna Tech Ltd",
    "job_title": "CEO",
    "status": "Contacted",
    "status_type": "Ongoing",
    "converted": 0,
    "deal_name": null,
    "partner": "Acme Partners Ltd",
    "partner_ref": "PP-LEAD-2026-0042",
    "source": "Partner",
    "territory": "East Africa",
    "industry": "Technology",
    "sla_status": "Fulfilled",
    "communication_status": "Replied",
    "creation": "2026-07-31T09:15:00",
    "modified": "2026-07-31T14:30:00"
  }
}
```

---

### 4.3 List Leads

```
GET /api/method/crm.api.partner.get_leads
```

Returns a paginated list of leads owned by the authenticated partner.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-indexed) |
| `page_size` | integer | `20` | Records per page (max 100) |
| `status` | string | — | Filter by status name (e.g. `"Contacted"`) |
| `status_type` | string | — | Filter by type: `Open`, `Ongoing`, `On Hold`, `Won`, `Lost` |
| `converted` | boolean | — | `true` to show only converted leads; `false` for unconverted |
| `from_date` | string (ISO 8601) | — | Creation date from (inclusive) |
| `to_date` | string (ISO 8601) | — | Creation date to (inclusive) |
| `order_by` | string | `"modified desc"` | Sort field and direction |

**Example request:**
```
GET /api/method/crm.api.partner.get_leads?page=1&page_size=20&status_type=Open
```

**Example response (200):**
```json
{
  "message": {
    "total": 147,
    "page": 1,
    "page_size": 20,
    "data": [
      {
        "name": "CRM-LEAD-2026-00187",
        "lead_name": "Amina Wanjiku",
        "email": "amina.wanjiku@example.co.ke",
        "organization": "Savanna Tech Ltd",
        "status": "New Lead",
        "status_type": "Open",
        "converted": 0,
        "partner_ref": "PP-LEAD-2026-0042",
        "creation": "2026-07-31T09:15:00",
        "modified": "2026-07-31T14:30:00"
      }
    ]
  }
}
```

---

### 4.4 Update Lead Status

```
POST /api/method/crm.api.partner.update_lead_status
```

Advances or changes the lifecycle status of a lead. The new status must exist in the CRM's configured lead statuses (see §6.1).

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lead_name` | string | Yes* | CRM Lead ID |
| `partner_ref` | string | Yes* | Your internal reference ID |
| `status` | string | Yes | Target status name (must be a valid `CRM Lead Status`) |
| `notes` | string | No | Optional notes recorded against this status change |

*Either `lead_name` or `partner_ref` required.

**Example request:**
```json
{
  "lead_name": "CRM-LEAD-2026-00187",
  "status": "Contacted",
  "notes": "Introductory call completed. Customer interested in the Starter plan."
}
```

**Example response (200):**
```json
{
  "message": {
    "name": "CRM-LEAD-2026-00187",
    "status": "Contacted",
    "status_type": "Ongoing",
    "modified": "2026-07-31T15:00:00"
  }
}
```

**Business rules:**
- You cannot set `converted = true` via this endpoint. Use [Convert Lead](#45-convert-lead-to-deal) instead.
- Setting status to a type `Lost` transitions the lead out of the active funnel.

---

### 4.5 Convert Lead to Deal

```
POST /api/method/crm.api.partner.convert_lead
```

Signals that a Lead has been qualified into a formal Deal. Creates a new `CRM Deal` linked to the lead. The deal inherits `partner` and `partner_ref` from the lead.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lead_name` | string | Yes* | CRM Lead ID |
| `partner_ref` | string | Yes* | Your internal reference ID |
| `deal_partner_ref` | string | No | A separate partner reference for the resulting deal |

*Either `lead_name` or `partner_ref` required.

**Example request:**
```json
{
  "lead_name": "CRM-LEAD-2026-00187",
  "deal_partner_ref": "PP-DEAL-2026-0011"
}
```

**Example response (200):**
```json
{
  "message": {
    "lead_name": "CRM-LEAD-2026-00187",
    "deal_name": "CRM-DEAL-2026-00053",
    "deal_status": "Qualification",
    "partner": "Acme Partners Ltd",
    "partner_ref": "PP-DEAL-2026-0011"
  }
}
```

**Business rules:**
- An already-converted lead returns the existing deal name with HTTP 200 (no duplicate created).

---

## 5. Deals

A **Deal** represents a qualified sales opportunity with a known organisation, expected value, and defined lifecycle towards Won or Lost.

### 5.1 Create Deal

```
POST /api/method/crm.api.partner.create_deal
```

Creates a Deal directly, without a preceding Lead. Use this when the customer is already qualified.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organization` | string | Yes | Organisation / company name |
| `first_name` | string | Yes | Primary contact first name |
| `last_name` | string | No | Primary contact last name |
| `email` | string (email) | Yes | Primary contact email |
| `mobile_no` | string | No | Primary contact mobile |
| `phone` | string | No | Primary contact phone |
| `job_title` | string | No | Primary contact job title |
| `website` | string | No | Organisation website |
| `territory` | string | No | CRM Territory name |
| `industry` | string | No | CRM Industry name |
| `source` | string | No | Lead source — defaults to `"Partner"` |
| `deal_value` | number | No | Estimated deal value (in account currency) |
| `currency` | string | No | ISO 4217 currency code (e.g. `"KES"`) |
| `expected_closure_date` | string (ISO 8601 date) | No | Expected close date |
| `annual_revenue` | number | No | Organisation annual revenue |
| `no_of_employees` | string | No | `1-10`, `11-50`, `51-200`, `201-500`, `501-1000`, `1000+` |
| `partner_ref` | string | No | Your internal reference ID |
| `products` | array | No | `[{"item_code": "...", "qty": 1}]` |

**Example request:**
```json
{
  "organization": "Savanna Tech Ltd",
  "first_name": "Amina",
  "last_name": "Wanjiku",
  "email": "amina.wanjiku@example.co.ke",
  "mobile_no": "+254712345678",
  "deal_value": 250000,
  "currency": "KES",
  "expected_closure_date": "2026-09-30",
  "territory": "East Africa",
  "partner_ref": "PP-DEAL-2026-0011"
}
```

**Example response (201):**
```json
{
  "message": {
    "name": "CRM-DEAL-2026-00053",
    "status": "Qualification",
    "status_type": "Open",
    "organization": "Savanna Tech Ltd",
    "deal_value": 250000,
    "currency": "KES",
    "partner": "Acme Partners Ltd",
    "partner_ref": "PP-DEAL-2026-0011"
  }
}
```

---

### 5.2 Get Deal

```
GET /api/method/crm.api.partner.get_deal
```

Returns the full detail of a single deal owned by your partner account.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deal_name` | string | Yes* | CRM Deal ID (e.g. `CRM-DEAL-2026-00053`) |
| `partner_ref` | string | Yes* | Your internal reference ID |

*Either `deal_name` or `partner_ref` required.

**Example response (200):**
```json
{
  "message": {
    "name": "CRM-DEAL-2026-00053",
    "organization": "Savanna Tech Ltd",
    "status": "Negotiation",
    "status_type": "Ongoing",
    "probability": 60,
    "deal_value": 250000,
    "expected_deal_value": 200000,
    "currency": "KES",
    "expected_closure_date": "2026-09-30",
    "closed_date": null,
    "lead": "CRM-LEAD-2026-00187",
    "email": "amina.wanjiku@example.co.ke",
    "mobile_no": "+254712345678",
    "partner": "Acme Partners Ltd",
    "partner_ref": "PP-DEAL-2026-0011",
    "source": "Partner",
    "territory": "East Africa",
    "sla_status": "Fulfilled",
    "creation": "2026-07-31T09:30:00",
    "modified": "2026-07-31T16:00:00"
  }
}
```

---

### 5.3 List Deals

```
GET /api/method/crm.api.partner.get_deals
```

Returns a paginated list of deals owned by the authenticated partner.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number |
| `page_size` | integer | `20` | Max 100 |
| `status` | string | — | Filter by status name |
| `status_type` | string | — | `Open`, `Ongoing`, `On Hold`, `Won`, `Lost` |
| `from_date` | string (ISO 8601) | — | Creation date from |
| `to_date` | string (ISO 8601) | — | Creation date to |
| `order_by` | string | `"modified desc"` | Sort field and direction |

**Example response (200):**
```json
{
  "message": {
    "total": 34,
    "page": 1,
    "page_size": 20,
    "data": [
      {
        "name": "CRM-DEAL-2026-00053",
        "organization": "Savanna Tech Ltd",
        "status": "Negotiation",
        "status_type": "Ongoing",
        "deal_value": 250000,
        "currency": "KES",
        "partner_ref": "PP-DEAL-2026-0011",
        "creation": "2026-07-31T09:30:00",
        "modified": "2026-07-31T16:00:00"
      }
    ]
  }
}
```

---

### 5.4 Update Deal Status

```
POST /api/method/crm.api.partner.update_deal_status
```

Advances the deal's lifecycle status.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deal_name` | string | Yes* | CRM Deal ID |
| `partner_ref` | string | Yes* | Your internal reference ID |
| `status` | string | Yes | Target status name (must be a valid `CRM Deal Status`) |
| `lost_reason` | string | Conditional | Required when `status` is of type `Lost` |
| `lost_notes` | string | No | Free-text notes (required if `lost_reason == "Other"`) |
| `closed_date` | string (ISO 8601 date) | No | Closing date — defaults to today for Won/Lost |
| `notes` | string | No | Status change notes |

*Either `deal_name` or `partner_ref` required.

**Example request (Won):**
```json
{
  "deal_name": "CRM-DEAL-2026-00053",
  "status": "Won",
  "closed_date": "2026-08-15"
}
```

**Example request (Lost):**
```json
{
  "deal_name": "CRM-DEAL-2026-00053",
  "status": "Lost",
  "lost_reason": "Price",
  "lost_notes": "Customer chose a cheaper competitor.",
  "closed_date": "2026-08-10"
}
```

**Example response (200):**
```json
{
  "message": {
    "name": "CRM-DEAL-2026-00053",
    "status": "Won",
    "status_type": "Won",
    "closed_date": "2026-08-15",
    "modified": "2026-08-15T10:00:00"
  }
}
```

---

## 6. Contacts

Contacts represent named individuals associated with an organisation. A Deal can have multiple Contacts; one is designated primary. Contacts are **shared across Tiberbu** — creating a contact makes it visible to all internal Tiberbu users, not just your partner account.

### 6.1 Create Contact

```
POST /api/method/crm.api.partner.create_contact
```

Creates a new Contact record and optionally links it immediately to one of your Deals.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | Yes | Contact's first name |
| `last_name` | string | No | Contact's last name |
| `email` | string (email) | Yes | Primary email address |
| `mobile_no` | string | No | Mobile number (E.164 recommended) |
| `phone` | string | No | Landline number |
| `job_title` | string | No | Job title / designation |
| `company_name` | string | No | Organisation name (free text) |
| `deal_name` | string | No | CRM Deal ID to link this contact to immediately |
| `partner_ref` | string | No | Your internal reference ID for this contact (idempotency key) |
| `set_primary` | boolean | No | If linking to a deal, set this contact as the primary contact (default: `false`) |

**Example request:**
```json
{
  "first_name": "Brian",
  "last_name": "Otieno",
  "email": "brian.otieno@savannatech.co.ke",
  "mobile_no": "+254723456789",
  "job_title": "CTO",
  "company_name": "Savanna Tech Ltd",
  "deal_name": "CRM-DEAL-2026-00053",
  "partner_ref": "PP-CONTACT-2026-0005"
}
```

**Example response (201):**
```json
{
  "message": {
    "name": "Brian Otieno",
    "full_name": "Brian Otieno",
    "email": "brian.otieno@savannatech.co.ke",
    "mobile_no": "+254723456789",
    "linked_deal": "CRM-DEAL-2026-00053",
    "is_primary": false
  }
}
```

---

### 6.2 Get Deal Contacts

```
GET /api/method/crm.api.partner.get_deal_contacts
```

Returns all contacts linked to a deal owned by your partner account.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deal_name` | string | Yes* | CRM Deal ID |
| `partner_ref` | string | Yes* | Your deal's internal reference ID |

*Either `deal_name` or `partner_ref` required.

**Example request:**
```
GET /api/method/crm.api.partner.get_deal_contacts?deal_name=CRM-DEAL-2026-00053
```

**Example response (200):**
```json
{
  "message": [
    {
      "contact": "Amina Wanjiku",
      "full_name": "Amina Wanjiku",
      "email": "amina.wanjiku@example.co.ke",
      "mobile_no": "+254712345678",
      "job_title": "CEO",
      "is_primary": true
    },
    {
      "contact": "Brian Otieno",
      "full_name": "Brian Otieno",
      "email": "brian.otieno@savannatech.co.ke",
      "mobile_no": "+254723456789",
      "job_title": "CTO",
      "is_primary": false
    }
  ]
}
```

---

### 6.3 Add Contact to Deal

```
POST /api/method/crm.api.partner.add_contact_to_deal
```

Links an existing Contact to one of your Deals. Idempotent — if the contact is already on the deal, returns 200 without error.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deal_name` | string | Yes* | CRM Deal ID |
| `partner_ref` | string | Yes* | Your deal's internal reference ID |
| `contact` | string | Yes | Contact name (Frappe Contact ID, e.g. `"Brian Otieno"`) |
| `set_primary` | boolean | No | Set this contact as the deal's primary contact (default: `false`) |

*Either `deal_name` or `partner_ref` required.

**Example request:**
```json
{
  "deal_name": "CRM-DEAL-2026-00053",
  "contact": "Brian Otieno",
  "set_primary": false
}
```

**Example response (200):**
```json
{
  "message": {
    "deal_name": "CRM-DEAL-2026-00053",
    "contact": "Brian Otieno",
    "is_primary": false
  }
}
```

---

## 7. Reference Data

These endpoints return lookup values your system needs for validation.

### 7.1 Lead Statuses

```
GET /api/method/crm.api.partner.get_lead_statuses
```

Returns all configured Lead statuses and their lifecycle type.

**Example response:**
```json
{
  "message": [
    { "name": "New Lead",    "type": "Open" },
    { "name": "Contacted",   "type": "Ongoing" },
    { "name": "Nurturing",   "type": "Ongoing" },
    { "name": "On Hold",     "type": "On Hold" },
    { "name": "Converted",   "type": "Won" },
    { "name": "Lost",        "type": "Lost" }
  ]
}
```

**Status Types:**

| Type | Meaning |
|------|---------|
| `Open` | Lead is new / not yet engaged |
| `Ongoing` | Active engagement in progress |
| `On Hold` | Paused — pending customer or partner action |
| `Won` | Lead successfully converted |
| `Lost` | Lead will not progress |

---

### 7.2 Deal Statuses

```
GET /api/method/crm.api.partner.get_deal_statuses
```

Returns all configured Deal statuses and their lifecycle type and default probability.

**Example response:**
```json
{
  "message": [
    { "name": "Qualification", "type": "Open",    "probability": 20 },
    { "name": "Negotiation",   "type": "Ongoing", "probability": 60 },
    { "name": "Won",           "type": "Won",     "probability": 100 },
    { "name": "Lost",          "type": "Lost",    "probability": 0 }
  ]
}
```

> Note: Status configurations can be modified by Tiberbu administrators. Refresh this list periodically (e.g. daily) and do not hard-code status names.

---

## 8. Webhooks

Tiberbu CRM will POST event notifications to your configured `webhook_url` when key lifecycle events occur on your leads and deals. Provide your endpoint URL to your Tiberbu account manager.

### 8.1 Webhook Events

| Event Type | Trigger |
|------------|---------|
| `lead.status_changed` | Lead status changes to any value |
| `lead.converted` | Lead is converted to a Deal |
| `lead.lost` | Lead status changes to a type `Lost` status |
| `deal.status_changed` | Deal status changes to any value |
| `deal.won` | Deal status changes to a type `Won` status |
| `deal.lost` | Deal status changes to a type `Lost` status |

---

### 8.2 Payload Structure

All events share a common envelope:

```json
{
  "event": "deal.won",
  "timestamp": "2026-08-15T10:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": { /* event-specific payload */ }
}
```

#### `lead.status_changed`
```json
{
  "event": "lead.status_changed",
  "timestamp": "2026-07-31T15:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": {
    "lead_name": "CRM-LEAD-2026-00187",
    "partner_ref": "PP-LEAD-2026-0042",
    "lead_display_name": "Amina Wanjiku",
    "organization": "Savanna Tech Ltd",
    "old_status": "New Lead",
    "new_status": "Contacted",
    "new_status_type": "Ongoing"
  }
}
```

#### `lead.converted`
```json
{
  "event": "lead.converted",
  "timestamp": "2026-07-31T16:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": {
    "lead_name": "CRM-LEAD-2026-00187",
    "partner_ref": "PP-LEAD-2026-0042",
    "deal_name": "CRM-DEAL-2026-00053",
    "deal_partner_ref": "PP-DEAL-2026-0011"
  }
}
```

#### `deal.status_changed`
```json
{
  "event": "deal.status_changed",
  "timestamp": "2026-08-01T09:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": {
    "deal_name": "CRM-DEAL-2026-00053",
    "partner_ref": "PP-DEAL-2026-0011",
    "organization": "Savanna Tech Ltd",
    "old_status": "Qualification",
    "new_status": "Negotiation",
    "new_status_type": "Ongoing",
    "probability": 60
  }
}
```

#### `deal.won`
```json
{
  "event": "deal.won",
  "timestamp": "2026-08-15T10:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": {
    "deal_name": "CRM-DEAL-2026-00053",
    "partner_ref": "PP-DEAL-2026-0011",
    "organization": "Savanna Tech Ltd",
    "deal_value": 250000,
    "currency": "KES",
    "closed_date": "2026-08-15"
  }
}
```

#### `deal.lost`
```json
{
  "event": "deal.lost",
  "timestamp": "2026-08-10T14:00:00Z",
  "partner": "Acme Partners Ltd",
  "data": {
    "deal_name": "CRM-DEAL-2026-00053",
    "partner_ref": "PP-DEAL-2026-0011",
    "organization": "Savanna Tech Ltd",
    "deal_value": 250000,
    "currency": "KES",
    "lost_reason": "Price",
    "lost_notes": "Customer chose a cheaper competitor.",
    "closed_date": "2026-08-10"
  }
}
```

---

### 8.3 Signature Verification

Every webhook POST includes an `X-Tiberbu-Signature` header. Verify it to confirm the payload originated from Tiberbu and was not tampered with.

**Algorithm:** HMAC-SHA256  
**Key:** Your `webhook_secret` (provided by Tiberbu alongside your API credentials)  
**Input:** Raw request body (bytes, before JSON parsing)

**Verification (Python example):**
```python
import hmac, hashlib

def verify_signature(body: bytes, secret: str, header: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)

# In your webhook handler:
signature = request.headers.get("X-Tiberbu-Signature", "")
if not verify_signature(request.body, WEBHOOK_SECRET, signature):
    return 401
```

**Verification (Node.js example):**
```javascript
const crypto = require("crypto");

function verifySignature(body, secret, header) {
  const expected = "sha256=" + crypto
    .createHmac("sha256", secret)
    .update(body)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(header)
  );
}
```

> Always use a constant-time comparison (`hmac.compare_digest` / `timingSafeEqual`) to prevent timing attacks.

---

### 8.4 Retry Policy

If your endpoint does not respond with `2xx` within 10 seconds, Tiberbu will retry delivery:

| Attempt | Delay after previous failure |
|---------|------------------------------|
| 1 (initial) | — |
| 2 | 30 seconds |
| 3 | 2 minutes |
| 4 | 5 minutes |

After 4 failed attempts, the event is marked as failed and logged. Tiberbu support can replay failed webhooks on request.

**Your endpoint must:**
- Respond `200 OK` (or any `2xx`) as quickly as possible.
- Process the event asynchronously if needed — do not perform long operations in the request handler.
- Be idempotent — the same event may be delivered more than once.

---

## 9. Field Reference

### 9.1 Lead Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | CRM-internal Lead ID (`CRM-LEAD-YYYY-NNNNN`) |
| `lead_name` | string | Full display name |
| `first_name` | string | |
| `middle_name` | string | |
| `last_name` | string | |
| `email` | string | Primary email |
| `mobile_no` | string | Mobile number |
| `phone` | string | Landline number |
| `organization` | string | Company name |
| `job_title` | string | |
| `website` | string | Company website |
| `territory` | string | CRM Territory name |
| `industry` | string | CRM Industry name |
| `source` | string | Lead source (default: `"Partner"`) |
| `status` | string | Current status name |
| `status_type` | string | `Open`, `Ongoing`, `On Hold`, `Won`, `Lost` |
| `converted` | boolean | `true` if converted to a Deal |
| `deal_name` | string | Linked Deal ID (if converted) |
| `partner` | string | Partner account name (read-only) |
| `partner_ref` | string | Your internal reference ID |
| `annual_revenue` | number | Estimated annual revenue |
| `no_of_employees` | string | Headcount band |
| `sla_status` | string | SLA tracking status |
| `communication_status` | string | Communication state |
| `creation` | datetime (ISO 8601) | Record creation timestamp |
| `modified` | datetime (ISO 8601) | Last modification timestamp |

---

### 9.2 Deal Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | CRM-internal Deal ID (`CRM-DEAL-YYYY-NNNNN`) |
| `organization` | string | Linked organisation name |
| `status` | string | Current status name |
| `status_type` | string | `Open`, `Ongoing`, `On Hold`, `Won`, `Lost` |
| `probability` | number | Win probability (0–100) |
| `deal_value` | number | Estimated deal value |
| `expected_deal_value` | number | Probability-adjusted value |
| `currency` | string | ISO 4217 currency code |
| `expected_closure_date` | date | Expected close date |
| `closed_date` | date | Actual close date (set on Won/Lost) |
| `lead` | string | Source Lead ID (if converted from Lead) |
| `email` | string | Primary contact email |
| `mobile_no` | string | Primary contact mobile |
| `phone` | string | Primary contact phone |
| `first_name` | string | Primary contact first name |
| `last_name` | string | Primary contact last name |
| `job_title` | string | Primary contact job title |
| `territory` | string | CRM Territory name |
| `industry` | string | CRM Industry name |
| `source` | string | Lead source |
| `lost_reason` | string | Reason for loss (set on Lost) |
| `lost_notes` | string | Loss notes |
| `partner` | string | Partner account name (read-only) |
| `partner_ref` | string | Your internal reference ID |
| `sla_status` | string | SLA tracking status |
| `communication_status` | string | Communication state |
| `creation` | datetime (ISO 8601) | Record creation timestamp |
| `modified` | datetime (ISO 8601) | Last modification timestamp |

---

### 9.3 Contact Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Frappe Contact ID (typically full name, e.g. `"Brian Otieno"`) |
| `full_name` | string | Display name |
| `first_name` | string | |
| `last_name` | string | |
| `email` | string | Primary email |
| `mobile_no` | string | Mobile number |
| `phone` | string | Landline number |
| `job_title` | string | |
| `company_name` | string | Organisation name |
| `creation` | datetime (ISO 8601) | Record creation timestamp |
| `modified` | datetime (ISO 8601) | Last modification timestamp |

---

## 10. Idempotency

Supply a `partner_ref` on every create call. It is your stable external identifier for the record and acts as an idempotency key.

**Rules:**
- `partner_ref` must be unique within your partner account per document type (Leads and Deals are separate namespaces).
- If you POST a create request with a `partner_ref` that already exists for your account, the server returns **HTTP 200** with the existing record — no duplicate is created.
- You can use `partner_ref` instead of `name` in any endpoint that accepts either (get, update, convert).

**Recommended format:** A stable identifier from your internal system, e.g. `PP-LEAD-2026-0042`. Avoid UUIDs unless your system guarantees they are stable across retries.

---

## 11. Lifecycle Diagrams

### Lead Lifecycle

```
           ┌─────────┐
    POST   │         │
 ─────────►│ New Lead│ (type: Open)
           │         │
           └────┬────┘
                │  update_lead_status
                ▼
           ┌──────────┐
           │Contacted │ (type: Ongoing)
           └────┬─────┘
                │
       ┌────────┴────────┐
       │                 │
       ▼                 ▼
 ┌──────────┐     ┌──────────┐
 │Nurturing │     │ On Hold  │ (type: On Hold)
 └────┬─────┘     └────┬─────┘
      │                │
      └────────┬────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
 ┌──────────┐    ┌────────────┐
 │ Convert  │    │    Lost    │ (type: Lost)
 │ to Deal  │    └────────────┘
 └──────────┘
       │
       ▼
  CRM Deal created
```

### Deal Lifecycle

```
           ┌───────────────┐
    POST   │               │
 ─────────►│ Qualification │ (type: Open, p=20%)
           │               │
           └───────┬───────┘
                   │  update_deal_status
                   ▼
           ┌───────────────┐
           │  Negotiation  │ (type: Ongoing, p=60%)
           └───────┬───────┘
                   │
          ┌────────┴─────────┐
          │                  │
          ▼                  ▼
    ┌──────────┐       ┌──────────┐
    │   Won    │       │   Lost   │
    │(p=100%)  │       │  (p=0%)  │
    └──────────┘       └──────────┘
```

> Actual status names and their types are configurable by Tiberbu. Always fetch the current list from §6 rather than hard-coding.

---

## 12. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-07-31 | Added §6 Contacts (create, list, link). Added `default_deal_owner` note in auth. Renumbered Reference Data → §7, Webhooks → §8, Field Reference → §9. Resolved OQ-1, OQ-3, OQ-5. |
| 1.0 | 2026-07-31 | Initial release |

---

## Support

For integration questions, credential requests, or to report API issues:

- **Email:** integrations@tiberbu.com
- **Subject prefix:** `[Partner API]`

For urgent production incidents, contact your Tiberbu account manager directly.
