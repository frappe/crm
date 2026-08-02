# BMAD Story Breakdown — HFR Cardinality Refactor

**Date:** 2026-08-02
**Epic:** `epic-hfr-refactor`
**BRD:** `hfr-cardinality-refactor-brd.md` (v1.0 — OQ-1 resolved)
**ADR:** `hfr-cardinality-refactor-adr.md`
**Branch:** `careverse_fixes`

---

## Architecture Summary

```
Current (v1.1 — wrong)
  CRM Organization  ──  hfr_facility_id (flat col)
  CRM Lead          ──  hfr_facility_id (flat col)

Target (this refactor)
  CRM Organization  1──* CRM Org Facility   (child table)
  CRM Lead          1──* CRM Lead Facility  (child table)
  CRM Deal          1──* CRM Deal Facility  (child table, copied from Lead at conversion)

Each child row = one HFR-verified facility with its full registry profile.
Sync state (hfr_sync_status, hfr_last_synced) lives only on each child row.
No HFR columns remain on the parent DocTypes.
```

**Critical constraints:**
- Migration patch MUST run BEFORE column drops (`bench migrate` runs patches then
  re-syncs DocType columns — patch order in `patches.txt` controls this).
- Three child DocTypes share the same field schema — keep them in sync.
- `create_deal()` copies Lead fields via a meta loop but skips child tables — facility
  rows must be copied explicitly after `new_deal.insert()`.
- `bench restart` after every Python change. `bench migrate` after every DocType JSON
  change.
- No f-strings in log/error strings (Amazon Inspector B608).

---

## Reference Files (read before implementing)

| File | Why |
|------|-----|
| `crm/patches/v1_0/move_crm_note_data_to_fcrm_note.py` | Patch style: idempotency guard, frappe.db.sql for reads, frappe.get_doc for inserts |
| `crm/patches.txt` | Where to register the new patch (append at end) |
| `crm/fcrm/doctype/crm_organization/crm_organization.json` | DocType to strip flat HFR columns from |
| `crm/fcrm/doctype/crm_lead/crm_lead.json` | DocType to strip flat HFR columns from |
| `crm/fcrm/doctype/crm_deal/crm_deal.json` | DocType to add facilities table to |
| `crm/fcrm/doctype/crm_lead/crm_lead.py:273` | `create_organization()` — rewrite to copy child rows |
| `crm/fcrm/doctype/crm_lead/crm_lead.py:364` | `create_deal()` — extend to copy child rows |
| `crm/fcrm/doctype/crm_lead/crm_lead.py:550` | `convert_to_deal()` module function |
| `crm/api/hfr.py` | Replace `resync_organization()` with `resync_facility_row()` |
| `frontend/src/components/HfrSearchPanel.vue` | Rewrite: append-row semantics + pending list |
| `frontend/src/components/Modals/OrganizationModal.vue` | Wire childDoctype prop |
| `frontend/src/components/Modals/LeadModal.vue` | Wire childDoctype prop |
| `frontend/src/pages/Organization.vue` | Replace flat Registry tab with Facilities tab |
| `frontend/src/pages/Lead.vue` | Add Facilities section |
| `frontend/src/pages/Deal.vue` | Add Facilities section |

---

## Canonical Child DocType Field Schema

All three child DocTypes (`CRM Org Facility`, `CRM Lead Facility`, `CRM Deal Facility`)
use this exact field set. Copy it to all three JSON files.

