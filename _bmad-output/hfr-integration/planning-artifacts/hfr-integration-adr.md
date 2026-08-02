# Architecture Decision Records — HFR Integration for Tiberbu CRM
**Epic:** hfr-integration
**Date:** 2026-08-01
**Author:** Salim

---

## ADR-001 — Server-side proxy for all HFR/HIE calls

**Status:** Accepted

### Context
The HIE API requires a JWT token signed with `hie_password` (stored in
`HealthPro Backend Settings`). The CRM frontend is a Vue SPA running in the browser.
Exposing `hie_password` or a long-lived JWT to the browser would allow any user with
DevTools access to make direct HIE calls and read any facility's sensitive data
(ownership, ID numbers, etc.).

### Decision
All calls to the HIE/HFR endpoint are made by the **CRM Python backend**.
The Vue frontend calls a CRM-internal whitelisted method
(`crm.api.hfr.search_facility`, `crm.api.hfr.get_facility_detail`).
Those methods generate a short-lived JWT server-side, call HIE, and return a
sanitised subset of fields to the browser.

### Consequences
- Browser never sees `hie_password`, `hie_username`, or the JWT.
- CRM Python process must have network access to the HIE endpoint.
- Adds one server round-trip vs. a direct browser call (acceptable — HIE latency
  dominates).
- If HIE is unreachable from the CRM server, the feature is unavailable (graceful
  degradation: hide the HFR button).

---

## ADR-002 — Credential strategy: direct HIE vs. proxy through healthpro_erp site

**Status:** Accepted (OQ-1 resolved 2026-08-01)

### Context
The HIE credentials (`hie_url`, `hie_username`, `hie_password`) exist today only in
`HealthPro Backend Settings` on the `healthpro_erp` app. CRM and `healthpro_erp` are
separate Frappe sites. Two options:

**Option A — Direct credentials in CRM.**
CRM `CRM Settings` (or a new `CRM HFR Settings` Single DocType) stores its own
`hfr_proxy_url`, `hfr_proxy_username`, `hfr_proxy_password`. CRM generates its own
JWT and calls HIE directly.

**Option B — Proxy call to healthpro_erp.**
CRM makes an authenticated server-to-server call to a whitelisted method on the
`healthpro_erp` site, which in turn calls HIE. CRM never holds HIE credentials.

### Recommendation
**Option A — direct credentials** for the initial implementation.

Rationale:
- Avoids a cross-site dependency that would couple CRM deployment to `healthpro_erp`
  uptime.
- The JWT generation pattern is a trivial 10-line function already understood in this
  codebase; no new infrastructure needed.
- The HIE credentials are scoped to read-only HFR operations — the blast radius of a
  credential leak is bounded.
- A second credential set is manageable; it can be rotated independently.

Option B should be reconsidered if Tiberbu centralises HIE credential management or
if the CRM-to-HIE network path requires a specific IP allowlist that the
`healthpro_erp` server already satisfies.

### Consequences (Option A)
- New fields on `CRM Settings`: `hfr_enabled`, `hfr_url`, `hfr_fetch_path`,
  `hfr_username`, `hfr_password` (Password type).
- CRM admin must configure these before the feature is usable.
- `CRM Settings.vue` gains an "HFR" section.
- JWT generation utility function lives in `crm/api/hfr.py`; mirrors
  `healthpro_erp.api.hie_settings.HIE.generate_jwt_token` (HS256, 20 000 s expiry).

---

## ADR-003 — Fill-empty semantics for HFR pre-fill (create modal); user-choice on re-sync

**Status:** Accepted (OQ-3 resolved 2026-08-01)

### Context
The CRM already has a domain enrichment "preview" pattern where an external call
returns a field map and the UI fills only empty fields (no overwrite of values the
agent has already typed). This is defined in `crm.domain_enrichment.pipeline.preview`
and used in `OrganizationModal.vue` and `LeadModal.vue`.

