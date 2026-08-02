# BMAD Epic Breakdown: Health Facility Registry (HFR) Integration

**Date:** 2026-08-01
**Project:** crm (Tiberbu CRM fork)
**Status:** Ready for sprint planning
**Branch:** careverse_fixes
**BRD:** `hfr-integration/planning-artifacts/hfr-integration-brd.md` (v1.1 — Approved)
**ADR:** `hfr-integration/planning-artifacts/hfr-integration-adr.md`

---

## Architecture Summary

```
Sales Agent opens OrganizationModal / LeadModal
  → types ≥ 3 chars in HFR search panel → clicks Search
      → Vue calls crm.api.hfr.search_facility(query, search_by)
          → Python generates short-lived JWT from CRM Settings HIE creds
          → GET {hfr_url}{hfr_fetch_path}?facility-name=... (Bearer JWT)
          → returns [{fid, name, mfl_code, level, county, owner_type, ...}]
  → agent selects a result → Vue calls crm.api.hfr.get_facility_detail(fid)
          → Python fetches full HFR record for that FID
          → returns field-map keyed to CRM Organization fieldnames
  → applyHfrPreview(doc, hfrFields) fills empty form fields
  → agent clicks Create → frappe.client.insert saves CRM Organization / CRM Lead
      → on Lead save: lead.create_organization() extended to carry HFR fields through

Organisation detail page (post-save):
  → "Re-sync from HFR" button → confirmation prompt (fill-empty | overwrite)
      → crm.api.hfr.resync_organization(organization_name, mode)
          → fetch HFR detail by stored hfr_facility_id
          → apply mode to HFR-managed fields only
          → update hfr_last_synced + hfr_sync_status = "HFR Verified"
```

**Key constraints:**
- All HIE calls are **server-side Python only** — JWT and credentials never reach the browser.
- CRM holds its own HIE credentials in `CRM HFR Settings` (separate Single DocType;
  mirrors `CRM SES Settings` pattern). Not proxied through `healthpro_erp`.
- `hfr_enabled = false` by default. All HFR UI uses `v-if` (not `v-show`) — elements
  are conditionally not rendered, not hidden.
- `CRM Lead` carries only 5 identification fields; coordinates live on `CRM Organization` only.
- Organisation auto-created **after Lead save**, not at HFR select time (prevents orphans).
- Re-sync mode is the agent's choice at click time (fill-empty OR overwrite) — both
  modes restrict writes to the HFR-managed field set only.
- No `on_update` hooks for side effects. No scheduler jobs (post-MVP).
- `bench restart` after every Python change. `bench migrate` after every DocType JSON change.

---

## Reference Files (read before implementing)

| File | Why |
|------|-----|
| `crm/api/ses.py` | Pattern for a `get_settings` / `update_settings` whitelist pair against a Single DocType |
| `crm/fcrm/doctype/crm_ses_settings/crm_ses_settings.json` | Pattern for a Settings Single DocType |
| `frontend/src/components/Settings/SESSettings.vue` | Pattern for a Settings page section (enable toggle → conditional fields → save) |
| `frontend/src/components/Settings/Settings.vue` | Where to register the new HFR tab (tabs computed array, lines 101–262) |
| `frontend/src/components/Modals/OrganizationModal.vue` | Modal to extend with HFR panel |
| `frontend/src/components/Modals/LeadModal.vue` | Modal to extend with HFR panel |
| `frontend/src/pages/Organization.vue` | Detail page to extend with Registry section |
| `crm/fcrm/doctype/crm_lead/crm_lead.py:251` | `create_organization()` method to extend |
| `healthpro_erp/api/hie_settings.py` | `HIE.generate_jwt_token()` — exact JWT pattern to replicate |
| `healthpro_erp/api/facility_onboarding_v2.py` | `fetch_facility_hwr_fr()` — exact HFR request pattern to replicate |

---

## Story Dependency Chain