```json
[
  { "fieldname": "hfr_facility_id",       "fieldtype": "Data",     "label": "HFR Facility ID",      "in_list_view": 1, "search_index": 1 },
  { "fieldname": "facility_name",         "fieldtype": "Data",     "label": "Facility Name",         "in_list_view": 1 },
  { "fieldname": "mfl_code",              "fieldtype": "Data",     "label": "MFL Code",              "in_list_view": 1 },
  { "fieldname": "facility_type",         "fieldtype": "Data",     "label": "Facility Type" },
  { "fieldname": "facility_category",     "fieldtype": "Data",     "label": "Category" },
  { "fieldname": "facility_level",        "fieldtype": "Data",     "label": "Facility Level",        "in_list_view": 1 },
  { "fieldname": "facility_owner",        "fieldtype": "Data",     "label": "Facility Owner" },
  { "fieldname": "facility_owner_type",   "fieldtype": "Data",     "label": "Owner Type",            "in_list_view": 1 },
  { "fieldname": "regulatory_body",       "fieldtype": "Data",     "label": "Regulatory Body" },
  { "fieldname": "registration_number",   "fieldtype": "Data",     "label": "Registration Number" },
  { "fieldname": "operational_status",    "fieldtype": "Data",     "label": "Operational Status" },
  { "fieldname": "hfr_county",            "fieldtype": "Data",     "label": "County",                "in_list_view": 1 },
  { "fieldname": "hfr_sub_county",        "fieldtype": "Data",     "label": "Sub-County" },
  { "fieldname": "hfr_ward",              "fieldtype": "Data",     "label": "Ward" },
  { "fieldname": "latitude",              "fieldtype": "Float",    "label": "Latitude" },
  { "fieldname": "longitude",             "fieldtype": "Float",    "label": "Longitude" },
  { "fieldname": "license_number",        "fieldtype": "Data",     "label": "License Number" },
  { "fieldname": "license_expiry",        "fieldtype": "Data",     "label": "License Expiry" },
  { "fieldname": "facility_standing",     "fieldtype": "Data",     "label": "Standing" },
  { "fieldname": "number_of_beds",        "fieldtype": "Int",      "label": "Number of Beds" },
  { "fieldname": "hfr_sync_status",       "fieldtype": "Select",   "label": "Sync Status",
    "options": "\nHFR Verified\nManual",  "default": "Manual",     "in_list_view": 1 },
  { "fieldname": "hfr_last_synced",       "fieldtype": "Datetime", "label": "Last Synced",           "read_only": 1 }
]
```

---

## Phase 1 — Child DocTypes + Migration

### Story `hfr-c1a` — CRM Org Facility DocType
**Estimate:** S

Create `crm/fcrm/doctype/crm_org_facility/`:
- `__init__.py` (empty)
- `crm_org_facility.json` — child DocType, `istable: 1`, parent `CRM Organization`,
  `parentfield: facilities`. Fields from canonical schema above.
- `crm_org_facility.py` — stub controller (`pass`).

`bench migrate` after creation.

**Proof:** `bench execute frappe.db.sql` showing `tabCRM Org Facility` exists with correct columns.

---

### Story `hfr-c1b` — CRM Lead Facility DocType
**Estimate:** S

Same structure as C1a. Parent = `CRM Lead`, parentfield = `facilities`.

Create `crm/fcrm/doctype/crm_lead_facility/`.

`bench migrate`.

**Proof:** `SHOW TABLES LIKE 'tabCRM Lead Facility'` returns one row.

---

### Story `hfr-c1c` — CRM Deal Facility DocType
**Estimate:** S

Same structure. Parent = `CRM Deal`, parentfield = `facilities`.

Create `crm/fcrm/doctype/crm_deal_facility/`.

`bench migrate`.

**Proof:** `SHOW TABLES LIKE 'tabCRM Deal Facility'` returns one row.

---

### Story `hfr-c1d` — Migration Patch: flat columns → child rows
**Estimate:** M

**This story must run before C1e (column removal).**

Create `crm/patches/v1_0/hfr_cardinality_migration.py`:

