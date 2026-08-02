# BRD — Health Facility Registry (HFR) Integration for CRM
**Version:** 1.1
**Date:** 2026-08-01
**Author:** Salim
**Status:** Approved — open questions resolved

**Changelog:**
- v1.1 — OQ-1 through OQ-4 resolved (Salim, 2026-08-01). HFR field set on CRM Organization expanded to include all meaningful registry attributes.

---

## 1. Background & Business Context

Tiberbu's Sales Agents prospect healthcare organisations as new CRM customers.
Today, when a Sales Agent creates an Organisation or a Lead in Tiberbu CRM they type
facility details manually — name, location, registration number, contacts — from
memory or from a physical document. This creates three problems:

1. **Data quality.** Manually-entered records diverge from the official government
   registry immediately: wrong MFL codes, misspelled names, stale phone numbers.
2. **Duplicate work.** HFR already holds hundreds of fields about every licensed
   facility in Kenya. Agents re-key what the registry knows.
3. **Trust gap.** Tiberbu's downstream products (HealthPro ERP) require a valid
   `hie_id` (Facility ID from HFR). If the CRM record was created without one, a
   manual reconciliation step is needed before any HealthPro workflow can start.

The **Kenya Health Facility Registry (HFR)** — accessed through the HIE integration
layer already built in `healthpro_erp` — provides a verified, real-time data source
for every licensed health facility. The HIE layer is already deployed and authenticated
(`HealthPro Backend Settings`: `hie_url`, `hfr_fetch_url`, JWT auth via `hie_username`
/ `hie_password`).

This BRD defines the scope of wiring that existing HFR integration into the CRM's
**Organisation creation** and **Lead creation** flows so that Sales Agents can look
up a facility by name, MFL code, or registration number and pre-fill the record with
verified registry data in a single click.

---

## 2. Goals

| # | Goal |
|---|------|
| G1 | Sales Agents can search the HFR from within the CRM Create Organisation modal and pre-fill the record with verified registry data. |
| G2 | Sales Agents can search the HFR from within the CRM Create Lead modal and attach an HFR-verified facility to the lead. |
| G3 | HFR-sourced records carry the facility's full official profile — FID, MFL code, level, category, owner type, location (county/sub-county/ward), coordinates, operational status, regulatory body, registration number, license details, and operational hours — available for downstream HealthPro workflows. |
| G4 | The lookup is non-blocking — agents can still create an Org/Lead manually if no HFR match is found or if the feature is unavailable. |
| G5 | The UX is consistent with the existing domain-enrichment pattern ("search → preview → accept/reject → create"). |
| G6 | HFR credentials remain server-side only — never exposed to the browser. |

---

## 3. Stakeholders

| Role | Person / Team | Interest |
|------|--------------|----------|
| Product Owner | Salim | Approval, scope |
| CRM Engineering | Tiberbu CRM team | Implementation |
| HealthPro Engineering | Tiberbu ERP team | HIE/HFR API owner |
| Sales Agents | Tiberbu internal | Primary end-users |
| HealthPro Ops | Tiberbu internal | Data quality / downstream workflows |

---

## 4. Scope

### 4.1 In Scope

- New whitelisted Python API `crm.api.hfr.search_facility` — proxies the HFR
  fetch endpoint, returns a normalised list of candidate facilities.
- New whitelisted Python API `crm.api.hfr.get_facility_detail` — fetches the full
  record for a single FID, returns a field map ready to apply to `CRM Organization`.
- New "Registry" field section on `CRM Organization` — full set of HFR attributes
  (see FR-4 for the complete list).
- Minimal HFR fields on `CRM Lead` (FID, MFL code, level, owner type, sync status)
  — coordinates and timestamps live only on Organisation.
- Updated `OrganizationModal.vue`: "Search HFR" button opens an inline search panel;
  selecting a result pre-fills the creation form (fill-empty semantics).
- Updated `LeadModal.vue`: same "Search HFR" affordance; Organisation is created from
  HFR data after the Lead is saved (not before).