```
P1 (backend, parallelisable within phase)
  hfr-p1-doctype-org-fields   ──┐
  hfr-p1-doctype-lead-fields  ──┤── all must be merged + migrated before P2
  hfr-p1-settings-fields      ──┤
  hfr-p1-api-module           ──┘

P2 (frontend modals — depends on P1)
  hfr-p2-composable           ──┐── composable must exist before modal stories
  hfr-p2-org-modal            ──┤
  hfr-p2-lead-modal           ──┘

P3 (detail page — depends on P1 + P2)
  hfr-p3-org-detail-registry

P4 (settings UI — depends on P1 settings fields; parallelisable with P2/P3)
  hfr-p4-settings-ui

P5 (QA — depends on all above)
  hfr-qa-full-flow
```

---

## Phase 1 — Backend Foundation

### Story: `hfr-p1-doctype-org-fields`
**Title:** CRM Organization — add HFR Registry fields  
**BRD ref:** FR-4  
**Estimate:** S

**What to build:**
Add a new "Health Facility Registry" section to
`crm/fcrm/doctype/crm_organization/crm_organization.json` with the following fields.

Section label: `Health Facility Registry`

**Sub-section: Registry Identity**
```
hfr_facility_id            Data       "HFR Facility ID"
mfl_code                   Data       "MFL Code"
facility_type              Data       "Facility Type"
facility_category          Data       "Category"
facility_level             Data       "Facility Level"
facility_owner             Data       "Facility Owner"
facility_owner_type        Data       "Owner Type"
regulatory_body            Data       "Regulatory Body"
registration_number        Data       "Registration Number"
board_registration_number  Data       "Board Registration No."
operational_status         Data       "Operational Status"
kra_pin                    Data       "KRA PIN"
```

**Sub-section: Registry Location**
```
hfr_county                 Data       "County"
hfr_sub_county             Data       "Sub-County"
hfr_constituency           Data       "Constituency"
hfr_ward                   Data       "Ward"
latitude                   Float      "Latitude"
longitude                  Float      "Longitude"
```

**Sub-section: Registry Licensing**
```
license_number             Data       "License Number"
license_type               Data       "License Type"
license_expiry             Data       "License Expiry"
facility_standing          Data       "Standing"
```

**Sub-section: Registry Operations**
```
open_whole_day             Check      "Open Whole Day"
open_weekends              Check      "Open Weekends"
open_public_holidays       Check      "Open Public Holidays"
open_late_night            Check      "Open Late Night"
number_of_beds             Int        "Number of Beds"
number_of_cots             Int        "Number of Cots"
```

**Sub-section: Registry Sync**
```
hfr_sync_status            Select     "HFR Sync Status"   options: \nHFR Verified\nManual  default: Manual
hfr_last_synced            Datetime   "Last HFR Sync"     read_only: 1
```

All fields: `in_list_view: 0`, `search_index: 0` (except `hfr_facility_id` and `mfl_code`
which get `search_index: 1`).

**Implementation notes:**
- Edit the JSON directly (do not use Frappe desk migrate UI).
- Run `bench --site cr-dev.tiberbu.app migrate` after saving the JSON.
- No Python controller changes needed for this story.

**Proof:** `bench --site cr-dev.tiberbu.app execute frappe.db.sql --args "['DESC \`tabCRM Organization\`']"` output showing new columns.

---

### Story: `hfr-p1-doctype-lead-fields`
**Title:** CRM Lead — add minimal HFR identification fields  
**BRD ref:** FR-5  
**Estimate:** XS

**What to build:**
Add a "Health Facility Registry" section to
`crm/fcrm/doctype/crm_lead/crm_lead.json` with only the identification subset:

```
hfr_facility_id    Data     "HFR Facility ID"   search_index: 1
mfl_code           Data     "MFL Code"
facility_level     Data     "Facility Level"
facility_owner_type Data    "Owner Type"
hfr_sync_status    Select   "HFR Sync Status"   options: \nHFR Verified\nManual  default: Manual
```

No coordinates, no timestamps, no licensing fields on Lead.

**Proof:** `DESC \`tabCRM Lead\`` output showing the 5 new columns.

---

### Story: `hfr-p1-settings-fields`
**Title:** CRM HFR Settings — new Single DocType for HIE credentials  
**BRD ref:** FR-6, ADR-002  
**Estimate:** S

**What to build:**
Create a new Single DocType `CRM HFR Settings` following the exact pattern of
`crm/fcrm/doctype/crm_ses_settings/`.