```python
import frappe


# Flat HFR columns that existed on CRM Organization (v1.1)
_ORG_HFR_COLUMNS = [
    "hfr_facility_id", "mfl_code", "facility_type", "facility_category",
    "facility_level", "facility_owner", "facility_owner_type", "regulatory_body",
    "registration_number", "board_registration_number", "operational_status",
    "kra_pin", "hfr_county", "hfr_sub_county", "hfr_constituency", "hfr_ward",
    "latitude", "longitude", "license_number", "license_type", "license_expiry",
    "facility_standing", "open_whole_day", "open_weekends", "open_public_holidays",
    "open_late_night", "number_of_beds", "number_of_cots",
    "hfr_sync_status", "hfr_last_synced",
]

# Flat HFR columns that existed on CRM Lead (v1.1)
_LEAD_HFR_COLUMNS = [
    "hfr_facility_id", "mfl_code", "facility_level",
    "facility_owner_type", "hfr_sync_status",
]


def execute():
    _migrate_org_facilities()
    _migrate_lead_facilities()


def _migrate_org_facilities():
    # Guard: skip if column no longer exists (patch already ran + columns dropped)
    if not frappe.db.has_column("CRM Organization", "hfr_facility_id"):
        return

    orgs = frappe.db.sql(
        "SELECT name, hfr_facility_id, mfl_code, facility_type, facility_category,"
        " facility_level, facility_owner, facility_owner_type, regulatory_body,"
        " registration_number, operational_status, hfr_county, hfr_sub_county,"
        " hfr_ward, latitude, longitude, license_number, license_expiry,"
        " facility_standing, number_of_beds, hfr_sync_status, hfr_last_synced"
        " FROM `tabCRM Organization`"
        " WHERE hfr_facility_id IS NOT NULL AND hfr_facility_id != ''",
        as_dict=True,
    )
    for org in orgs:
        # Idempotency: skip if a child row with this FID already exists
        if frappe.db.exists(
            "CRM Org Facility",
            {"parent": org.name, "hfr_facility_id": org.hfr_facility_id},
        ):
            continue
        row = frappe.get_doc({
            "doctype": "CRM Org Facility",
            "parent": org.name,
            "parenttype": "CRM Organization",
            "parentfield": "facilities",
            "hfr_facility_id": org.hfr_facility_id,
            "facility_name": org.name,   # best available at migration time
            "mfl_code": org.mfl_code,
            "facility_type": org.facility_type,
            "facility_category": org.facility_category,
            "facility_level": org.facility_level,
            "facility_owner": org.facility_owner,
            "facility_owner_type": org.facility_owner_type,
            "regulatory_body": org.regulatory_body,
            "registration_number": org.registration_number,
            "operational_status": org.operational_status,
            "hfr_county": org.hfr_county,
            "hfr_sub_county": org.hfr_sub_county,
            "hfr_ward": org.hfr_ward,
            "latitude": org.latitude,
            "longitude": org.longitude,
            "license_number": org.license_number,
            "license_expiry": org.license_expiry,
            "facility_standing": org.facility_standing,
            "number_of_beds": org.number_of_beds,
            "hfr_sync_status": org.hfr_sync_status or "HFR Verified",
            "hfr_last_synced": org.hfr_last_synced,
        })
        row.insert(ignore_permissions=True)  # SYSTEM-INTERNAL

    frappe.db.commit()


def _migrate_lead_facilities():
    if not frappe.db.has_column("CRM Lead", "hfr_facility_id"):
        return

    leads = frappe.db.sql(
        "SELECT name, hfr_facility_id, mfl_code, facility_level,"
        " facility_owner_type, hfr_sync_status"
        " FROM `tabCRM Lead`"
        " WHERE hfr_facility_id IS NOT NULL AND hfr_facility_id != ''",
        as_dict=True,
    )
    for lead in leads:
        if frappe.db.exists(
            "CRM Lead Facility",
            {"parent": lead.name, "hfr_facility_id": lead.hfr_facility_id},
        ):
            continue
        row = frappe.get_doc({
            "doctype": "CRM Lead Facility",
            "parent": lead.name,
            "parenttype": "CRM Lead",
            "parentfield": "facilities",
            "hfr_facility_id": lead.hfr_facility_id,
            "facility_name": lead.hfr_facility_id,  # only FID available on lead
            "mfl_code": lead.mfl_code,
            "facility_level": lead.facility_level,
            "facility_owner_type": lead.facility_owner_type,
            "hfr_sync_status": lead.hfr_sync_status or "HFR Verified",
        })
        row.insert(ignore_permissions=True)  # SYSTEM-INTERNAL

    frappe.db.commit()
```

Append to `crm/patches.txt` **before** the line that would drop the columns (i.e., before the DocType JSON changes are applied — in practice, add it as the last line since `bench migrate` runs patches before syncing DocType fields):

```
crm.patches.v1_0.hfr_cardinality_migration
```

**Proof:** After `bench migrate`, run:
```python
frappe.db.count("CRM Org Facility")   # must be ≥ 1
frappe.db.count("CRM Lead Facility")  # must be ≥ 0
```

---

### Story `hfr-c1e` — Update parent DocType JSONs: remove flat cols, add table fields
**Estimate:** S

**Run AFTER C1d is verified.**

**`crm_organization.json`:**
- Remove all entries from `fields` and `field_order` for the 30 flat HFR column fieldnames listed in `_ORG_HFR_COLUMNS` above.
- Add to `fields`:
  ```json
  { "fieldname": "facilities_section", "fieldtype": "Section Break", "label": "Facilities" },
  { "fieldname": "facilities", "fieldtype": "Table", "label": "Facilities",
    "options": "CRM Org Facility" }
  ```
