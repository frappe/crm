# Architecture Decision Records — HFR Cardinality Refactor
**Date:** 2026-08-02
**Author:** Salim
**BRD:** `hfr-cardinality-refactor-brd.md`

---

## ADR-C01 — Three child DocTypes, not one shared DocType

**Status:** Accepted

### Context
The HFR facility row (FID, MFL code, name, type, level, county, coordinates, licensing,
operations, sync metadata) needs to be stored as a child of three different parents:
`CRM Organization`, `CRM Lead`, and `CRM Deal`.

Options:
- (A) One shared child DocType (e.g. `CRM HFR Facility Link`) with a dynamic parent
  reference field — polymorphic parent.
- (B) Three separate child DocTypes (`CRM Org Facility`, `CRM Lead Facility`,
  `CRM Deal Facility`), each with the same field set.
- (C) One child DocType with a `parenttype` discrimination column (Frappe's native
  child table mechanism already does this).

### Decision
**Option C — Frappe native child tables, three DocType names.**

Frappe's child table mechanism already stores `parent`, `parenttype`, and `parentfield`
on every child row. Three separate DocType names (`CRM Org Facility`, `CRM Lead Facility`,
`CRM Deal Facility`) are the idiomatic Frappe pattern, even though the field schema is
identical. This is how all child tables in Frappe work — `Sales Order Item` and
`Purchase Order Item` are separate DocTypes with nearly identical fields.

Rationale:
- Separate DocType names mean separate DB tables, making it impossible to accidentally
  join facility rows from an Org with rows from a Lead.
- Each DocType has its own permissions, which is important: a Sales User can see
  `CRM Lead Facility` rows but may not have access to the full `CRM Org Facility`
  list.
- Field evolution is independent — we may add Deal-specific fields later (e.g.
  `contracted_services`) without polluting the Org table.

Option A (polymorphic parent) is not idiomatic Frappe and creates join complexity.
Option B is identical to C in practice — "B" and "C" are the same thing in Frappe.

### Field schema for all three DocTypes

```
hfr_facility_id      Data       "HFR Facility ID"   (unique within parent)
facility_name        Data       "Facility Name"
mfl_code             Data       "MFL Code"
facility_type        Data       "Facility Type"
facility_category    Data       "Category"
facility_level       Data       "Facility Level"
facility_owner       Data       "Facility Owner"
facility_owner_type  Data       "Owner Type"
regulatory_body      Data       "Regulatory Body"
registration_number  Data       "Registration Number"
operational_status   Data       "Operational Status"
hfr_county           Data       "County"
hfr_sub_county       Data       "Sub-County"
hfr_ward             Data       "Ward"
latitude             Float      "Latitude"
longitude            Float      "Longitude"
license_number       Data       "License Number"
license_expiry       Data       "License Expiry"
facility_standing    Data       "Standing"
number_of_beds       Int        "Number of Beds"
hfr_sync_status      Select     "Sync Status"   options: \nHFR Verified\nManual
hfr_last_synced      Datetime   "Last Synced"   read_only: 1
```

Non-essential fields from v1.1 (board_registration_number, kra_pin, constituency,
open_whole_day, open_weekends, open_public_holidays, open_late_night, number_of_cots)
are retained for completeness but hidden in the default list view.

### Consequences
- Three JSON files to create and maintain.
- Field changes require updating three files. Mitigated by creating a shared fixture
  generator or documenting the canonical list here.
- DB: three new tables (`tabCRM Org Facility`, `tabCRM Lead Facility`,
  `tabCRM Deal Facility`). Small row counts per parent — no performance concern.

---

## ADR-C02 — `hfr_sync_status` / `hfr_last_synced` at row level only (OQ-1 resolved 2026-08-02)

**Status:** Accepted

### Decision
**Row-level only.** `hfr_sync_status` and `hfr_last_synced` live exclusively on each
facility child row. `CRM Organization` carries no `hfr_sync_status` or
`hfr_last_synced` header columns. The flat columns added in v1.1 are removed as part
of the migration patch.