Files to create:
```
crm/fcrm/doctype/crm_hfr_settings/
  __init__.py
  crm_hfr_settings.json
  crm_hfr_settings.py
```

Fields in `crm_hfr_settings.json`:
```
hfr_enabled        Check     "Enable HFR Integration"   default: 0
--- Section Break: HIE Credentials ---
hfr_url            Data      "HIE Base URL"             depends_on: eval:doc.hfr_enabled
hfr_fetch_path     Data      "HFR Fetch Path"           default: /v1/hfr/facilities  depends_on: eval:doc.hfr_enabled
hfr_username       Data      "HIE Username"             depends_on: eval:doc.hfr_enabled
hfr_password       Password  "HIE Password"             depends_on: eval:doc.hfr_enabled
hfr_jwt_expiry     Int       "JWT Expiry (seconds)"     default: 20000  depends_on: eval:doc.hfr_enabled
```

`crm_hfr_settings.py`: stub controller (class body = `pass`).

Run `bench --site cr-dev.tiberbu.app migrate` after creation.

**Proof:** `frappe.get_single("CRM HFR Settings")` via bench console returns the doc
with `hfr_enabled = 0` and all fields present.

---

### Story: `hfr-p1-api-module`
**Title:** `crm/api/hfr.py` — search, detail, resync whitelist methods  
**BRD ref:** FR-1, FR-2, FR-3, FR-7, ADR-006  
**Estimate:** M

**What to build:**
New file `crm/api/hfr.py`. Three public whitelisted functions + private helpers.