- Add `"facilities_section"` and `"facilities"` to `field_order` (at the end, after the Social section).

**`crm_lead.json`:**
- Remove `hfr_tab`, `hfr_facility_id`, `mfl_code`, `facility_level`, `facility_owner_type`, `hfr_sync_status` from `fields` and `field_order`.
- Add:
  ```json
  { "fieldname": "facilities_tab", "fieldtype": "Tab Break", "label": "Facilities" },
  { "fieldname": "facilities", "fieldtype": "Table", "label": "Facilities",
    "options": "CRM Lead Facility" }
  ```

**`crm_deal.json`:**
- Add only (no removals):
  ```json
  { "fieldname": "facilities_tab", "fieldtype": "Tab Break", "label": "Facilities" },
  { "fieldname": "facilities", "fieldtype": "Table", "label": "Facilities",
    "options": "CRM Deal Facility" }
  ```

`bench migrate` — this drops the flat columns from DB and creates the table fields.

**Proof:** `SHOW COLUMNS FROM \`tabCRM Organization\` LIKE 'hfr%'` returns empty.

---

## Phase 2 — Python Backend

### Story `hfr-c2b` — crm_lead.py: create_organization() + create_deal() refactor
**Estimate:** M

**`crm/fcrm/doctype/crm_lead/crm_lead.py`** — full rewrite of HFR-related helpers:

1. **Remove** `_HFR_LEAD_FIELDS`, `_copy_hfr_fields_to_org()` (no longer needed).

2. **Rewrite `create_organization()`** — replace the `_HFR_LEAD_FIELDS` loop with child row copy:

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
        _copy_facilities_to_org(self, existing_organization)
        return existing_organization

    organization = frappe.new_doc("CRM Organization")
    organization.update({
        "organization_name": self.organization,
        "website": self.website,
        "territory": self.territory,
        "industry": self.industry,
        "annual_revenue": self.annual_revenue,
    })
    for row in (self.facilities or []):
        organization.append("facilities", {
            "hfr_facility_id": row.hfr_facility_id,
            "facility_name": row.facility_name,
            "mfl_code": row.mfl_code,
            "facility_type": row.facility_type,
            "facility_category": row.facility_category,
            "facility_level": row.facility_level,
            "facility_owner": row.facility_owner,
            "facility_owner_type": row.facility_owner_type,
            "regulatory_body": row.regulatory_body,
            "registration_number": row.registration_number,
            "operational_status": row.operational_status,
            "hfr_county": row.hfr_county,
            "hfr_sub_county": row.hfr_sub_county,
            "hfr_ward": row.hfr_ward,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "license_number": row.license_number,
            "license_expiry": row.license_expiry,
            "facility_standing": row.facility_standing,
            "number_of_beds": row.number_of_beds,
            "hfr_sync_status": row.hfr_sync_status,
            "hfr_last_synced": row.hfr_last_synced,
        })
    organization.insert(ignore_permissions=True)  # SYSTEM-INTERNAL
    return organization.name
```

3. **Extend `create_deal()`** — after `new_deal.insert()`, copy facility rows:

```python
# After new_deal.insert() — copy facility rows from lead to deal
for row in (self.facilities or []):
    frappe.get_doc({
        "doctype": "CRM Deal Facility",
        "parent": new_deal.name,
        "parenttype": "CRM Deal",
        "parentfield": "facilities",
        "hfr_facility_id": row.hfr_facility_id,
        "facility_name": row.facility_name,
        "mfl_code": row.mfl_code,
        "facility_type": row.facility_type,
        "facility_category": row.facility_category,
        "facility_level": row.facility_level,
        "facility_owner": row.facility_owner,
        "facility_owner_type": row.facility_owner_type,
        "regulatory_body": row.regulatory_body,
        "registration_number": row.registration_number,
        "operational_status": row.operational_status,
        "hfr_county": row.hfr_county,
        "hfr_sub_county": row.hfr_sub_county,
        "hfr_ward": row.hfr_ward,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "license_number": row.license_number,
        "license_expiry": row.license_expiry,
        "facility_standing": row.facility_standing,
        "number_of_beds": row.number_of_beds,
        "hfr_sync_status": row.hfr_sync_status,
        "hfr_last_synced": row.hfr_last_synced,
    }).insert(ignore_permissions=True)  # SYSTEM-INTERNAL