### Consequences
- `CRM Organization.validate()` needs no roll-up logic.
- The Org JSON retains neither `hfr_sync_status` nor `hfr_last_synced`.
- The migration patch drops these two columns from `tabCRM Organization` along with
  the other 26 flat HFR columns.
- Organisation list view / Kanban cannot filter by HFR sync status at the org level.
  If that becomes a need, it can be added later as a derived field.

---

## ADR-C03 — Migration strategy: create child rows before dropping columns

**Status:** Accepted

### Context
The v1.1 release added 28 flat HFR columns to `tabCRM Organization` and 5 to
`tabCRM Lead`. The refactor removes them. At least one live record exists with real
HFR data (the NATIONAL SPINAL INJURY REFERRAL HOSPITAL created during live testing).

### Decision
Two-phase migration patch:

**Phase 1 (in the migration patch, runs via `bench migrate`):**
```python
# crm/patches/hfr_cardinality_migration.py
def execute():
    # 1. For each CRM Organization with hfr_facility_id set, create CRM Org Facility row
    # 2. For each CRM Lead with hfr_facility_id set, create CRM Lead Facility row
    # 3. frappe.db.commit()
    # Phase 2 column drops happen separately after validation
```

**Phase 2 (separate DDL, after data validation):**
```python
    frappe.db.sql("ALTER TABLE `tabCRM Organization` DROP COLUMN hfr_facility_id, ...")
    frappe.db.sql("ALTER TABLE `tabCRM Lead` DROP COLUMN hfr_facility_id, ...")
```

The patch is idempotent: skip rows where a child row with the same `hfr_facility_id`
already exists. The DocType JSON removes the fields — `bench migrate` will attempt
to drop the columns after running patches. The patch must run BEFORE column drop
(controlled by patch order in `patches.txt`).

### Consequences
- Patch must be registered in `crm/patches.txt` before the JSON column removals
  are applied.
- If patch fails mid-run, data is not lost (columns still exist).
- Column drop is irreversible — must be gated on patch success.

---

## ADR-C04 — `HfrSearchPanel.vue` append-row semantics (replaces fill-empty)

**Status:** Accepted

### Context
In v1.1, `HfrSearchPanel.vue` called `applyHfrPreview(doc, hfrFields)` which filled
flat fields on the parent doc using fill-empty semantics. This no longer applies since
there are no flat fields.

### Decision
On "Use this" click, `HfrSearchPanel.vue` appends a row to `props.doc.facilities`:

```js
function select(r) {
  // Dedup: skip if FID already in the table
  const existing = (props.doc.facilities || []).find(row => row.hfr_facility_id === r.fid)
  if (existing) {
    toast.warning(__('This facility is already in the list.'))
    return
  }
  fetchingDetail.value = true
  detailResource.submit({ fid: r.fid }, {
    onSuccess(data) {
      if (!props.doc.facilities) props.doc.facilities = []
      props.doc.facilities.push({
        doctype: props.childDoctype,  // 'CRM Org Facility' | 'CRM Lead Facility'
        ...data,
        facility_name: data.organization_name,
        hfr_sync_status: 'HFR Verified',
      })
      selectedRows.value.push(data.organization_name)
      fetchingDetail.value = false
      emit('filled', data)
    }
  })
}
```

`HfrSearchPanel` now accepts a new prop `childDoctype` so the parent modal can specify
which child table it is populating.

The "verified chip" state is replaced by a mini list of added facilities displayed
below the search input, each with an × to remove before Save. The chip was designed
for the single-facility assumption and no longer makes sense.

### Consequences
- `HfrSearchPanel.vue` prop interface changes: `doc` stays (needed to read existing
  rows for dedup), new `childDoctype` prop added.
- `applyHfrPreview()` export from `useHfrSearch.js` is no longer called by the panel
  (but remains exported for other potential consumers).
- `OrganizationModal.vue` and `LeadModal.vue` pass `:childDoctype` to the panel.

---

## ADR-C05 — Facilities displayed as an inline mini-table in modals, not a full child table editor

**Status:** Accepted

