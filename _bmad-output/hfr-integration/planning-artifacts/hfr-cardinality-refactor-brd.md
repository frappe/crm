# BRD — HFR Cardinality Refactor: One Organisation → Many Facilities
**Version:** 1.0
**Date:** 2026-08-02
**Author:** Salim
**Status:** Draft
**Supersedes:** `hfr-integration-brd.md` §4 (Scope), §6 (FR-4, FR-5), §7 (US-01–03)
**Companion ADR:** `hfr-cardinality-refactor-adr.md`

**Changelog:**
- v1.0 — Initial refactor spec. Corrects the cardinality assumption from v1.1 BRD.

---

## 1. What Changed and Why

### The original assumption (now incorrect)
v1.1 BRD treated **Organisation : Facility = 1 : 1**. All HFR fields were stored as
flat columns directly on `CRM Organization` and `CRM Lead`. A single `hfr_facility_id`
column identified the one facility associated with each record.

### The real-world cardinality
A healthcare **organisation** (e.g. Aga Khan Health Services, Nairobi Women's
Hospital Group, a county health department) operates **multiple licensed facilities**.
A **Lead** represents a sales opportunity with that organisation — and that opportunity
may span one or many of their facilities (e.g. "supply our Nairobi and Mombasa
branches"). A **Deal** inherits the same reality.

Forcing a single FID onto Organisation/Lead loses this information: agents can only
record one facility per record, dropping the rest, or must create duplicate Org records
per facility — neither is acceptable.

### Correct model
```
CRM Organization  1 ── * CRM Org Facility          (child table)
CRM Lead          1 ── * CRM Lead Facility          (child table)
CRM Deal          1 ── * CRM Deal Facility          (child table, inherited/editable)
```

Each child row holds the full HFR profile of one facility.
The parent (Org/Lead/Deal) holds no per-facility HFR columns.

---

## 2. Goals

| # | Goal |
|---|------|
| G1 | An Organisation can have any number of linked HFR-verified facilities, each with its full registry profile. |
| G2 | A Lead captures all facilities in scope for the sales opportunity at creation time, not just one. |
| G3 | A Deal inherits the facilities from its originating Lead and allows agents to add/remove as the scope evolves. |
| G4 | The Sales Agent experience remains: search HFR → click result → row added to the table. Multiple searches allowed before saving. |
| G5 | All existing data (flat HFR columns already written) is migrated to the new child rows without loss. |
| G6 | HealthPro Ops can see all facility FIDs for a Lead/Deal in one view for downstream onboarding. |

---

## 3. Stakeholders

Same as v1.1 BRD. No change.

---

## 4. Scope

### 4.1 In Scope

**New DocType: `CRM Org Facility`**
- Child DocType of `CRM Organization`
- Holds the full HFR field set per facility (FID, MFL code, name, type, level,
  owner, county/sub-county, coordinates, licensing, operations, sync metadata)
- One row = one HFR-verified facility

**New DocType: `CRM Lead Facility`**
- Child DocType of `CRM Lead`
- Same HFR field set as `CRM Org Facility`
- Populated at Lead creation via the HfrSearchPanel (multiple calls allowed)

**New DocType: `CRM Deal Facility`**
- Child DocType of `CRM Deal`
- Copied from the originating Lead's facilities at `convert_to_deal` time
- Agents can add/remove facilities post-conversion

**Updated `CRM Organization`**
- Remove all 28 flat HFR columns added in v1.1
- Add `facilities` child table field (→ `CRM Org Facility`)
- Retain `hfr_sync_status` / `hfr_last_synced` at org level (represent the org's
  overall registry sync state — useful for bulk re-sync workflows)

**Updated `CRM Lead`**
- Remove 5 flat HFR columns added in v1.1
- Add `facilities` child table field (→ `CRM Lead Facility`)

**Updated `CRM Deal`**
- Add `facilities` child table field (→ `CRM Deal Facility`)
- No HFR flat columns ever existed on Deal — this is a net-new addition

**Data migration patch**
- Any `CRM Organization` record with a non-null `hfr_facility_id` gets one child row
  created in `CRM Org Facility` using the existing flat column values
- Same for `CRM Lead` records
- Flat columns then dropped via DDL

**Updated `HfrSearchPanel.vue`**
- Instead of calling `applyHfrPreview(doc, hfrFields)` to fill flat fields, it
  appends a row to `doc.facilities[]`
- Multiple facilities can be added before Save
- Each row in the table shows: facility name, MFL code, level, county, owner type,
  a sync-status badge, and a remove (×) button

**Updated `Organization.vue` — Facilities tab**
- Replaces the current "Registry" tab (which showed flat fields)
- Shows the `facilities` child table as a read-only list with per-row "Re-sync" and
  "Remove" actions
- "Add Facility" button opens the HfrSearchPanel inline

**Updated `Lead.vue` / `Deal.vue`**
- Facilities section added to the side panel or as a tab
- Shows linked facilities with per-row re-sync

**Updated `crm.api.hfr.resync_organization`**
- Now accepts `facility_row_name` (the child row name) instead of a flat org name
- Updates that specific child row from HFR
- Updates the row's `hfr_sync_status` and `hfr_last_synced`

**Updated `crm.fcrm.doctype.crm_lead.crm_lead.create_organization()`**
- When creating the linked Org from a Lead, copy all `lead.facilities` rows into
  `org.facilities` (fill-empty per FID — skip if FID already exists on org)

**Updated `convert_to_deal()`**
- Copy all `lead.facilities` rows into `deal.facilities`

### 4.2 Out of Scope

- Editing facility details from within CRM (HFR is authoritative — changes go
  through HealthPro ERP's facility update workflow)
- Bulk re-sync of all facilities across all orgs (scheduler job, post-MVP)
- Deduplication of the same facility across multiple Leads/Orgs (separate concern)
- Mobile views (after desktop stable)

---

## 5. User Stories

### US-01 — Add multiple facilities when creating an Organisation
> As a Sales Agent creating a new Organisation, I want to add all of the
> organisation's facilities from HFR so that the full scope is captured from day one.

**Acceptance Criteria:**
- The create-Org modal shows a Facilities section below the form fields.
- The HfrSearchPanel is embedded in that section; each "Use" click adds a row.
- After adding 3 facilities: the section shows 3 rows, each with name, MFL, county,
  and an × to remove.
- Clicking × removes the row before Save (no DB write yet).
- Clicking "Create" inserts the Org and all child facility rows in one transaction.

### US-02 — Add facilities when creating a Lead
> As a Sales Agent creating a new Lead, I want to specify which facilities are in
> scope for this opportunity so that the pipeline is accurate.

**Acceptance Criteria:**
- The Create Lead modal has a Facilities section with the same HfrSearchPanel.
- Multiple facilities can be added before clicking "Create".
- After Lead save, `CRM Lead Facility` child rows exist for all added facilities.
- Each facility row is visible on the Lead detail page.

### US-03 — Deal inherits Lead facilities
> As a Sales Agent converting a Lead to a Deal, I want the facilities already
> recorded on the Lead to carry across so I don't have to re-enter them.

**Acceptance Criteria:**
- After `convert_to_deal`, the Deal has the same `CRM Deal Facility` rows as the
  originating Lead's `CRM Lead Facility` rows.
- The agent can add or remove facilities on the Deal post-conversion.

### US-04 — View and manage facilities on an Organisation
> As a Sales Agent viewing an Organisation, I want to see all its HFR-verified
> facilities in one place and be able to add new ones or re-sync existing ones.

**Acceptance Criteria:**
- Organisation detail page has a "Facilities" tab.
- Each facility shows: name, MFL code, level, county, owner type, last synced.
- "Re-sync" on a row fetches the latest HFR data for that FID and updates the row.
- "Add Facility" opens the HfrSearchPanel inline to append another facility.
- A facility cannot appear twice in the same Org (dedup by FID on insert).

### US-05 — Data migration: existing flat columns preserved
> As a Sales Agent, I want existing Organisation and Lead records that already have
> HFR data (from the v1.1 flat columns) to be migrated to the new child rows without
> any data loss.

**Acceptance Criteria:**
- After the migration patch runs, every Organisation with a non-null `hfr_facility_id`
  has exactly one child row in `CRM Org Facility` with the same FID and all other
  HFR fields populated.
- Same for Leads.
- The flat HFR columns are removed post-migration.
- No manual intervention required.

---

## 6. Functional Requirements

| # | Requirement |
|---|-------------|
| FR-1 | New `CRM Org Facility` child DocType with full HFR field set (28 fields from v1.1 FR-4, now per-row not per-org). Parent = `CRM Organization`. |
| FR-2 | New `CRM Lead Facility` child DocType. Same fields as FR-1. Parent = `CRM Lead`. |
| FR-3 | New `CRM Deal Facility` child DocType. Same fields as FR-1. Parent = `CRM Deal`. |
| FR-4 | `CRM Organization` JSON: remove all 28 flat HFR columns (including `hfr_sync_status` / `hfr_last_synced`); add `facilities` Table field (→ `CRM Org Facility`). No per-org sync fields — sync state lives only on each facility row. |
| FR-5 | `CRM Lead` JSON: remove 5 flat HFR columns; add `facilities` Table field (→ `CRM Lead Facility`). |
| FR-6 | `CRM Deal` JSON: add `facilities` Table field (→ `CRM Deal Facility`). No removals needed. |
| FR-7 | Data migration patch: for each Org/Lead with non-null `hfr_facility_id`, create the corresponding child row. Run before column removal. |
| FR-8 | `HfrSearchPanel.vue`: on facility select, append a row to `props.doc.facilities` instead of applying flat fields. |
| FR-9 | `OrganizationModal.vue`: Facilities section shows the pending child table rows (add/remove before Save). |
| FR-10 | `LeadModal.vue`: same Facilities section. |
| FR-11 | `Organization.vue` Facilities tab: list of child rows, per-row Re-sync + Remove, Add Facility button. |
| FR-12 | `Lead.vue` / `Deal.vue`: Facilities section on the side panel. |
| FR-13 | `crm.api.hfr.resync_facility_row(doctype, docname, row_name)` — new whitelist method. Fetches HFR by FID, updates the named child row, updates `hfr_last_synced` / `hfr_sync_status`. |
| FR-14 | `crm_lead.create_organization()`: copy all `self.facilities` rows to the new/existing Org (fill-empty by FID). |
| FR-15 | `convert_to_deal()`: copy all Lead `facilities` rows to the new Deal. |
| FR-16 | FID deduplication on insert: if a facility with the same `hfr_facility_id` already exists in the parent's child table, skip (don't create a duplicate row). |

---

## 7. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-1 | Migration patch must be idempotent — safe to run multiple times. |
| NFR-2 | Zero data loss: migration must create child rows before dropping columns. |
| NFR-3 | `pnpm build` zero warnings after frontend changes. |
| NFR-4 | Dark/light mode parity on child table UI. |
| NFR-5 | Performance: child table rows loaded lazily on detail page (not blocking initial load). |

---

## 8. Open Questions

| # | Question | Owner | Resolution |
|---|----------|-------|-----------|
| OQ-1 | Should `hfr_sync_status` / `hfr_last_synced` remain on the Org header, or move purely to each facility row? | Salim | **Row-level only** (2026-08-02). No header sync columns on Org. |
| OQ-2 | When the same facility FID appears on multiple Organisations (e.g. a facility that changed ownership), should a warning be surfaced? | Salim | Open |

---

## 9. What Is NOT Changing

- `crm.api.hfr.search_facility` — no change (returns same list format)
- `crm.api.hfr.get_facility_detail` — no change (returns same field map)
- `crm.api.hfr.get_hfr_settings` / `update_hfr_settings` — no change
- `CRM HFR Settings` DocType — no change
- JWT generation, HIE credential storage — no change
- `HfrSearchPanel.vue` search/result/verified-chip UX — unchanged; only what happens
  on "Use" changes (append row vs fill flat fields)

---

## 10. Impact on Shipped v1.1 Code

The v1.1 implementation shipped the following that must be refactored:

| File | v1.1 state | Refactor action |
|------|-----------|-----------------|
| `crm_organization.json` | 28 flat HFR columns | Remove; add `facilities` Table field |
| `crm_lead.json` | 5 flat HFR columns | Remove; add `facilities` Table field |
| `crm_deal.json` | No HFR fields | Add `facilities` Table field |
| `crm_lead.py` | `_HFR_LEAD_FIELDS`, `_copy_hfr_fields_to_org`, `create_organization()` uses flat fields | Rewrite to copy child rows |
| `crm/api/hfr.py` | `resync_organization()` writes flat fields | Replace with `resync_facility_row()` |
| `HfrSearchPanel.vue` | Calls `applyHfrPreview()` → fills flat fields | Append to `doc.facilities[]` instead |
| `OrganizationModal.vue` | `onHfrFilled()` stub | Wire up child table display |
| `Organization.vue` | Flat field display in Registry tab | Replace with child table list |
| `Lead.vue` | No facility display yet | Add Facilities section |
| `Deal.vue` | No facility display yet | Add Facilities section |
| Flat HFR DB columns | Present on `tabCRM Organization`, `tabCRM Lead` | Drop after migration |
