# Custom Scripting — Future Phases

> **Pre-requisite context:** [custom-scripting.md](./custom-scripting.md) (implemented Phase 1), [meta-refactor.md](./meta-refactor.md) (architecture), [testing-strategy.md](./testing-strategy.md), [form-scripts.md](./form-scripts.md) (existing scripting API)

---

## Table of Contents

1. [Phase 2 — FieldLayout Dialog from Script](#phase-2--fieldlayout-dialog-from-script)
2. [Phase 3 — Decouple FieldLayout and Grid](#phase-3--decouple-fieldlayout-and-grid)
3. [Phase 4 — getMeta Single Source of Truth](#phase-4--getmeta-single-source-of-truth)
4. [Phase 5 — Scripting DX Rethink](#phase-5--scripting-dx-rethink)
5. [Phase 6 — More Capabilities](#phase-6--more-capabilities)
6. [Design Principles](#design-principles)

---

## Phase 2 — FieldLayout Dialog from Script

> **Priority: HIGH — next up**

### Goal

Allow script authors to open a dialog with a full FieldLayout inside it, collect data from the user, and use it in an action callback. This is the scripting equivalent of what `CreateDocumentModal` does, but fully controlled from a Form Script — no SFC needed.

### Why it matters

Many CRM workflows need intermediate data collection: "Convert to Deal" needs a pipeline + stage, "Mark as Lost" needs a reason, custom workflows need arbitrary fields. Currently these all require dedicated Vue SFC modals. A script-driven dialog unlocks these for customizers without code deployment.

### Proposed API

```js
class CRMLead {
  async mark_as_lost() {
    const { data, close } = await this.createFieldLayoutDialog({
      title: 'Mark Lead as Lost',
      doctype: 'CRM Lost Reason',       // fetch layout from this doctype
      size: 'xl',                        // optional, default 'xl'
      defaults: {                        // pre-fill fields
        lead: this.doc.name,
      },
      required: ['lost_reason'],         // extra mandatory fields (in addition to doctype reqd)
    })

    // `data` is the collected form values (plain object)
    // Only reached if user clicked the primary action
    this.doc.lost_reason = data.lost_reason
    this.doc.lost_notes = data.lost_notes
    close()
  }
}
```

Alternative — inline fields (no doctype needed):

```js
class CRMLead {
  async custom_action() {
    const { data, close } = await this.createFieldLayoutDialog({
      title: 'Enter Details',
      fields: [
        { fieldname: 'reason', fieldtype: 'Select', label: 'Reason', options: 'Price\nFeatures\nTiming', reqd: 1 },
        { fieldname: 'notes', fieldtype: 'Text', label: 'Notes' },
        { fieldname: 'followup_date', fieldtype: 'Date', label: 'Follow-up Date' },
      ],
      actions: [
        {
          label: 'Submit',
          variant: 'solid',
          // onClick receives { data, close }
        },
        {
          label: 'Cancel',
        },
      ],
    })

    if (data) {
      await call('crm.api.lead.mark_lost', { lead: this.doc.name, ...data })
      toast.success('Marked as lost')
    }
  }
}
```

### Key questions to decide

1. **Should it return a Promise that resolves on action click, or use callbacks?**
   - Promise (async/await) is cleaner DX — `const { data } = await this.createFieldLayoutDialog({...})`
   - Callback style matches existing `createDialog` — `onClick: ({ data, close }) => {}`
   - **Recommendation:** Support both. Primary action resolves the promise. Custom actions get `{ data, close }` in their onClick.

2. **Should `setFieldProperty` work inside the dialog?**
   - Yes — the dialog should create its own `fieldPropertyOverrides` scope. Script can call `this.setFieldProperty` on the dialog's fields during `onBeforeCreate` or a change hook.
   - Needs design: how to distinguish dialog field overrides from the page field overrides (they share the same controller instance).

3. **Doctype mode vs inline fields mode?**
   - Doctype mode: fetches the Quick Entry layout for that doctype, same as `CreateDocumentModal`
   - Inline mode: fields array defined in the script, wrapped in a single section/column
   - Both should be supported.

### Implementation notes

- **Not a refactor of frappe-ui `Dialog`** — frappe-ui's Dialog is a generic modal shell. We build a new component `FieldLayoutDialog.vue` that uses frappe-ui's `<Dialog>` and renders `<FieldLayout>` inside its `#body` slot.
- **Programmatic mounting** — Similar to how `renderDialog()` in frappe-ui works (using `h()` to push a VNode into `dialogs` ref). We create a `renderFieldLayoutDialog()` utility that returns a Promise.
- **Data isolation** — The dialog creates a temporary reactive `doc` object (not tied to `documentsCache`). When the user clicks an action, the current `doc` state is passed to the callback/resolved promise.
- **FieldLayout dependency** — This is why Phase 3 (decouple FieldLayout) matters. Currently FieldLayout needs `useDocument` which accesses global caches. For a standalone dialog, we need FieldLayout to work with just a doctype + local reactive data, without polluting `documentsCache`.

### Files likely involved

| File | Changes |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | **New** — Dialog + FieldLayout + local doc + actions |
| `frontend/src/utils/renderFieldLayoutDialog.js` | **New** — Programmatic dialog helper using `h()` + Promise |
| `frontend/src/data/script.js` | Add `createFieldLayoutDialog` to prototype |
| `frontend/src/components/Modals/GlobalModals.vue` | Mount the dynamic dialog container |

---

## Phase 3 — Decouple FieldLayout and Grid

> **Priority: HIGH — needed for generic use outside CRM**

### Goal

Make FieldLayout and Grid work as standalone components that only need a `doctype` (or inline field definitions). Remove the hard dependency on inject/provide chains from parent components.

### Current problems

1. **Field.vue has two code paths** — `isGridRow` vs not. The non-grid path calls `useDocument(doctype, data.value.name)` which triggers the entire document resource + script loading. The grid path injects `triggerOnChange` from a parent.

2. **Grid.vue injects 6 things** from parent Field.vue:
   ```
   triggerOnChange, triggerButton, triggerOnRowAdd, triggerOnRowRemove,
   fieldPropertyOverrides, parentFieldname
   ```
   If Grid is rendered outside FieldLayout→Field.vue, all injects get defaults (empty functions/objects) and scripting doesn't work.

3. **FieldLayout.vue calls `useDocument`** to get `fieldPropertyOverrides` for tabs/sections. This ties it to the document resource system.

4. **The provide/inject chain** creates an implicit contract:
   ```
   FieldLayout provides: data, hasTabs, doctype, preview, isGridRow
   Field.vue provides: triggerOnChange, triggerButton, triggerOnRowAdd, triggerOnRowRemove, fieldPropertyOverrides
   Grid.vue provides: parentDoc, fieldPropertyOverrides, parentFieldname
   GridRowModal provides: parentFieldname
   ```

### Proposed approach

**Create a `useFieldLayout(doctype, options)` composable** that encapsulates all the wiring. Components call this instead of inject/provide directly.

```js
// New composable: useFieldLayout.js
export function useFieldLayout(doctype, options = {}) {
  // options.docname — for existing doc context (triggers script loading)
  // options.doc — for standalone/dialog mode (local reactive data, no document resource)
  // options.fieldPropertyOverrides — for external override injection
  // options.onFieldChange — callback when any field changes
  // options.readonly — make all fields read-only

  return {
    doc,                      // reactive doc data
    fieldPropertyOverrides,   // reactive overrides map
    triggerOnChange,          // field change handler
    triggerButton,            // button click handler
    triggerOnRowAdd,          // row add handler
    triggerOnRowRemove,       // row remove handler
    setFieldProperty,         // direct API (no script controller needed)
    removeFieldProperty,
  }
}
```

**FieldLayout, Field, Grid** all consume `useFieldLayout` via a single provide/inject key instead of 6+ separate ones.

### Key questions to decide

1. **Should FieldLayout accept a `doc` prop directly (for dialog/standalone mode) or always go through `useFieldLayout`?**
   - Having both a prop-based mode and a composable-based mode adds flexibility. The composable can be the default, with props as an escape hatch for simple cases.

2. **How does scripting work in standalone mode?**
   - Standalone FieldLayout (dialog, embedded form) doesn't load Form Scripts automatically. The parent decides whether to wire up scripting.
   - For the dialog feature (Phase 2), we might want scripts to NOT run (the dialog is collecting data, not editing a doc).

3. **Should Grid work completely without FieldLayout?**
   - Yes. Grid receives its doctype + parentDoctype + data as props. If `useFieldLayout` context is available (via inject), it uses it. If not, it works in basic mode with just props.

### Files likely involved

| File | Changes |
|---|---|
| `frontend/src/composables/useFieldLayout.js` | **New** — unified composable |
| `frontend/src/components/FieldLayout/FieldLayout.vue` | Use `useFieldLayout` instead of direct `useDocument` + provide |
| `frontend/src/components/FieldLayout/Field.vue` | Inject from single `useFieldLayout` key |
| `frontend/src/components/Controls/Grid.vue` | Inject from `useFieldLayout` key with fallback to props |
| `frontend/src/components/Controls/GridRowModal.vue` | Simplify — just pass context through |

---

## Phase 4 — getMeta Single Source of Truth

> **Priority: MEDIUM — architectural cleanup**

### Goal

Complete the getMeta refactor described in [meta-refactor.md](./meta-refactor.md):

1. `getMeta` `getField(fieldname)` returns a cloned, transformed, override-merged field — **one place** for all transforms
2. Layout APIs return structure only (fieldname strings) + perm overrides map — no embedded field.as_dict()
3. Rendering components call `getField()` instead of doing their own Select/Link transforms
4. `getFields()` no longer filters hidden fields — callers decide

### What was deferred from Phase 1

- `getFields()` still mutates `doctypesMeta` field objects (Select options string → array, Link → User fieldtype)
- Layout APIs still return full `field.as_dict()` per field
- `getFields()` still has `!f.hidden` filter
- `processField()` from `fieldTransforms.js` exists and is tested but not used in rendering components yet

### Dependencies

Phase 3 (decouple FieldLayout) should land first — once FieldLayout uses `useFieldLayout` composable, we can route all field resolution through `getMeta.getField()` in one place.

---

## Phase 5 — Scripting DX Rethink

> **Priority: LOW — after core is stable**

### Ideas to explore

1. **Builder / chainable API**
   ```js
   this.field('annual_revenue').hide()
   this.field('status').setOptions('New\nOpen\nClosed')
   this.field('email').makeRequired().setLabel('Work Email')
   this.section('financial_section').collapse()
   this.tab('advanced_tab').hide()
   ```

2. **Bulk operations**
   ```js
   this.fields(['email', 'phone', 'mobile_no']).makeRequired()
   this.fields(['lost_reason', 'lost_notes']).showWhen(() => this.doc.status === 'Lost')
   ```

3. **Declarative rules** (in addition to imperative)
   ```js
   class CRMLead {
     rules = {
       lost_reason: { hidden: (doc) => doc.status !== 'Lost', reqd: (doc) => doc.status === 'Lost' },
       annual_revenue: { read_only: async () => !(await call('crm.api.can_edit_revenue')) },
     }
   }
   ```

4. **Better event system**
   ```js
   this.on('beforeSave', (doc) => { ... })
   this.on('fieldChange:status', (value, oldValue) => { ... })
   ```

### Backwards compatibility

All new syntax would be additive. `setFieldProperty` continues to work.

---

## Phase 6 — More Capabilities

| Feature | Description |
|---|---|
| **Programmatic layout manipulation** | `this.addField(section, fieldDef)`, `this.moveField(fieldname, targetSection)`, `this.addSection({...})` — virtual fields not in DocType |
| **List view scripting** | Column visibility, custom cell renderers, bulk action hooks |
| **`usePermLevel` composable** | Client-side perm level handling with server validation on save |
| **Inter-script communication** | `this.emit('customEvent', data)` / `this.on('customEvent', handler)` across multiple scripts |
| **Conditional field injection** | Scripts can inject temporary fields that exist only at runtime (not in DocType) |

---

## Design Principles

These apply to all phases:

1. **Generic-first** — Everything is built for reuse beyond Frappe CRM. No CRM-specific assumptions in FieldLayout, Grid, Field, or the scripting engine. CRM-specific behaviour lives in CRM Form Script records and page components, not in the core machinery.

2. **Ask before deciding** — When the current implementation doesn't fit or a design choice could go multiple ways, ask the maintainer rather than assuming. Document the options in the relevant phase doc.

3. **Extensibility via records** — Third-party apps add behaviour by creating `CRM Form Script` records (fixtures, hooks, or UI). No source code modification needed. Multiple scripts per doctype run sequentially.

4. **Props > inject for public API** — Components like FieldLayout and Grid should accept props for their core inputs (doctype, data, fields). inject/provide is for internal wiring between parent-child in the same feature. External consumers should never need to understand the provide chain.

5. **Test before implement** — Extract pure logic to testable utility files. Write tests for the logic before wiring it into components. Use vitest for unit tests (already set up: 96 tests, ~250ms).

6. **Incremental** — Each phase is independently shippable. No phase depends on all prior phases being complete (Phase 3 helps Phase 2, but Phase 2 can land with workarounds).