### Context
Frappe's standard child table editor (the grid with inline rows) is available but
requires the FieldLayout to be configured, and the Quick Entry layout doesn't include
child tables by default. Options:

- (A) Use the Frappe child table grid inside the modal (requires FieldLayout work).
- (B) Render a custom lightweight list inside the modal: each added facility shows as
  a row with name + MFL code + county + × button. No inline editing — facilities are
  read from HFR and not editable pre-Save.

### Decision
**Option B — custom lightweight list.**

Rationale:
- Agents are adding HFR-verified data, not typing free-form rows. The input surface
  is the search panel; the list is output/confirmation.
- The list only needs to show name, MFL, county, and a remove button — 3 lines of
  template, not a grid.
- Keeps the modal lean. The full table editor (with re-sync etc.) lives on the detail
  page, not the create modal.

Visual treatment:
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 MFL code, FID, or registration number...               [×]  │
│                                                                 │
│ Added facilities (2):                                           │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ NATIONAL SPINAL INJURY REFERRAL HOSPITAL    MFL 114746  × │   │
│ │ NAIROBI · GOVERNMENT OF KENYA                             │   │
│ ├──────────────────────────────────────────────────────────┤   │
│ │ KENYATTA NATIONAL HOSPITAL PRIME CARE CENTRE  MFL GK-… × │   │
│ │ NAIROBI · GOVERNMENT OF KENYA                             │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Consequences
- `HfrSearchPanel.vue` renders its own pending-rows list.
- The verified chip (single-facility design) is removed.
- `props.doc.facilities` array is the source of truth for pending rows — same array
  that `frappe.client.insert` will serialise when the modal saves.

---

## ADR-C06 — `convert_to_deal()` copies facility rows, not references

**Status:** Accepted

### Context
When a Lead converts to a Deal, the facilities associated with that lead should be
visible on the Deal. Options:

- (A) **Copy rows** — `CRM Deal Facility` rows are created from `CRM Lead Facility`
  rows. Independent after copy; changes on Deal don't affect Lead.
- (B) **Reference** — Deal stores a Link to the Lead and resolves facilities through
  the Lead's child table. No copy needed but adds a join.
- (C) **Shared parent** — one child table, parent = Lead, both Lead and Deal reference it.

### Decision
**Option A — copy rows.**

Rationale:
- Frappe's deal conversion is already a copy-based operation (Lead fields → Deal
  fields). Copy semantics are consistent.
- After conversion, the Deal's facility list may diverge from the Lead (agent adds
  or removes facilities as scope evolves). References would make that impossible.
- Option B adds a query join every time the Deal detail page loads.
- Simple, explicit, no hidden dependencies.

### Consequences
- `convert_to_deal()` extended: after creating the Deal doc, iterate
  `lead.facilities` and append equivalent rows to `deal.facilities`.
- Deleting a Lead post-conversion does not affect Deal facilities.

---

## ADR-C07 — User journey for the Lead creation flow

**Status:** Accepted

### The complete revised user journey

```
Sales Agent opens "Create Lead" modal
│
├── Fills in contact details (First Name, Email, etc.)
│
├── In the Facilities section:
│   ├── Types a facility identifier (MFL code / FID / reg. number)
│   ├── Auto-search fires after 600ms
│   ├── Clicks a result card → row appended to pending list
│   │   └── Repeat for each facility in scope
│   └── Can remove a pending row with ×
│
└── Clicks "Create"
    ├── CRM Lead inserted with facilities[] child rows
    │
    └── lead.create_organization():
        ├── If org exists by name → link it + copy facilities fill-empty by FID
        └── If new org → insert org with same facilities[] rows

Lead detail page:
└── Facilities tab shows all linked facility rows
    └── Per-row: Re-sync from HFR | Remove

Convert to Deal:
└── Deal created with facilities[] copied from Lead
    └── Deal Facilities tab: add / remove / re-sync
```

### Key UX rules
1. **No facility is required to create a Lead.** An agent can create a Lead with
   zero facilities (e.g. inbound enquiry before site details are known) and add
   facilities later from the detail page.