```

4. **Add** module-level helper `_copy_facilities_to_org()`:

```python
def _copy_facilities_to_org(lead, org_name):
    """Fill-empty by FID: copy lead facility rows to an existing org, skip duplicates."""
    org = frappe.get_doc("CRM Organization", org_name)
    existing_fids = {r.hfr_facility_id for r in (org.facilities or [])}
    dirty = False
    for row in (lead.facilities or []):
        if row.hfr_facility_id in existing_fids:
            continue
        org.append("facilities", {
            "hfr_facility_id": row.hfr_facility_id,
            "facility_name": row.facility_name,
            "mfl_code": row.mfl_code,
            "facility_level": row.facility_level,
            "facility_owner_type": row.facility_owner_type,
            "hfr_county": row.hfr_county,
            "hfr_sync_status": row.hfr_sync_status,
        })
        dirty = True
    if dirty:
        org.save(ignore_permissions=True)  # SYSTEM-INTERNAL
```

`bench restart` after changes.

**Proof:** bench console — create a lead with 2 facility rows, call `convert_to_deal`, verify:
- `frappe.get_doc("CRM Deal", deal_name).facilities` has 2 rows
- `frappe.get_doc("CRM Organization", org_name).facilities` has 2 rows

---

### Story `hfr-c2c` — hfr.py: resync_facility_row(), remove resync_organization()
**Estimate:** S

**`crm/api/hfr.py`** changes:

1. **Remove** `resync_organization()` entirely.

2. **Add** `resync_facility_row()`:

```python
@frappe.whitelist()
def resync_facility_row(doctype, docname, row_name):
    """Fetch latest HFR data for a facility row and overwrite all HFR-managed fields."""
    allowed = ("CRM Organization", "CRM Lead", "CRM Deal")
    if doctype not in allowed:
        frappe.throw(_("Invalid doctype."))

    parent = frappe.get_doc(doctype, docname)
    row = next((r for r in parent.facilities if r.name == row_name), None)
    if not row:
        frappe.throw(_("Facility row not found."))
    if not row.hfr_facility_id:
        frappe.throw(_("This facility row has no HFR Facility ID."))

    hfr_data = get_facility_detail(row.hfr_facility_id)

    field_map = {
        "facility_name": "organization_name",
        "mfl_code": "mfl_code",
        "facility_type": "facility_type",
        "facility_category": "facility_category",
        "facility_level": "facility_level",
        "facility_owner": "facility_owner",
        "facility_owner_type": "facility_owner_type",
        "regulatory_body": "regulatory_body",
        "registration_number": "registration_number",
        "operational_status": "operational_status",
        "hfr_county": "hfr_county",
        "hfr_sub_county": "hfr_sub_county",
        "hfr_ward": "hfr_ward",
        "latitude": "latitude",
        "longitude": "longitude",
        "license_number": "license_number",
        "license_expiry": "license_expiry",
        "facility_standing": "facility_standing",
        "number_of_beds": "number_of_beds",
    }
    for row_field, data_field in field_map.items():
        val = hfr_data.get(data_field)
        if val is not None:
            row.set(row_field, val)

    row.hfr_sync_status = "HFR Verified"
    row.hfr_last_synced = frappe.utils.now_datetime()
    parent.save()

    return {"updated_row": row_name, "hfr_facility_id": row.hfr_facility_id}
```

`bench restart`.

**Proof:** bench console — call `resync_facility_row("CRM Organization", org_name, row_name)` on an existing child row, verify `hfr_last_synced` is updated.

---

## Phase 3 — Frontend: Modals

### Story `hfr-c3a` — HfrSearchPanel.vue: append-row semantics + pending list
**Estimate:** M

**Complete rewrite of `frontend/src/components/HfrSearchPanel.vue`.**

Key behavioural changes from v1.1:
- On "Use this", call `get_facility_detail(fid)` and **append to `props.doc.facilities`** (not `applyHfrPreview`).
- Show a **pending list** of already-added facilities below the input (name + MFL + county + × to remove).
- The single-facility "verified chip" is removed.
- FID dedup: if FID already in `props.doc.facilities`, show toast "Already added" and skip.
- New prop: `childDoctype` (String, required) — `"CRM Org Facility"` or `"CRM Lead Facility"`.

New component interface:
```
Props:
  doc           Object  required  — the reactive parent doc (org.doc or lead.doc)
  childDoctype  String  required  — "CRM Org Facility" | "CRM Lead Facility"