The HFR lookup happens at the same point in the workflow: **before** the record is
saved to the database (in-modal, on the in-memory `doc` object).

### Decision
**Create modals:** fill-empty semantics — a field is set from HFR data only if its
current value is null/empty. An agent who types `organization_name` before clicking
"Search HFR" keeps their typed value.

**Re-sync button** on the Organisation detail page: the agent is asked **at re-sync
time** to choose between two modes:

> "How would you like to apply the latest registry data?"
> **[Fill empty fields only]** — safe; only blank HFR-managed fields get values.
> **[Overwrite all HFR fields]** — refreshes all HFR-managed fields regardless of
> manual edits.
> **[Cancel]**

Both modes restrict updates to the HFR-managed field set only. Fields outside that set
(`website`, `no_of_employees`, `annual_revenue`, etc.) are never touched by re-sync.

Rationale for user-choice over a fixed policy: agents may have corrected a registry
error manually (e.g. a wrong phone number that HFR hasn't updated yet). Letting them
choose fill-empty preserves that correction. When they know the registry is now
authoritative, they can choose overwrite. Presenting the choice is a one-line
confirmation prompt — low friction, high transparency.

### Consequences
- `useHfrSearch()` composable exposes `applyHfrPreview(doc, hfrFields)` — fill-empty.
- `resync_organization(organization_name, mode)` Python API accepts `mode` param
  (`fill_empty` | `overwrite`) and applies it accordingly.
- Vue re-sync button shows a confirmation dialog with the two options before calling
  the API.
- `hfr_sync_status` field on `CRM Organization` distinguishes "HFR Verified" from
  "Manual" entries.

---

## ADR-004 — HFR fields added to CRM Organization, not a child DocType; full registry attribute set

**Status:** Accepted (expanded to full field set 2026-08-01)

### Context
HFR data about a facility (FID, MFL code, level, owner type, coordinates, sync
status) could be stored as:

- (A) Flat fields on `CRM Organization` itself.
- (B) A child DocType `CRM Organization HFR Data` (one-to-one row).
- (C) A separate Single linked record.

### Decision
**Option A — flat fields on `CRM Organization`.**

Rationale:
- One-to-one relationship (each org has at most one HFR record).
- Flat fields are indexed directly, simpler to filter/sort in list views and reports.
- Avoids JOIN overhead and the complexity of child-table logic for a trivial one-to-one.
- Consistent with how `healthpro_erp.health_facility` handles HFR fields (flat on the
  DocType).

Fields — four sub-sections within the "Registry" section on `CRM Organization`:

**Registry Identity**
```
hfr_facility_id            Data       — HFR FID (hie_id)
mfl_code                   Data       — Master Facility List code
facility_type              Data       — e.g. "Dispensary", "Hospital"
facility_category          Data       — e.g. "In-Patient", "Out-Patient"
facility_level             Data       — KEPHL Level (Level 2–6)
facility_owner             Data       — Owning entity name
facility_owner_type        Data       — Public / Private / Faith-Based / NGO
regulatory_body            Data       — e.g. "Kenya Medical Practitioners Board"
registration_number        Data       — Official registration number
board_registration_number  Data       — Board-specific registration
operational_status         Data       — e.g. "Operational", "Closed"
kra_pin                    Data       — KRA PIN
```

**Registry Location**
```
hfr_county                 Data       — County (used for Territory mapping)
hfr_sub_county             Data       — Sub-county
hfr_constituency           Data       — Constituency
hfr_ward                   Data       — Ward
latitude                   Float      — HFR latitude
longitude                  Float      — HFR longitude
```

**Registry Licensing**
```
license_number             Data       — License number
license_type               Data       — License type
license_expiry             Data       — License expiry date
facility_standing          Data       — e.g. "Good Standing", "Suspended"
```

**Registry Operations**
```
open_whole_day             Check      — Open 24 hours
open_weekends              Check      — Open on weekends
open_public_holidays       Check      — Open on public holidays
open_late_night            Check      — Open late night
number_of_beds             Int        — Number of beds
number_of_cots             Int        — Number of cots
```

**Registry Sync Metadata** (read-only)
```
hfr_sync_status            Select     — HFR Verified / Manual; default: Manual
hfr_last_synced            Datetime   — Set by resync_organization()
```

`CRM Lead` carries only the minimal identification set:
`hfr_facility_id`, `mfl_code`, `facility_level`, `facility_owner_type`, `hfr_sync_status`.
Coordinates, licensing, and timestamps live only on Organisation (OQ-2 resolved).

### Consequences
- `bench migrate` required after DocType JSON changes.
- New fields appear in Frappe list/detail views automatically; no Vue changes needed
  for the raw fields — only the modal pre-fill and detail page "Registry" section need
  new Vue code.

---

## ADR-005 — HFR search UI: inline panel inside the create modal, not a separate step

**Status:** Accepted

### Context
Several UX approaches were considered for the HFR lookup affordance inside
`OrganizationModal.vue` and `LeadModal.vue`:

- (A) A separate "Find on HFR" dialog/step before the create form opens.
- (B) An inline collapsible panel inside the existing modal, above the form fields.
- (C) A search input replacing the `organization_name` field with autocomplete
  against HFR in real-time.

### Decision
**Option B — inline collapsible panel** inside the existing modal.

Rationale:
- **No modals / no drawers on primary work surfaces** (project rule). Option A
  requires either a nested modal or a multi-step wizard, both disallowed.
- Option C (autocomplete) would fire on every keystroke, creating excessive API calls
  to an external system with ~3 s latency. It also prevents free-text manual creation
  (agent types a name that doesn't exist in HFR yet).
- Option B keeps a single-screen flow. The agent either expands the panel and searches,
  or ignores it and fills the form manually. The panel is collapsed by default so it
  does not disrupt agents who don't need it.

### UI spec for the panel
```
┌─────────────────────────────────────────────────────────────┐
│  New Organisation                                           │
│  ─────────────────────────────────────────────────────────  │
│  [▼ Search Health Facility Registry]  ← toggle button       │
│                                                             │
│  (when expanded)                                            │
│  ┌───────────────────────────────────┐  [Search]           │
│  │ Facility name or MFL code...      │                     │
│  └───────────────────────────────────┘                     │
│                                                             │
│  Results:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ● Kenyatta National Hospital   MFL 13100  Lvl 6      │  │
│  │   Nairobi · Public · Operational                     │  │
│  │                             [Use this facility]      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ ● Karen Hospital               MFL 19647  Lvl 4      │  │
│  │   Nairobi · Private · Operational                    │  │
│  │                             [Use this facility]      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Organisation Name  [Kenyatta National Hospital          ]  │
│  HFR Facility ID    [FID-00013100                        ]  │
│  MFL Code           [13100                               ]  │
│  Territory          [Nairobi County                      ]  │
│  ...                                                        │
│                              [Cancel]  [Create]             │
└─────────────────────────────────────────────────────────────┘
```

### Consequences
- `OrganizationModal.vue` and `LeadModal.vue` each gain ~80–100 lines of new Vue
  template + script for the panel.
- A shared composable `useHfrSearch()` extracts the search/select logic to avoid
  duplication.
- Loading state and error state must be handled inside the panel (not toast-only,
  so the agent can retry without closing the modal).

---

## ADR-006 — HFR API module: standalone `crm/api/hfr.py`, not folded into existing modules

**Status:** Accepted

### Context
The CRM backend has several API modules: `crm/api/doc.py`, `crm/api/session.py`,
`crm/api/contact.py`, etc. HFR-related whitelisted methods could be added to any of
these or placed in a new file.

### Decision
New file `crm/api/hfr.py` with three public functions:

```python
@frappe.whitelist(methods=["GET"])
def search_facility(query: str, search_by: str = "facility_name") -> list:
    ...

@frappe.whitelist(methods=["GET"])
def get_facility_detail(fid: str) -> dict:
    ...

@frappe.whitelist(methods=["POST"])
def resync_organization(organization_name: str) -> dict:
    ...
```

Private helpers (no `@frappe.whitelist`): `_get_hfr_settings()`, `_generate_jwt()`,
`_hfr_request(url, params)`.

Rationale: HIE/HFR is a distinct external dependency. Separating it into its own
module makes it easy to mock in tests, easy to find, and easy to disable by removing
the import rather than editing a shared module.

### Consequences
- `crm/hooks.py` does NOT need changes (whitelisted methods are auto-discovered).
- All three functions must handle `hfr_enabled = False` by raising
  `frappe.throw(_("HFR integration is not enabled."), frappe.PermissionError)`.
- `_generate_jwt()` uses PyJWT (`jwt.encode`), which is already available in Frappe's
  Python environment (used by `healthpro_erp`). Confirm with `pip show PyJWT` before
  implementation.

---

## ADR-007 — Territory mapping: best-effort, not blocking

**Status:** Accepted

### Context
HFR returns `county` (e.g. `"Nairobi"`) and `sub_county`. CRM `CRM Organization` has
a `territory` field (Link → CRM Territory). There may or may not be a matching
`CRM Territory` record for every HFR county.

### Decision
Territory mapping is **best-effort**:
1. `get_facility_detail` returns `county` as a plain string.
2. The backend attempts `frappe.db.exists("CRM Territory", {"territory_name": county})`.
3. If a match is found, `territory` is set in the returned field map.
4. If no match, `territory` is omitted from the field map — the agent fills it
   manually or the field stays blank.

This is **not** a blocking error. The HFR lookup succeeds regardless of territory
match. Creating territory records to match HFR counties is a separate admin task
(out of scope for this BRD).

### Consequences
- No hard dependency on territory setup. Feature works day one.
- A follow-up task can pre-seed `CRM Territory` records from KMHFR county list.

---

## ADR-008 — UIUX consistency: reuse frappe-ui primitives, no custom design system

**Status:** Accepted

### Context
Tiberbu CRM uses `frappe-ui` (Vue component library) + Tailwind for all UI. The
project has a glassmorphic theme spec but the HFR search panel is an internal
admin surface (Sales Agent use), not a public-facing form. The panel will be seen
inside an existing modal that already uses `frappe-ui` components (`Dialog`, `Input`,
`Button`, `Spinner`).

### Decision
HFR search panel uses only `frappe-ui` + Tailwind utility classes — no new CSS
variables, no glassmorphic treatment, no custom components. The panel should feel like
a native part of the existing modal, not a "feature callout".

Specific components:
- `frappe-ui` `Button` (variant `subtle`) for the toggle.
- Standard `Input` with magnifying glass icon prefix for the search field.
- `frappe-ui` `LoadingIndicator` / `Spinner` during API call.
- A `ul` / `li` list with hover highlight (Tailwind `hover:bg-gray-100 dark:hover:bg-gray-700`) for results.
- `frappe-ui` `Badge` for facility level and owner type chips.

### Consequences
- Dark/light mode parity is automatic (frappe-ui tokens handle it).
- No new CSS files needed.
- Implementation stays within the existing design language — no glassmorphic skill
  invocation needed for this feature.

---

## ADR-010 — Organisation auto-created after Lead save, not at HFR select time

**Status:** Accepted (OQ-4 resolved 2026-08-01)

### Context
When an agent selects an HFR result inside the Lead modal, a `CRM Organization`
record may need to be created. The question was whether to create it immediately on
select (so it exists before the Lead is saved) or after the Lead is saved.

### Decision
**After Lead save.** The existing `CRM Lead.create_organization()` method is extended
to carry HFR fields through when it creates the Organisation. No Organisation is
written to the database until the agent confirms the Lead.

Rationale:
- Creating an Organisation at select-time would mean an aborted Lead creation leaves
  an orphan Organisation in the database.
- The existing `create_organization()` path already handles deduplication
  (`frappe.db.exists("CRM Organization", {"organization_name": ...})`). Extending it
  is a minimal diff.
- Agents frequently open and close create modals without submitting. Creating records
  eagerly would pollute the Organisation list with half-formed entries.

### Consequences
- `CRM Lead` must carry the full HFR field set needed to seed the Organisation
  (FR-5). `create_organization()` reads these fields from the Lead when creating the Org.
- No background job or `after_insert` hook needed for this path.
- If a matching Organisation already exists, `create_organization()` skips creation
  and links — same as today, but now also copies HFR fields onto the existing Org
  using fill-empty semantics.

---

## ADR-009 — No real-time HFR auto-sync; manual re-sync only (MVP)

**Status:** Accepted

### Context
Options for keeping HFR data fresh on Organisation records:
- (A) Background scheduler job that periodically re-syncs all HFR-verified Orgs.
- (B) Triggered re-sync when Organisation is opened in the detail view.
- (C) Manual "Re-sync from HFR" button on the detail page (explicit admin action).

### Decision
**Option C — manual re-sync button only** for the initial release.

Rationale:
- HFR data changes infrequently (facility levels, ownership changes are regulatory
  events). A scheduler job adds operational overhead (queue load, error monitoring)
  for minimal practical benefit in MVP.
- Option B would add latency to every Organisation page load and requires careful
  caching to avoid hammering HIE.
- Option C is transparent: agents and admins know exactly when data was last refreshed
  (`hfr_last_synced` field). No surprising background overwrites.

The scheduler job (Option A) is a natural follow-up once the re-sync API is battle-tested.

### Consequences
- `hfr_last_synced` is set only by `resync_organization()`.
- Organisation detail page shows `hfr_last_synced` so agents can judge data staleness.
- No new scheduler entries in `hooks.py` at this time.

---

## Implementation Sequence

The natural build order minimises risk and allows incremental testing:

```
Phase 1 — Backend foundation
  1a. Add HFR fields to CRM Organization JSON + migrate
  1b. Add HFR fields to CRM Lead JSON + migrate
  1c. Add hfr_enabled/credentials fields to CRM Settings + migrate
  1d. Implement crm/api/hfr.py (search, detail, resync)
  1e. Unit-test hfr.py against a mock HIE response

Phase 2 — Frontend: Create modals
  2a. Implement useHfrSearch() composable
  2b. Wire HFR panel into OrganizationModal.vue
  2c. Wire HFR panel into LeadModal.vue
  2d. Manual browser test: search → select → fill → create

Phase 3 — Frontend: Detail page
  3a. Add "Registry" section to Organization.vue
  3b. Wire "Re-sync from HFR" button to resync API
  3c. Manual browser test: re-sync overwrites HFR fields

Phase 4 — Settings UI
  4a. Add HFR section to CRM Settings UI (Vue)
  4b. Manual test: disable toggle hides HFR button in modals

Phase 5 — QA
  5a. Full flow: configure HFR creds → create org via HFR → verify fields
  5b. Error path: invalid creds → graceful toast, modal still works
  5c. Dark mode visual check
```

---

## Context7 Validation Checklist

Before implementing each phase, query Context7 for:

| Claim | Context7 query required |
|-------|------------------------|
| `frappe.whitelist(methods=["GET"])` signature in Frappe v15 | `frappe whitelist methods` |
| `frappe.db.exists` for Link field validation | `frappe db exists` |
| `frappe.db.set_value` multi-field update | `frappe db set_value` |
| frappe-ui `Dialog` / `Input` / `Button` current API | `frappe-ui dialog input button` |
| PyJWT `jwt.encode` signature (HS256) | `pyjwt encode hs256` |
| Vue 3 composable pattern (`useHfrSearch`) | `vue 3 composables` |
| `createResource` at setup time (frappe-ui) | `frappe-ui createResource` |