2. **The search panel is always visible** in the modal (not behind a toggle).
3. **Adding the same FID twice is silently prevented** with a toast, not an error.
4. **No free-text facility entry.** All facility rows must originate from an HFR
   search result. If HFR is unreachable, the section shows a disabled state with a
   message; the rest of the modal still works.

---

## ADR-C08 — Re-sync operates at the row level, not the parent level

**Status:** Accepted

### Context
v1.1 had `resync_organization(organization_name, mode)` which updated flat fields on
the Org. With the new model, each facility row has its own FID and should be
re-syncable independently.

### Decision
New API: `crm.api.hfr.resync_facility_row(doctype, docname, row_name)`.

- `doctype`: `CRM Organization` | `CRM Lead` | `CRM Deal`
- `docname`: the parent record name
- `row_name`: the child row's `name` field

Logic: fetch HFR detail for `row.hfr_facility_id`, overwrite all HFR-managed fields
on the specific row (always overwrite — this is an explicit sync action), update
`row.hfr_last_synced` and `row.hfr_sync_status = "HFR Verified"`, then save the parent to persist the updated row.

The old `resync_organization()` is removed (or kept as a deprecated shim that calls
`resync_facility_row` for the first row, for backward compatibility with any tooling).

Fill-empty vs overwrite choice (from v1.1 ADR-003 OQ-3) **no longer applies at the
row level** — row-level re-sync always overwrites HFR fields. The choice was only
meaningful when mixing manually-entered flat fields with HFR fields on the same record.
Since all fields in a facility row come from HFR, overwrite is always correct.

### Consequences
- One-step re-sync (no confirmation dialog needed per row).
- Header `hfr_sync_status` roll-up recomputed after each row re-sync.
- `Organization.vue`, `Lead.vue`, `Deal.vue` each call `resync_facility_row` with
  the appropriate `doctype`.

---

## Implementation Sequence

```
Phase 1 — New child DocTypes + migration
  C1a. Create CRM Org Facility JSON + py + __init__
  C1b. Create CRM Lead Facility JSON + py + __init__
  C1c. Create CRM Deal Facility JSON + py + __init__
  C1d. Write migration patch (crm/patches/hfr_cardinality_migration.py)
  C1e. Register patch in patches.txt BEFORE JSON column removals
  C1f. Update CRM Organization JSON: remove all 28 flat HFR columns, add facilities table
       (no header sync fields — row-level only)
  C1g. Update CRM Lead JSON: remove 5 flat HFR columns, add facilities table
  C1h. Update CRM Deal JSON: add facilities table
  C1i. bench migrate (patch runs, creates child rows, then columns dropped)
  C1j. Verify: child rows exist, flat columns gone, zero data loss

Phase 2 — Python backend
  # C2a removed — no validate() roll-up needed (OQ-1: row-level sync only)
  C2b. Update crm_lead.py: remove _HFR_LEAD_FIELDS, rewrite create_organization()
  C2c. Update crm/api/hfr.py: add resync_facility_row(), remove/shim resync_organization()
  C2d. Update convert_to_deal() to copy facility rows
  C2e. bench restart

Phase 3 — Frontend: modals
  C3a. Update HfrSearchPanel.vue: append-row semantics, pending list, childDoctype prop
  C3b. Update OrganizationModal.vue: pass childDoctype, show pending rows
  C3c. Update LeadModal.vue: same

Phase 4 — Frontend: detail pages
  C4a. Organization.vue: Facilities tab with child table list + per-row Re-sync/Remove
  C4b. Lead.vue: Facilities section
  C4c. Deal.vue: Facilities section

Phase 5 — QA
  C5a. Migration: verify existing NATIONAL SPINAL INJURY REFERRAL HOSPITAL Org has child row
  C5b. Create Lead with 2 facilities → verify both child rows
  C5c. Convert Lead to Deal → verify facilities copied
  C5d. Re-sync a facility row → verify fields updated, header roll-up recomputed
  C5e. Add facility to existing Org from detail page
  C5f. Duplicate FID prevention toast
```