```python
# crm/api/hfr.py

import time
import frappe
from frappe import _
import requests
import jwt  # PyJWT — already available in frappe env

_DOCTYPE = "CRM HFR Settings"


def _get_settings():
    s = frappe.get_single(_DOCTYPE)
    if not s.hfr_enabled:
        frappe.throw(_("HFR integration is not enabled."), frappe.PermissionError)
    return s


def _generate_jwt(s):
    payload = {"key": s.hfr_username, "exp": int(time.time()) + (s.hfr_jwt_expiry or 20000)}
    return jwt.encode(payload, s.get_password("hfr_password"), algorithm="HS256")


def _hfr_request(url, params):
    s = _get_settings()
    token = _generate_jwt(s)
    resp = requests.get(url, params=params, headers={"Authorization": "Bearer %s" % token}, timeout=10)
    resp.raise_for_status()
    return resp.json()


@frappe.whitelist(methods=["GET"])
def search_facility(query, search_by="facility_name"):
    """Return a list of HFR facility candidates matching query."""
    s = _get_settings()
    param_map = {
        "facility_name": "facility-name",
        "registration_number": "registration-number",
        "facility_code": "facility-code",
    }
    if search_by not in param_map:
        frappe.throw(_("Invalid search_by value."))
    url = "%s%s" % (s.hfr_url.rstrip("/"), s.hfr_fetch_path)
    params = {param_map[search_by]: query}
    data = _hfr_request(url, params)
    # Normalise — HFR returns data under "message" key (same as healthpro_erp pattern)
    facilities = data.get("message") or data.get("data") or []
    if not isinstance(facilities, list):
        facilities = [facilities]
    return [
        {
            "fid": f.get("facility_fid") or f.get("hie_id"),
            "name": f.get("facility_name"),
            "mfl_code": f.get("facility_mfl"),
            "level": f.get("kephl_level"),
            "category": f.get("category"),
            "county": f.get("county"),
            "owner_type": f.get("facility_owner_type"),
            "operational_status": f.get("operational_status"),
        }
        for f in facilities
        if f.get("facility_fid") or f.get("hie_id")
    ]


@frappe.whitelist(methods=["GET"])
def get_facility_detail(fid):
    """Return HFR fields keyed to CRM Organization fieldnames for a given FID."""
    s = _get_settings()
    url = "%s%s" % (s.hfr_url.rstrip("/"), s.hfr_fetch_path)
    data = _hfr_request(url, {"facility-fid": fid})
    f = data.get("message") or data.get("data") or {}
    if isinstance(f, list):
        f = f[0] if f else {}

    # Best-effort territory mapping
    territory = None
    county = f.get("county")
    if county:
        territory = frappe.db.exists("CRM Territory", {"territory_name": county})

    return {
        "organization_name": f.get("facility_name"),
        "hfr_facility_id": f.get("facility_fid") or f.get("hie_id"),
        "mfl_code": f.get("facility_mfl"),
        "facility_type": f.get("facility_type"),
        "facility_category": f.get("category"),
        "facility_level": f.get("kephl_level"),
        "facility_owner": f.get("facility_owner"),
        "facility_owner_type": f.get("facility_owner_type"),
        "regulatory_body": f.get("regulatory_body"),
        "registration_number": f.get("registration_number"),
        "board_registration_number": f.get("board_registration_number"),
        "operational_status": f.get("operational_status"),
        "kra_pin": f.get("kra_pin"),
        "hfr_county": f.get("county"),
        "hfr_sub_county": f.get("sub_county"),
        "hfr_constituency": f.get("constituency"),
        "hfr_ward": f.get("ward"),
        "latitude": f.get("latitude"),
        "longitude": f.get("longitude"),
        "license_number": f.get("license_number"),
        "license_type": f.get("license_type"),
        "license_expiry": f.get("license_expiry"),
        "facility_standing": f.get("standing"),
        "open_whole_day": f.get("open_whole_day", 0),
        "open_weekends": f.get("open_weekends", 0),
        "open_public_holidays": f.get("open_public_holiday", 0),
        "open_late_night": f.get("open_late_night", 0),
        "number_of_beds": f.get("number_of_beds"),
        "number_of_cots": f.get("number_of_cots"),
        "territory": territory,
        "hfr_sync_status": "HFR Verified",
    }


@frappe.whitelist(methods=["POST"])
def resync_organization(organization_name, mode="fill_empty"):
    """Re-sync HFR-managed fields on an existing CRM Organization.

    mode: 'fill_empty' | 'overwrite'
    """
    if mode not in ("fill_empty", "overwrite"):
        frappe.throw(_("Invalid mode. Use 'fill_empty' or 'overwrite'."))

    org = frappe.get_doc("CRM Organization", organization_name)
    if not org.hfr_facility_id:
        frappe.throw(_("This organisation has no HFR Facility ID. Search HFR to link one first."))

    hfr_fields = get_facility_detail(org.hfr_facility_id)
    # Remove keys that are not HFR-managed (organisation_name, territory handled separately)
    non_hfr = {"organization_name", "territory"}
    hfr_fields = {k: v for k, v in hfr_fields.items() if k not in non_hfr}

    updated = []
    for field, value in hfr_fields.items():
        if value is None:
            continue
        if mode == "fill_empty" and org.get(field):
            continue
        org.set(field, value)
        updated.append(field)

    import frappe.utils
    org.hfr_last_synced = frappe.utils.now_datetime()
    org.hfr_sync_status = "HFR Verified"
    org.save(ignore_permissions=False)  # respect normal permissions — this is a user action

    return {"updated_fields": updated, "hfr_facility_id": org.hfr_facility_id}
```

**Critical:** run `bench restart` after creating the file.

**Proof:** bench console call —
```python
import frappe
frappe.init(site="cr-dev.tiberbu.app"); frappe.connect()
# First enable + configure settings, then:
from crm.api.hfr import search_facility
print(search_facility("Kenyatta", "facility_name"))
```
Paste the response JSON as proof.

---

## Phase 2 — Frontend: Create Modals

### Story: `hfr-p2-composable`
**Title:** `useHfrSearch()` composable + `applyHfrPreview()` helper  
**BRD ref:** FR-8, ADR-003, ADR-005  
**Estimate:** S

**What to build:**
New file `frontend/src/composables/useHfrSearch.js`.