Emits:
  row-added     (rowData)  — after a facility is appended
  row-removed   (fid)      — after a pending row is removed
```

Pending list template (below the search input):
```html
<div v-if="pendingRows.length" class="mt-2 flex flex-col gap-1">
  <div class="text-p-xs-medium text-ink-gray-5 uppercase tracking-wider">
    {{ __('Added ({0})', [pendingRows.length]) }}
  </div>
  <div
    v-for="row in pendingRows"
    :key="row.hfr_facility_id"
    class="flex items-center gap-2 rounded-lg border border-outline-gray-2
           bg-surface-white dark:bg-surface-gray-2 px-3 py-2"
  >
    <div class="flex flex-col flex-1 min-w-0 gap-0.5">
      <span class="text-p-sm-medium text-ink-gray-8 truncate">{{ row.facility_name }}</span>
      <span class="text-p-xs text-ink-gray-5">
        <span v-if="row.mfl_code">MFL {{ row.mfl_code }} · </span>
        {{ row.hfr_county }}
        <span v-if="row.facility_owner_type"> · {{ row.facility_owner_type }}</span>
      </span>
    </div>
    <span class="shrink-0 text-p-xs bg-green-100 dark:bg-green-900 text-green-700
                  dark:text-green-300 rounded px-1.5 py-0.5">
      {{ __('Verified') }}
    </span>
    <button
      class="shrink-0 text-ink-gray-4 hover:text-red-500 transition-colors"
      @click="removeRow(row.hfr_facility_id)"
    >
      <svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor"
           stroke-width="1.5"><path d="M4 4l8 8M12 4l-8 8"/></svg>
    </button>
  </div>
</div>
```

`pendingRows` computed:
```js
const pendingRows = computed(() =>
  (props.doc.facilities || []).filter(r => !r.name)  // unsaved rows have no `name`
)
```

On `removeRow(fid)`:
```js
function removeRow(fid) {
  props.doc.facilities = (props.doc.facilities || []).filter(
    r => r.hfr_facility_id !== fid
  )
  emit('row-removed', fid)
}
```

On `select(r)` (clicking a result card):
```js
function select(r) {
  const existing = (props.doc.facilities || []).find(
    row => row.hfr_facility_id === r.fid
  )
  if (existing) {
    toast.warning(__('This facility is already in the list.'))
    return
  }
  fetchingDetail.value = true
  detailResource.submit({ fid: r.fid }, {
    onSuccess(data) {
      if (!props.doc.facilities) props.doc.facilities = []
      props.doc.facilities.push({
        doctype: props.childDoctype,
        hfr_facility_id: data.hfr_facility_id,
        facility_name: data.organization_name,
        mfl_code: data.mfl_code,
        facility_type: data.facility_type,
        facility_category: data.facility_category,
        facility_level: data.facility_level,
        facility_owner: data.facility_owner,
        facility_owner_type: data.facility_owner_type,
        regulatory_body: data.regulatory_body,
        registration_number: data.registration_number,
        operational_status: data.operational_status,
        hfr_county: data.hfr_county,
        hfr_sub_county: data.hfr_sub_county,
        hfr_ward: data.hfr_ward,
        latitude: data.latitude,
        longitude: data.longitude,
        license_number: data.license_number,
        license_expiry: data.license_expiry,
        facility_standing: data.facility_standing,
        number_of_beds: data.number_of_beds,
        hfr_sync_status: 'HFR Verified',
      })
      emit('row-added', data)
      fetchingDetail.value = false
    },
    onError() { fetchingDetail.value = false },
  })
}
```

**Proof:** screenshot of the modal after adding 2 facilities — pending list shows both rows with × buttons.

---

### Story `hfr-c3b` — OrganizationModal.vue: wire childDoctype
**Estimate:** XS

Single change: pass `childDoctype` prop to `<HfrSearchPanel>`:

```html
<HfrSearchPanel
  :doc="organization.doc"
  childDoctype="CRM Org Facility"
  class="mb-4"
  @row-added="onHfrFilled"
/>
```

`onHfrFilled` stub can remain as-is. No other changes needed.

**Proof:** `organization.doc.facilities` contains the appended row after clicking "Use".

---

### Story `hfr-c3c` — LeadModal.vue: wire childDoctype
**Estimate:** XS

Same as C3b:

```html
<HfrSearchPanel
  :doc="lead.doc"
  childDoctype="CRM Lead Facility"
  class="mb-4"