- `CRM Settings` gains new HFR section: `hfr_enabled` toggle + direct HIE credentials
  (`hfr_url`, `hfr_fetch_path`, `hfr_username`, `hfr_password`).
- Re-sync UX on Organisation detail page: "Re-sync from HFR" button prompts agent to
  choose fill-empty or overwrite before syncing.
- Migration fixture adding all new fields to `CRM Organization` and `CRM Lead`.

### 4.2 Out of Scope

- HFR update/write-back from CRM (CRM is read-only against HFR at this stage).
- HWR (Health Worker Registry) integration.
- C360 (Compliance 360) integration.
- HFR auto-sync / periodic refresh job (post-MVP).
- Facility onboarding flow (full `create_new_facility` pipeline from `healthpro_erp`)
  — CRM only creates the CRM-side record; HealthPro ERP owns the facility lifecycle.
- Mobile views (handled after desktop is stable).
- Proxying HIE calls through `healthpro_erp` site (CRM holds its own credentials).

---

## 5. User Stories

### US-01 — Search HFR when creating an Organisation
> As a Sales Agent, when I open the "New Organisation" modal, I want to search the
> Health Facility Registry by name or MFL code so that the form is pre-filled with
> verified data and I do not have to type it manually.

**Acceptance Criteria:**
- "Search Health Facility Registry" panel is accessible inside the Create Organisation modal.
- Typing ≥ 3 characters and pressing Search calls `crm.api.hfr.search_facility`.
- A result list shows: facility name, MFL code, level, county, owner type, operational status.
- Selecting a result calls `crm.api.hfr.get_facility_detail` and fills the full HFR
  field set (see FR-4) using fill-empty semantics.
- Agent can edit any field after fill before clicking Create.
- If HFR returns no results, the modal remains usable and shows "No results — create manually".
- If HFR is unreachable or disabled, the panel is not rendered; modal works as before.

### US-02 — HFR lookup when creating a Lead
> As a Sales Agent, when I open the "Create Lead" modal, I want to attach the lead
> to an HFR-verified facility so that the lead record includes the facility's official
> details.

**Acceptance Criteria:**
- "Search Health Facility Registry" panel is present in the Create Lead modal.
- Selecting an HFR result fills Lead fields (see FR-5) using fill-empty semantics.
- After the Lead is saved, if no existing `CRM Organization` matches `facility_name`,
  one is created automatically using the same HFR data (follows existing
  `lead.create_organization()` path, extended to carry HFR fields).
- Fill-empty semantics in the modal; manual editing is always possible.

### US-03 — HFR data visible on Organisation detail page
> As a Sales Agent, I want to see which HFR-sourced fields an Organisation record
> carries so that I know whether the record is registry-verified.

**Acceptance Criteria:**
- Organisation detail page shows a "Registry" section with all HFR-managed fields
  grouped (identity, location, licensing, operations — see FR-4).
- `hfr_sync_status` = "HFR Verified" when data came from the registry; "Manual" otherwise.
- A "Re-sync from HFR" button is present on the detail page.
- Clicking "Re-sync" shows a confirmation prompt:
  > "How would you like to apply the latest registry data?"
  > [Fill empty fields only] [Overwrite all HFR fields] [Cancel]
- Choosing "Fill empty" applies fill-empty semantics to HFR-managed fields.
- Choosing "Overwrite" applies overwrite-all to HFR-managed fields only (non-HFR fields
  such as `website`, `no_of_employees`, `annual_revenue` are never touched).
- Either choice updates `hfr_last_synced` and sets `hfr_sync_status = "HFR Verified"`.

### US-04 — HFR lookup disabled gracefully
> As a Sales Agent, if the HFR is not configured or is unreachable, I want the
> create/detail flows to behave exactly as they did before this feature.

**Acceptance Criteria:**
- When `hfr_enabled = false` in CRM Settings, no HFR UI elements are rendered.
- When `hfr_enabled = true` but the API call fails, the error is surfaced as a toast;
  the form stays open and usable.
- No JavaScript exceptions when HFR is unavailable.