```js
// frontend/src/composables/useHfrSearch.js
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export function useHfrSearch() {
  const query = ref('')
  const searchBy = ref('facility_name')
  const results = ref([])
  const selectedFid = ref(null)
  const panelOpen = ref(false)

  const searchResource = createResource({
    url: 'crm.api.hfr.search_facility',
    onSuccess(data) { results.value = data },
    onError() { results.value = [] },
  })

  const detailResource = createResource({
    url: 'crm.api.hfr.get_facility_detail',
  })

  function search() {
    if (query.value.length < 3) return
    results.value = []
    searchResource.submit({ query: query.value, search_by: searchBy.value })
  }

  async function selectFacility(fid, doc) {
    selectedFid.value = fid
    await detailResource.submit({ fid })
    if (detailResource.data) {
      applyHfrPreview(doc, detailResource.data)
    }
  }

  function reset() {
    query.value = ''
    results.value = []
    selectedFid.value = null
    panelOpen.value = false
  }

  const searching = computed(() => searchResource.loading)
  const fetchingDetail = computed(() => detailResource.loading)

  return { query, searchBy, results, selectedFid, panelOpen, search, selectFacility, reset, searching, fetchingDetail }
}

/**
 * Fill-empty: only sets a field on `doc` if the current value is null/undefined/empty.
 * `doc` is the reactive frappe-ui document object (doc.doc or doc directly).
 */
export function applyHfrPreview(doc, hfrFields) {
  const target = doc.doc ?? doc
  for (const [field, value] of Object.entries(hfrFields)) {
    if (value === null || value === undefined) continue
    const current = target[field]
    if (current === null || current === undefined || current === '' || current === 0) {
      target[field] = value
    }
  }
}
```

**Notes:**
- `createResource` must be declared at setup time per project rules — both resources
  are declared at composable init, not inside functions.
- No TypeScript (`.js` not `.ts`) — this repo uses `.js` for composables.

**Proof:** unit test or manual console verification that `applyHfrPreview` does not
overwrite a non-empty field. A simple screenshot of the browser console showing the
composable imported cleanly is acceptable.

---

### Story: `hfr-p2-org-modal`
**Title:** `OrganizationModal.vue` — inline HFR search panel  
**BRD ref:** FR-8, US-01, ADR-005, ADR-008  
**Estimate:** M

**What to build:**
Extend `frontend/src/components/Modals/OrganizationModal.vue`.

**Setup additions:**
```js
import { useHfrSearch, applyHfrPreview } from '@/composables/useHfrSearch'
// check whether HFR is enabled (from session or a lightweight resource)
const hfrEnabled = inject('hfrEnabled', false)  // provided at app level or via a resource
const { query, searchBy, results, panelOpen, search, selectFacility, searching } = useHfrSearch()
```

**Template additions** — insert above the `<FieldLayout>`:
```html
<template v-if="hfrEnabled">
  <!-- Toggle button -->
  <div class="px-1 pb-2">
    <Button
      variant="subtle"
      :label="panelOpen ? __('Hide Registry Search') : __('Search Health Facility Registry')"
      @click="panelOpen = !panelOpen"
    />
  </div>

  <!-- Search panel -->
  <div v-if="panelOpen" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 mb-3 flex flex-col gap-2">
    <div class="flex gap-2">
      <FormControl
        v-model="query"
        :placeholder="__('Facility name or MFL code...')"
        class="flex-1"
        @keydown.enter="search"
      />
      <Button variant="solid" :label="__('Search')" :loading="searching" @click="search" />
    </div>

    <div v-if="searching" class="flex justify-center py-2">
      <LoadingIndicator class="size-5" />
    </div>

    <div v-else-if="results.length === 0 && query.length >= 3" class="text-p-sm text-ink-gray-5 px-1">
      {{ __('No results — create manually or try a different search.') }}
    </div>

    <ul v-else class="flex flex-col gap-1 max-h-48 overflow-y-auto">
      <li
        v-for="r in results"
        :key="r.fid"
        class="flex items-start justify-between rounded px-2 py-2 hover:bg-surface-gray-2 cursor-pointer"
      >
        <div class="flex flex-col gap-0.5">
          <span class="text-p-sm-medium text-ink-gray-8">{{ r.name }}</span>
          <span class="text-p-xs text-ink-gray-5">
            MFL {{ r.mfl_code }} · {{ r.level }} · {{ r.county }} · {{ r.owner_type }}
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          :label="__('Use')"
          @click="selectFacility(r.fid, organization)"
        />
      </li>
    </ul>
  </div>
</template>
```