/>
```

**Proof:** screenshot of Create Lead modal with 2 facilities in the pending list.

---

## Phase 4 — Frontend: Detail Pages

### Story `hfr-c4a` — Organization.vue: Facilities tab
**Estimate:** M

Replace the current "Registry" tab (flat field display) with a "Facilities" tab that
shows and manages the `CRM Org Facility` child table.

The tab panel renders:

```
┌── Facilities (3) ──────────────────────────────────────────────┐
│ [+ Add Facility]                                               │
│                                                                │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ NATIONAL SPINAL INJURY REFERRAL HOSPITAL                 │  │
│ │ MFL 114746 · Level 5 · NAIROBI · GOK   [HFR Verified]   │  │
│ │ Last synced: 2026-08-02 10:30          [Re-sync] [×]    │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ KENYATTA NATIONAL HOSPITAL PRIME CARE CENTRE             │  │
│ │ MFL GK-024372 · NAIROBI · GOK          [HFR Verified]   │  │
│ │ Last synced: 2026-08-02 10:31          [Re-sync] [×]    │  │
│ └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Additions to `Organization.vue` script:**
```js
const resyncingRow = ref(null)

const resyncRowResource = createResource({
  url: 'crm.api.hfr.resync_facility_row',
  onSuccess() {
    resyncingRow.value = null
    organization.reload()
    toast.success(__('Facility re-synced'))
  },
  onError(err) {
    resyncingRow.value = null
    toast.error((err && err.messages && err.messages[0]) || __('Re-sync failed'))
  },
})

function resyncRow(rowName) {
  resyncingRow.value = rowName
  resyncRowResource.submit({
    doctype: 'CRM Organization',
    docname: props.organizationId,
    row_name: rowName,
  })
}

function removeRow(rowName) {
  organization.doc.facilities = organization.doc.facilities.filter(
    r => r.name !== rowName
  )
  organization.save.submit()
}
```

The "Add Facility" button shows `<HfrSearchPanel>` inline (toggle with a `ref`),
passing `:doc="organization.doc" childDoctype="CRM Org Facility"`. On `@row-added`,
call `organization.save.submit()`.

**Remove** the old flat `hfrIdentityRows`, `hfrLocationRows`, `hfrLicensingRows`,
`hfrOperationsRows` arrays and the "Re-sync" dialog and `showResyncDialog` ref.

**Remove** the `resyncResource` and `resync()` function.

Update `tabs` computed: change `'Registry'` label to `'Facilities'`.

**Proof:** screenshot of Facilities tab showing at least one migrated row with Re-sync button.

---

### Story `hfr-c4b` — Lead.vue: Facilities section
**Estimate:** S