---

## 6. Functional Requirements

### FR-1 — `crm.api.hfr.search_facility`
Whitelist, GET. Accepts `query` (str) and `search_by`
(`facility_name` | `registration_number` | `facility_code`).
Generates a short-lived JWT from CRM's own HIE credentials, calls
`GET {hfr_url}{hfr_fetch_path}` with appropriate query params.
Returns `[{fid, name, mfl_code, level, category, county, owner_type, operational_status}]`.

### FR-2 — `crm.api.hfr.get_facility_detail`
Whitelist, GET. Accepts `fid` (str). Calls HFR for the full record.
Returns a dict keyed to `CRM Organization` field names (see FR-4 mapping table).

### FR-3 — `crm.api.hfr.resync_organization`
Whitelist, POST. Accepts `organization_name` (str) and `mode`
(`fill_empty` | `overwrite`). Fetches HFR detail using stored `hfr_facility_id`.
Applies the chosen mode to the HFR-managed fields only.
Updates `hfr_last_synced` and `hfr_sync_status = "HFR Verified"`.
Returns `{updated_fields: [...]}`.

### FR-4 — New `CRM Organization` fields (Registry section)

**Group: Registry Identity**

| CRM field | Type | HFR source | Notes |
|-----------|------|-----------|-------|
| `hfr_facility_id` | Data | `hie_id` / `facility_fid` | HFR Facility ID (FID) |
| `mfl_code` | Data | `facility_mfl` | Master Facility List code |
| `facility_type` | Data | `facility_type` | e.g. "Dispensary", "Hospital" |
| `facility_category` | Data | `category` | e.g. "In-Patient", "Out-Patient" |
| `facility_level` | Data | `kephl_level` | KEPHL Level (Level 2–6) |
| `facility_owner` | Data | `facility_owner` | Owning entity name |
| `facility_owner_type` | Data | `facility_owner_type` | Public / Private / Faith-Based / NGO |
| `regulatory_body` | Data | `regulatory_body` | e.g. "Kenya Medical Practitioners Board" |
| `registration_number` | Data | `registration_number` | Official registration number |
| `board_registration_number` | Data | `board_registration_number` | Board-specific registration |
| `operational_status` | Data | `operational_status` | e.g. "Operational", "Closed" |
| `kra_pin` | Data | `kra_pin` | KRA PIN |

**Group: Registry Location**

| CRM field | Type | HFR source | Notes |
|-----------|------|-----------|-------|
| `hfr_county` | Data | `county` | Used for Territory mapping |
| `hfr_sub_county` | Data | `sub_county` | |
| `hfr_constituency` | Data | `constituency` | |
| `hfr_ward` | Data | `ward` | |
| `latitude` | Float | `latitude` | |
| `longitude` | Float | `longitude` | |

**Group: Registry Licensing**

| CRM field | Type | HFR source | Notes |
|-----------|------|-----------|-------|
| `license_number` | Data | `license_number` | |
| `license_type` | Data | `license_type` | |
| `license_expiry` | Data | `license_expiry` | |
| `facility_standing` | Data | `standing` | e.g. "Good Standing", "Suspended" |

**Group: Registry Operations**

| CRM field | Type | HFR source | Notes |
|-----------|------|-----------|-------|
| `open_whole_day` | Check | `open_whole_day` | |
| `open_weekends` | Check | `open_weekends` | |
| `open_public_holidays` | Check | `open_public_holiday` | |
| `open_late_night` | Check | `open_late_night` | |
| `number_of_beds` | Int | `number_of_beds` | |
| `number_of_cots` | Int | `number_of_cots` | |

**Group: Registry Sync Metadata** (read-only after first set)

| CRM field | Type | Notes |
|-----------|------|-------|
| `hfr_sync_status` | Select (HFR Verified / Manual) | Set to "HFR Verified" when data came from registry |
| `hfr_last_synced` | Datetime | Timestamp of last successful re-sync |

### FR-5 — New `CRM Lead` fields (Registry section, minimal)