**`hfrEnabled` provision:** add to the app-level `provide` in `main.js` or fetch from
a `createResource` that calls `crm.api.hfr.get_hfr_enabled` (a new 2-line whitelist
method that returns `frappe.db.get_single_value("CRM HFR Settings", "hfr_enabled")`).
Whichever approach, it must be reactive and available before the modal renders.

**Proof:** screenshot of the modal with the HFR panel expanded showing at least one
search result and the form fields pre-filled after clicking "Use".

---

### Story: `hfr-p2-lead-modal`
**Title:** `LeadModal.vue` — HFR panel + `create_organization()` extension  
**BRD ref:** FR-9, US-02, ADR-010  
**Estimate:** M

**What to build:**

**Part A — `LeadModal.vue`:** Same HFR search panel as `hfr-p2-org-modal`. The `selectFacility`
call targets `lead` (the Lead doc object). The HFR fields filled onto the Lead are the
5 from FR-5: `hfr_facility_id`, `mfl_code`, `facility_level`, `facility_owner_type`,
`hfr_sync_status`. Also fills `organization` ← `organization_name` from HFR detail.

**Part B — `crm/fcrm/doctype/crm_lead/crm_lead.py` — extend `create_organization()`:**

```python
def create_organization(self, existing_organization=None):
    if not self.organization and not existing_organization:
        return

    existing_organization = existing_organization or frappe.db.exists(
        "CRM Organization", {"organization_name": self.organization}
    )
    if existing_organization:
        self.db_set("organization", existing_organization)
        self.copy_enrichment_from_organization()
        # NEW: copy HFR fields fill-empty onto existing org
        _copy_hfr_fields_to_org(self, existing_organization)
        return existing_organization

    organization = frappe.new_doc("CRM Organization")
    organization.update({
        "organization_name": self.organization,
        "website": self.website,
        "territory": self.territory,
        "industry": self.industry,
        "annual_revenue": self.annual_revenue,
    })
    # NEW: carry HFR fields through
    for field in _HFR_ORG_FIELDS:
        val = self.get(field)
        if val:
            organization.set(field, val)
    organization.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    return organization.name
```

Add near top of file:
```python
# HFR fields that exist on both CRM Lead and CRM Organization
_HFR_ORG_FIELDS = [
    "hfr_facility_id", "mfl_code", "facility_level",
    "facility_owner_type", "hfr_sync_status",
]

def _copy_hfr_fields_to_org(lead, org_name):
    """Fill-empty copy of HFR identification fields from Lead onto an existing Org."""
    org = frappe.get_doc("CRM Organization", org_name)
    dirty = False
    for field in _HFR_ORG_FIELDS:
        if lead.get(field) and not org.get(field):
            org.set(field, lead.get(field))
            dirty = True
    if dirty:
        org.save(ignore_permissions=True)  # SYSTEM-INTERNAL
```

Run `bench restart` after Python changes.

**Proof:**
1. Screenshot: Lead modal with HFR panel and a result selected.
2. API/terminal dump showing the `CRM Organization` created after lead save carries
   `hfr_facility_id` and `mfl_code`.

---

## Phase 3 — Frontend: Organisation Detail Page

### Story: `hfr-p3-org-detail-registry`
**Title:** `Organization.vue` — Registry section + Re-sync button  
**BRD ref:** FR-10, US-03, ADR-003  
**Estimate:** M

**What to build:**

**Part A — Registry read-only section** in `frontend/src/pages/Organization.vue`.
Add a new tab or section (follow the existing tabs pattern in the file — look for
how the "Deals" and "Contacts" tabs are structured). The Registry section is
read-only display of the FR-4 field groups.