`Lead.vue` currently has no facility display. Add a "Facilities" section to the side
panel (follow the existing `sections.data` pattern — or add as a standalone section
below the `SidePanelLayout` if the section system doesn't support child tables easily).

Simplest approach: add a dedicated `<div>` block in the right panel, visible when
`hfrEnabled && lead.doc.facilities?.length`:

```html
<div v-if="hfrEnabled" class="border-t px-4 py-3">
  <div class="text-p-xs-medium uppercase tracking-wider text-ink-gray-4 mb-2">
    {{ __('Facilities') }}
  </div>
  <div v-if="!lead.doc.facilities?.length" class="text-p-sm text-ink-gray-4">
    {{ __('No facilities linked') }}
  </div>
  <div v-else class="flex flex-col gap-1.5">
    <div
      v-for="row in lead.doc.facilities"
      :key="row.name"
      class="rounded-lg border border-outline-gray-2 bg-surface-white
             dark:bg-surface-gray-2 px-3 py-2 flex items-start gap-2"
    >
      <div class="flex flex-col flex-1 min-w-0 gap-0.5">
        <span class="text-p-sm-medium text-ink-gray-8 truncate">
          {{ row.facility_name }}
        </span>
        <span class="text-p-xs text-ink-gray-5">
          <span v-if="row.mfl_code">MFL {{ row.mfl_code }} · </span>
          {{ row.hfr_county }}
        </span>
      </div>
      <span
        v-if="row.hfr_sync_status === 'HFR Verified'"
        class="shrink-0 text-p-xs bg-green-100 dark:bg-green-900
               text-green-700 dark:text-green-300 rounded px-1.5 py-0.5"
      >{{ __('Verified') }}</span>
    </div>
  </div>
</div>
```

No Re-sync on the Lead detail page (Lead facilities are read-only once the Lead is saved — re-sync happens on the Org).

**Proof:** screenshot of Lead detail page showing the Facilities section with the rows created during Lead save.

---

### Story `hfr-c4c` — Deal.vue: Facilities section
**Estimate:** S

Identical to `hfr-c4b` but for `Deal.vue`. Add the same Facilities section using
`deal.doc.facilities` and `"CRM Deal Facility"` rows.

Deal facilities DO support Re-sync (deals are long-lived; facility data may change
over the deal lifecycle). Add per-row Re-sync button calling `resync_facility_row`
with `doctype = "CRM Deal"`.

**Proof:** screenshot of Deal detail page after `convert_to_deal` showing facilities copied from the Lead.

---

## Phase 5 — QA

### Story `hfr-c5-qa-refactor`
**Estimate:** S

**TC-1 — Migration: existing data preserved**
1. Check that the org "NATIONAL SPINAL INJURY REFERRAL HOSPITAL" (created during live testing) now has a `CRM Org Facility` child row with FID `FID-00-114746-3`.
2. Verify the flat `hfr_facility_id` column is gone from `tabCRM Organization`.

**TC-2 — Create Organisation with 2 facilities**
1. Open New Organisation modal.
2. Search HFR and add 2 facilities (e.g. FID-00-114746-3 and AM-FID-47-108521-3).
3. Verify both appear in the pending list.
4. Click Create. Open the new Org.
5. Go to Facilities tab — both rows present with Verified badge.

**TC-3 — Create Lead with facilities → Organisation auto-created**
1. Open Create Lead. Add 2 facilities via HFR panel.
2. Enter an Organisation name that doesn't exist.
3. Click Create.
4. Verify Lead has 2 `CRM Lead Facility` rows.
5. Verify a `CRM Organization` was auto-created with 2 `CRM Org Facility` rows.

**TC-4 — Convert Lead to Deal: facilities copied**
1. Take the Lead from TC-3. Convert to Deal.
2. Open the new Deal. Verify Facilities section shows the same 2 facilities.
3. `frappe.db.count("CRM Deal Facility", {"parent": deal_name})` = 2.

**TC-5 — Re-sync a facility row on Organisation**
1. Open an Org with a Verified facility row.
2. Click Re-sync on one row.
3. Verify `hfr_last_synced` updated (compare before/after timestamp).
4. Verify `hfr_sync_status` = "HFR Verified".

**TC-6 — Duplicate FID prevention**
1. Open New Organisation modal.
2. Search and add a facility.
3. Search the same FID again, click Use.
4. Verify toast "Already added" appears and the pending list still has only 1 row.

**Proof:** screenshots for TC-2 (pending list + Facilities tab), TC-3 (Lead + auto-created Org), TC-4 (Deal Facilities), TC-5 (updated timestamp).

---

## Sprint Status (already in sprint-status.yaml)

```yaml
epic-hfr-refactor: ready-for-dev

hfr-c1a-crm-org-facility-doctype: ready-for-dev
hfr-c1b-crm-lead-facility-doctype: ready-for-dev
hfr-c1c-crm-deal-facility-doctype: ready-for-dev
hfr-c1d-migration-patch: ready-for-dev
hfr-c1e-parent-doctype-updates: ready-for-dev
hfr-c2b-lead-py-refactor: ready-for-dev
hfr-c2c-api-resync-row: ready-for-dev
hfr-c2d-convert-to-deal: ready-for-dev     # covered in c2b story
hfr-c3a-search-panel-append: ready-for-dev
hfr-c3b-org-modal-facilities: ready-for-dev
hfr-c3c-lead-modal-facilities: ready-for-dev
hfr-c4a-org-facilities-tab: ready-for-dev
hfr-c4b-lead-facilities-section: ready-for-dev
hfr-c4c-deal-facilities-section: ready-for-dev
hfr-c5-qa-refactor: ready-for-dev
```

## Dependency Order (strict)

```
C1a + C1b + C1c (parallel) → C1d → C1e
C1e → C2b + C2c (parallel)
C2b + C2c → C3a → C3b + C3c (parallel)
C3b + C3c + C3a → C4a + C4b + C4c (parallel)
All above → C5
```