| CRM field | Type | HFR source |
|-----------|------|-----------|
| `hfr_facility_id` | Data | `hie_id` |
| `mfl_code` | Data | `facility_mfl` |
| `facility_level` | Data | `kephl_level` |
| `facility_owner_type` | Data | `facility_owner_type` |
| `hfr_sync_status` | Select (HFR Verified / Manual) | |

Coordinates and sync timestamps live only on `CRM Organization`.

### FR-6 — `CRM Settings` HFR section

New fields (all in a new "HFR Integration" section of CRM Settings):
- `hfr_enabled` (Check, default 0)
- `hfr_url` (Data) — HIE base URL, e.g. `https://hie.example.health`
- `hfr_fetch_path` (Data) — HFR fetch endpoint path, e.g. `/v1/hfr/facilities`
- `hfr_username` (Data) — HIE username
- `hfr_password` (Password) — HIE password
- `hfr_jwt_expiry` (Int, default 20000) — JWT expiry in seconds

### FR-7 — JWT generation
`crm/api/hfr.py` private helper `_generate_jwt()`: HS256, payload
`{"key": hfr_username, "exp": int(time.time()) + hfr_jwt_expiry}`, secret = `hfr_password`.
Mirrors `healthpro_erp.api.hie_settings.HIE.generate_jwt_token` exactly.

### FR-8 — `OrganizationModal.vue` HFR panel
Inline collapsible panel inside the existing modal (above the form fields).
Collapsed by default. Search triggers on explicit button press (not on keystroke).
Minimum query length: 3 characters.

### FR-9 — `LeadModal.vue` HFR panel
Same panel as FR-8. On Lead save, `create_organization()` is extended to pass
HFR fields through when creating the linked Organisation.

### FR-10 — Organisation detail page
`Organization.vue` gains a "Registry" section showing all FR-4 fields (read-only
display). "Re-sync from HFR" button triggers the confirmation prompt (US-03).

### FR-11 — Feature flag guard
All HFR UI elements use `v-if="hfrEnabled"` (computed from CRM Settings) —
conditionally not rendered (not `v-show`). Python methods throw `frappe.PermissionError`
when `hfr_enabled = 0`.

---

## 7. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-1 | HFR search response time ≤ 3 s P95. UX shows a loading spinner during the call. |
| NFR-2 | JWT secrets never appear in browser network traffic or Vue component state. All HIE calls are server-side Python. |
| NFR-3 | HFR feature flag off by default. Enabling requires explicit admin action in CRM Settings. |
| NFR-4 | `pnpm build` passes with zero warnings after frontend changes. |
| NFR-5 | Dark/light mode parity on all new UI elements. |
| NFR-6 | No hardcoded hex colours — all colours through theme tokens. |

---

## 8. Open Questions

All questions resolved.

| # | Question | Resolution |
|---|----------|-----------|
| OQ-1 | CRM hold own HIE creds vs. proxy through `healthpro_erp`? | **CRM holds its own HIE credentials** (direct calls, no cross-site dependency). |
| OQ-2 | `latitude`/`longitude` on `CRM Lead` too? | **Organisation only.** Coordinates are not stored on Lead. |
| OQ-3 | Re-sync semantics: overwrite-all vs. fill-empty? | **User's choice at re-sync time** — confirmation prompt with "Fill empty" and "Overwrite all HFR fields" options. |
| OQ-4 | Auto-create `CRM Organization` on HFR select in Lead modal? | **After Lead is saved**, not before. Follows existing `lead.create_organization()` path. |

---

## 9. Out-of-Scope Decisions Recorded

- **HFR write-back from CRM** — CRM is a sales tool, not a registry administrator.
  Updates to the registry remain the responsibility of HealthPro ERP.
- **Full HFR onboarding flow** — OTP verification, RSA encryption, C360 review, HWR sync
  are outside CRM's domain.
- **KMHFR county sync** — Territory seeding from KMHFR counties is a separate admin task.
- **Proxy through `healthpro_erp`** — resolved against; CRM holds its own credentials.