```html
<!-- Registry section — inside a v-if="hfrEnabled && organization.doc?.hfr_facility_id" guard -->
<div class="flex flex-col gap-4 p-4">

  <div class="flex items-center justify-between">
    <h3 class="text-p-base-semibold text-ink-gray-7">{{ __('Health Facility Registry') }}</h3>
    <div class="flex items-center gap-2">
      <Badge
        v-if="organization.doc.hfr_sync_status === 'HFR Verified'"
        :label="__('HFR Verified')"
        theme="green"
        variant="subtle"
      />
      <span v-if="organization.doc.hfr_last_synced" class="text-p-xs text-ink-gray-5">
        {{ __('Synced') }} {{ formatDate(organization.doc.hfr_last_synced) }}
      </span>
      <Button
        v-if="hfrEnabled && organization.doc.hfr_facility_id"
        variant="subtle"
        size="sm"
        :label="__('Re-sync from HFR')"
        :loading="resyncing"
        @click="showResyncDialog = true"
      />
    </div>
  </div>

  <!-- Field groups rendered as label/value pairs -->
  <!-- Identity, Location, Licensing, Operations sub-sections -->
  <!-- ... label-value grid using the same pattern as other detail sections in this file -->

</div>

<!-- Re-sync confirmation dialog -->
<Dialog v-model="showResyncDialog" :options="{ title: __('Re-sync from Health Facility Registry') }">
  <template #body-content>
    <p class="text-p-sm text-ink-gray-7 mb-4">
      {{ __('How would you like to apply the latest registry data?') }}
    </p>
    <div class="flex flex-col gap-2">
      <Button variant="outline" :label="__('Fill empty fields only')" @click="resync('fill_empty')" />
      <Button variant="outline" theme="red" :label="__('Overwrite all HFR fields')" @click="resync('overwrite')" />
    </div>
  </template>
</Dialog>
```

**Part B — resync logic:**
```js
const showResyncDialog = ref(false)
const resyncing = ref(false)

const resyncResource = createResource({
  url: 'crm.api.hfr.resync_organization',
  onSuccess() {
    resyncing.value = false
    showResyncDialog.value = false
    organization.reload()
    toast.success(__('Registry data updated'))
  },
  onError(err) {
    resyncing.value = false
    toast.error(err?.message || __('Re-sync failed'))
  },
})

function resync(mode) {
  resyncing.value = true
  resyncResource.submit({ organization_name: props.organizationId, mode })
}
```

**Proof:** screenshot of the Organisation detail page showing the Registry section with
HFR data populated, the "HFR Verified" badge, and the confirmation dialog open.

---

## Phase 4 — Settings UI

### Story: `hfr-p4-settings-ui`
**Title:** CRM Settings — HFR Integration tab  
**BRD ref:** FR-6, ADR-002, ADR-008  
**Estimate:** S

**What to build:**

**Part A — `frontend/src/components/Settings/HFRSettings.vue`:**
Follow `SESSettings.vue` exactly:
- Enable toggle (Switch component) at the top.
- Conditional fields block (v-if="form.hfr_enabled"):
  - HIE Base URL
  - HFR Fetch Path
  - HIE Username
  - HIE Password (type="password")
  - JWT Expiry (seconds)
- "Save Changes" button with dirty-state badge.
- `createResource` pairs for `crm.api.hfr.get_hfr_settings` and
  `crm.api.hfr.update_hfr_settings` (add these two whitelist methods to `crm/api/hfr.py`).

New whitelist methods to add to `crm/api/hfr.py`:
```python
@frappe.whitelist()
def get_hfr_settings():
    s = frappe.get_single("CRM HFR Settings")
    return {
        "hfr_enabled": s.hfr_enabled,
        "hfr_url": s.hfr_url,
        "hfr_fetch_path": s.hfr_fetch_path,
        "hfr_username": s.hfr_username,
        "hfr_jwt_expiry": s.hfr_jwt_expiry,
        # password intentionally omitted from GET response
    }

@frappe.whitelist(methods=["POST"])
def update_hfr_settings(settings):
    import json
    if isinstance(settings, str):
        settings = json.loads(settings)
    s = frappe.get_single("CRM HFR Settings")
    s.hfr_enabled = settings.get("hfr_enabled", 0)
    s.hfr_url = settings.get("hfr_url") or ""
    s.hfr_fetch_path = settings.get("hfr_fetch_path") or "/v1/hfr/facilities"
    s.hfr_username = settings.get("hfr_username") or ""
    s.hfr_jwt_expiry = settings.get("hfr_jwt_expiry") or 20000
    if settings.get("hfr_password"):
        s.hfr_password = settings["hfr_password"]
    s.save(ignore_permissions=False)
    return {"success": True}
```

**Part B — Register in `Settings.vue`:**
```js
// Add import
import HFRSettings from '@/components/Settings/HFRSettings.vue'

// Add to the integrations group in the tabs computed array
// (place near ERPNextSettings / WhatsAppSettings):
{
  label: __('HFR Integration'),
  icon: ...,  // use LucideNetwork or a suitable existing icon
  component: markRaw(HFRSettings),
},
```

**Part C — App-level `hfrEnabled` provide:**
In `main.js` or the root App component, after the session loads, provide `hfrEnabled`:
```js
const hfrEnabled = ref(false)
createResource({
  url: 'crm.api.hfr.get_hfr_settings',
  auto: true,
  onSuccess(data) { hfrEnabled.value = !!data.hfr_enabled },
})
provide('hfrEnabled', hfrEnabled)
```
This is what `OrganizationModal` and `LeadModal` inject.

Run `bench restart` after Python changes. Run `pnpm build` after frontend changes.

**Proof:** screenshot of the Settings page showing the "HFR Integration" tab with the
enable toggle and credential fields.

---

## Phase 5 — QA

### Story: `hfr-qa-full-flow`
**Title:** QA — full HFR integration flow  
**BRD ref:** All FRs, US-01 through US-04  
**Estimate:** S

**Test cases:**

**TC-1 — Happy path: create Organisation via HFR**
1. Go to Settings → HFR Integration. Enable HFR, enter valid HIE credentials. Save.
2. Open Organisations list → New Organisation.
3. Expand HFR panel. Search "Kenyatta". Verify result list appears.
4. Click "Use" on a result. Verify form fills: organisation_name, hfr_facility_id,
   mfl_code, facility_level, county, etc.
5. Click Create. Open the new Organisation. Verify Registry section shows all HFR
   fields with `hfr_sync_status = HFR Verified`.

**TC-2 — Happy path: create Lead via HFR + auto-org creation**
1. Open Leads → Create Lead. Search HFR for a facility.
2. Select a result. Verify `organization`, `hfr_facility_id`, `mfl_code` filled.
3. Click Create. Open the new Lead.
4. Open Organisations list — verify a matching `CRM Organization` was auto-created
   with `hfr_facility_id` populated.

**TC-3 — Re-sync: fill-empty mode**
1. Open an HFR-verified Organisation. Manually blank out `mfl_code`.
2. Click "Re-sync from HFR" → "Fill empty fields only".
3. Verify `mfl_code` is restored. Verify `hfr_last_synced` updated.

**TC-4 — Re-sync: overwrite mode**
1. Open an HFR-verified Organisation. Manually change `facility_level` to "Level 1".
2. Click "Re-sync from HFR" → "Overwrite all HFR fields".
3. Verify `facility_level` reverts to HFR value.

**TC-5 — Feature flag off**
1. Disable HFR in Settings.
2. Open Create Organisation modal — verify no HFR panel is rendered.
3. Open Organisation detail — verify no Registry section and no Re-sync button.

**TC-6 — HFR unreachable**
1. Set `hfr_url` to an invalid URL in Settings.
2. Open Create Organisation, search HFR. Verify error toast appears and modal
   stays open and usable.

**Proof:** screenshots for TC-1 (result list + filled form + Registry section on
detail) and TC-5 (modal without HFR panel). API response dump for TC-3 or TC-4
showing `updated_fields` list in the `resync_organization` response.

---

## Sprint Status Entries (already in sprint-status.yaml)

```yaml
epic-hfr-integration: ready-for-dev

hfr-p1-doctype-org-fields: ready-for-dev
hfr-p1-doctype-lead-fields: ready-for-dev
hfr-p1-settings-fields: ready-for-dev
hfr-p1-api-module: ready-for-dev
hfr-p2-composable: ready-for-dev
hfr-p2-org-modal: ready-for-dev
hfr-p2-lead-modal: ready-for-dev
hfr-p3-org-detail-registry: ready-for-dev
hfr-p4-settings-ui: ready-for-dev
hfr-qa-full-flow: ready-for-dev
```
