> **Archived.** This file is superseded. See [SPEC.md](../SPEC.md), [PLAN.md](../PLAN.md), [ARCHIVE.md](../ARCHIVE.md), or [feats/form-scripting/](../feats/form-scripting/).

---

# Custom Scripting — Future Phases

> **Pre-requisite context:** [custom-scripting.md](./custom-scripting.md) (implemented Phase 1), [meta-refactor.md](./meta-refactor.md) (architecture), [testing-strategy.md](./testing-strategy.md), [form-scripts.md](./form-scripts.md) (existing scripting API)

---

## Implementation Order

Phases are ordered by dependency, not by original numbering. Each phase is independently shippable.

| Order | Phase | Scope | Why this position |
|---|---|---|---|
| **1** | [3A — FieldLayout standalone mode](#phase-3a--fieldlayout-standalone-mode) | Small (~20 lines) | Unblocks Phase 2 cleanly |
| **2** | [2 — FieldLayout Dialog from Script](#phase-2--fieldlayout-dialog-from-script) | Medium, new files only | Highest user value; clean after 3A |
| **3** | [3B — Full decouple (Grid independent)](#phase-3b--full-decouple-grid-independent) | Structural refactor | Phase 2 stable first; then do risky change |
| **4** | [4 — getMeta single source of truth](#phase-4--getmeta-single-source-of-truth) | Architectural cleanup | Only clean once 3B gives single wiring point |
| **5** | [6 — More Capabilities (selected)](#phase-6--more-capabilities-selected) | Feature expansion | Clean foundation needed |
| **6** | [5 — Scripting DX Rethink](#phase-5--scripting-dx-rethink) | Syntax/API redesign | Must be last — do once full capability set is known |

---

## Phase 3A — FieldLayout Standalone Mode

> **Do first. Small scope, unblocks Phase 2.**

### Problem

`FieldLayout.vue` always calls `useDocument(props.doctype, props.data?.name)` to get
`fieldPropertyOverrides` for tab/section overrides:

```js
// FieldLayout.vue (current)
const { document: doc } = useDocument(props.doctype, props.data?.name)
overrides = computed(() => doc?.fieldPropertyOverrides || {})
```

For a dialog with inline fields (no doctype), this calls `useDocument('', undefined)` and
creates a garbage entry in `documentsCache`. For a dialog with a real doctype like
`'CRM Lost Reason'`, it calls `useDocument('CRM Lost Reason', undefined)`, the dialog's
temporary doc pollutes the global cache, and Form Script loading is triggered
unintentionally for that doctype.

### Fix

Add a way for FieldLayout to receive an externally managed context instead of always
calling `useDocument`. Two options — **decide before implementing:**

**Option A — `standalone` boolean prop**
```js
// FieldLayout.vue
if (!props.isGridRow && !props.standalone) {
  const { document: doc } = useDocument(props.doctype, props.data?.name)
  overrides = computed(() => doc?.fieldPropertyOverrides || {})
} else {
  overrides = computed(() => props.externalOverrides || {})
}
```
Usage: `<FieldLayout :tabs="tabs" :data="localDoc" :doctype="dt" standalone />`

**Option B — `context` prop (object)**
```js
// FieldLayout.vue
if (!props.isGridRow && !props.context) {
  const { document: doc } = useDocument(props.doctype, props.data?.name)
  overrides = computed(() => doc?.fieldPropertyOverrides || {})
} else if (props.context) {
  overrides = computed(() => props.context?.fieldPropertyOverrides || {})
}
```
Usage: `<FieldLayout :tabs="tabs" :data="localDoc" :doctype="dt" :context="localCtx" />`

Option B is better because `context` can carry more in the future (triggerOnChange,
triggerButton, etc.) without adding more props. Confirm before starting.

### Files

| File | Change |
|---|---|
| `frontend/src/components/FieldLayout/FieldLayout.vue` | Add `standalone` or `context` prop; skip `useDocument` when present |

### Checklist
- [ ] Decide: Option A (standalone prop) or Option B (context prop) — ask before implementing
- [ ] Add prop to FieldLayout
- [ ] Skip `useDocument` call when prop is set
- [ ] Ensure existing usages (Lead/Deal pages, all modals) are unaffected — they don't pass the new prop
- [ ] Test: FieldLayout with the new prop doesn't pollute `documentsCache`

---

## Phase 2 — FieldLayout Dialog from Script

> **High priority. Builds directly on Phase 3A.**

### Goal

Allow script authors to open a dialog with a full FieldLayout inside it, collect data
from the user, and act on it — without writing a Vue SFC.

### Decided: dialog fields are NOT scriptable (Option B)

The dialog is a data collector only. `setFieldProperty` called inside a dialog action
affects the **page** fields, not the dialog's fields. Scripting inside dialog fields is
a future iteration (would require isolated `fieldPropertyOverrides` scope and a way to
target dialog vs page fields).

### API

#### Doctype mode — fetch layout from an existing doctype's Quick Entry layout

```js
class CRMLead {
  async mark_as_lost() {
    const result = await this.createFieldLayoutDialog({
      title: 'Mark Lead as Lost',
      doctype: 'CRM Lost Reason',       // fetches Quick Entry layout for this doctype
      size: 'xl',                        // optional, default 'xl'
      defaults: {                        // pre-fill field values
        lead: this.doc.name,
      },
    })

    if (!result) return                  // user cancelled

    this.doc.lost_reason = result.lost_reason
    this.doc.lost_notes = result.lost_notes
    await this.doc.trigger('_save')
    toast.success('Marked as lost')
  }
}
```

#### Inline fields mode — define fields directly in the script

```js
class CRMLead {
  async assign_territory() {
    const result = await this.createFieldLayoutDialog({
      title: 'Assign Territory',
      fields: [
        {
          fieldname: 'territory',
          fieldtype: 'Link',
          label: 'Territory',
          options: 'Territory',
          reqd: 1,
        },
        {
          fieldname: 'notes',
          fieldtype: 'Small Text',
          label: 'Notes',
        },
      ],
      primaryAction: {
        label: 'Assign',
        variant: 'solid',
      },
    })

    if (!result) return

    await call('crm.api.lead.assign_territory', {
      lead: this.doc.name,
      territory: result.territory,
      notes: result.notes,
    })
    toast.success('Territory assigned')
  }
}
```

### Return value

- Resolves with the collected `doc` (plain object of fieldname → value) when the primary
  action is clicked and validation passes.
- Resolves with `null` when the user cancels or closes the dialog.
- The Promise pattern means the calling hook can be `async` and use `await`.

### Validation

Before resolving, the dialog validates mandatory fields (using `findMissingMandatory`
from `fieldTransforms.js`, same as page save validation). If validation fails, it shows
the error inline and does NOT resolve the promise — the dialog stays open.

The script can also pass `required: ['fieldname1', 'fieldname2']` to force-require fields
beyond what the doctype defines.

### Custom actions

For cases needing multiple buttons beyond primary/cancel:

```js
const result = await this.createFieldLayoutDialog({
  title: 'Convert to Deal',
  doctype: 'CRM Deal',
  defaults: { lead: this.doc.name },
  actions: [
    {
      label: 'Convert',
      variant: 'solid',
      onClick: ({ data, close }) => {
        // data = current form values
        // close() dismisses the dialog AND resolves the promise with data
        call('crm.api.lead.convert', { lead: this.doc.name, ...data })
          .then(() => close())
      },
    },
    {
      label: 'Cancel',
      onClick: ({ close }) => close(null),  // resolves with null
    },
  ],
})
```

When `actions` is provided, the Promise resolves with whatever is passed to `close()`.

### Implementation

**No refactor of frappe-ui `Dialog`.** We build a new `FieldLayoutDialog.vue` that uses
frappe-ui's `<Dialog>` shell and renders `<FieldLayout standalone>` (Phase 3A) inside
the `#body` slot.

The dialog mounts programmatically using the same pattern as frappe-ui's `renderDialog`:
a `renderFieldLayoutDialog()` utility creates a VNode with `h()` and pushes it to a
`dialogs` ref that is mounted in `GlobalModals.vue`.

The temporary `doc` object lives only in the dialog component. When the dialog unmounts,
the data is gone.

```
createFieldLayoutDialog({ title, doctype?, fields?, defaults? })
  → renderFieldLayoutDialog()
      → h(FieldLayoutDialog, { ...options, onResolve })
      → pushed to dialogs ref
      → returns Promise that resolves when onResolve is called
          → FieldLayoutDialog mounts, creates local reactive doc
          → User fills form
          → User clicks primary action
          → findMissingMandatory() validates
          → if valid: onResolve(doc), dialog unmounts
          → if invalid: show error, stay open
```

### Files

| File | Change |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | **New** — Dialog + FieldLayout standalone + local doc + actions |
| `frontend/src/utils/renderFieldLayoutDialog.js` | **New** — `h()` + Promise wrapper |
| `frontend/src/data/script.js` | Add `createFieldLayoutDialog` to prototype in `setupHelperMethods` |
| `frontend/src/components/Modals/GlobalModals.vue` | Mount the `FieldLayoutDialog` container |

### Checklist

- [ ] Phase 3A must be merged first
- [ ] `FieldLayoutDialog.vue` — Dialog shell + FieldLayout (standalone) + local reactive doc
- [ ] `renderFieldLayoutDialog.js` — Programmatic mounting + Promise
- [ ] Inline fields mode — wrap `fields[]` in a single tab/section/column layout shape
- [ ] Doctype mode — call `get_fields_layout` API same as `CreateDocumentModal` does
- [ ] `defaults` pre-fill — apply to local doc on mount
- [ ] `required` extra mandatory fields — merge into validation
- [ ] Primary action validates with `findMissingMandatory` before resolving
- [ ] `actions` custom override — resolve/reject based on `close(data)` argument
- [ ] Cancel / close button resolves with `null`
- [ ] `script.js` prototype: `createFieldLayoutDialog` — wraps `renderFieldLayoutDialog` and injects helpers
- [ ] `GlobalModals.vue` — mount container
- [ ] Unit test: `renderFieldLayoutDialog` Promise resolves/rejects correctly

---

## Phase 3B — Full Decouple (Grid Independent)

> **Do after Phase 2 is stable. Structural refactor.**

### Goal

Make `Grid` work as a standalone component that does not depend on inject/provide
chains from `FieldLayout → Field.vue`. Make `FieldLayout` and `Field` use a single
unified context instead of 6+ separate inject keys.

### Why after Phase 2

Phase 3B touches `Field.vue` and `Grid.vue` — the riskiest components in the codebase
(every form surface uses them). It's better to have Phase 2 merged and stable before
making this structural change, so they're not debugged simultaneously.

### Current inject/provide chain (to eliminate)

```
FieldLayout provides:     data, hasTabs, doctype, preview, isGridRow
Field.vue provides:       triggerOnChange, triggerButton, triggerOnRowAdd,
                          triggerOnRowRemove, fieldPropertyOverrides
Field.vue provides:       (also) parentFieldname — for Grid
Grid.vue provides:        parentDoc, fieldPropertyOverrides, parentFieldname
GridRowModal provides:    parentFieldname
```

If Grid is used outside this chain, all injects fall back to defaults (empty
functions/objects) and scripting silently doesn't work.

### Proposed approach

**`useFieldLayout(doctype, options)` composable** — encapsulates all wiring. One
provide/inject key replaces all 6+.

```js
// src/composables/useFieldLayout.js
export function useFieldLayout(doctype, options = {}) {
  // options.docname         — for existing doc (triggers script loading via useDocument)
  // options.doc             — for standalone mode (local reactive data, no useDocument)
  // options.readonly        — all fields read-only
  // options.onFieldChange   — callback instead of script hooks

  const fieldPropertyOverrides = reactive({})

  // If docname provided, wire to useDocument (existing behaviour)
  // If doc provided (standalone), use it directly

  return {
    // Context object — provided under single key 'fieldLayoutContext'
    context: {
      doc,
      doctype,
      fieldPropertyOverrides,
      triggerOnChange,
      triggerButton,
      triggerOnRowAdd,
      triggerOnRowRemove,
      setFieldProperty: (target, property, value, rowName) => { ... },
      removeFieldProperty: (target, property, rowName) => { ... },
    }
  }
}
```

`FieldLayout`, `Field.vue`, `Grid.vue` all inject `'fieldLayoutContext'` instead of
6 separate keys. External consumers that don't use `useFieldLayout` get safe no-op
defaults automatically.

### Key questions to decide before starting

1. **Should Grid work completely without any FieldLayout context?**
   - If yes: Grid needs its own `useDocument`-equivalent for child doctype scripts.
   - If no: Grid without FieldLayout context works for display only (no scripting).
   - Recommendation: "no" for now — Grid standalone = display only, scripting needs context.

2. **Should FieldLayout continue to accept `tabs` as a prop, or should it fetch its own layout?**
   - Currently all callers fetch tabs via `createResource` and pass them in.
   - Moving the fetch inside FieldLayout (given just `doctype` + `type`) would make it
     truly self-contained.
   - Trade-off: less flexible (callers can't transform tabs before passing in).
   - Ask before deciding.

### Files

| File | Change |
|---|---|
| `frontend/src/composables/useFieldLayout.js` | **New** — unified composable |
| `frontend/src/components/FieldLayout/FieldLayout.vue` | Use `useFieldLayout`; provide single context key |
| `frontend/src/components/FieldLayout/Field.vue` | Inject `'fieldLayoutContext'`; remove 6 separate injects |
| `frontend/src/components/Controls/Grid.vue` | Inject `'fieldLayoutContext'` with safe fallback |
| `frontend/src/components/Controls/GridRowModal.vue` | Simplify — propagate context, remove `parentFieldname` prop |

### Checklist

- [ ] Phase 2 must be merged and stable first
- [ ] Decide Grid standalone behaviour (display only vs full scripting)
- [ ] Decide whether FieldLayout fetches its own layout
- [ ] `useFieldLayout.js` composable
- [ ] `FieldLayout.vue` — provide `fieldLayoutContext`; keep Phase 3A `standalone/context` prop working
- [ ] `Field.vue` — inject `fieldLayoutContext`; remove `isGridRow` branch; no more 6 separate injects
- [ ] `Grid.vue` — inject `fieldLayoutContext`; fallback to props-only mode
- [ ] `GridRowModal.vue` — simplify
- [ ] Regression test: all existing forms (Lead, Deal, Contact, Organization pages, all modals)

---

## Phase 4 — getMeta Single Source of Truth

> **After Phase 3B. Completes the architectural cleanup.**

### Goal

Finish the refactor described in [meta-refactor.md](./meta-refactor.md):

1. `getMeta.getField(fieldname)` is the single place that clones, applies overrides, and
   transforms (Select→array, Link→User).
2. Layout APIs (`get_fields_layout`, `get_sidepanel_sections`) return fieldname strings
   only + a perm overrides map — no embedded `field.as_dict()`.
3. Rendering components call `getMeta.getField()` instead of doing their own transforms.
4. `getFields()` no longer filters `hidden` fields — callers decide.

### Why after Phase 3B

Phase 3B gives a single context object (`useFieldLayout`) as the wiring point. Routing
all field resolution through `getMeta.getField()` can happen there in one place instead
of updating `Field.vue`, `SidePanelLayout.vue`, and `Grid.vue` separately.

### What was already done in Phase 1

- `processField()` in `fieldTransforms.js` — the pure transform function, tested, but not
  yet used in rendering
- Cloning before transforms in `Field.vue`, `SidePanelLayout.vue`, `Grid.vue`
- `parseLinkFilters()` replacing `JSON.parse(field.link_filters)` in 6 places

### What remains

- `getFields()` in `meta.js` still mutates `doctypesMeta` field objects
- Layout APIs still return full `field.as_dict()` per field (redundant server call)
- `getFields()` still has `!f.hidden` filter
- `processField()` is tested but not wired into rendering

### Checklist

- [ ] Phase 3B must be merged first
- [ ] `meta.js` — `getField(fieldname, options)` method: clones + applies perm overrides + script overrides + transforms
- [ ] `meta.js` — `getFields()` uses `getField()` internally; removes `!f.hidden` filter; returns clones
- [ ] `useFieldLayout.js` — routes field resolution through `getMeta.getField()`
- [ ] `crm_fields_layout.py` — `get_fields_layout` returns `{ tabs: [...fieldname strings...], perm_overrides: {...} }`
- [ ] `crm_fields_layout.py` — `get_sidepanel_sections` same
- [ ] Update all callers of layout APIs to handle new format
- [ ] `ColumnSettings`, `ViewControls`, `KanbanSettings` — add explicit `hidden` filter since `getFields()` no longer does it
- [ ] Remove redundant Select/Link transforms from `SidePanelLayout.vue` (replaced by `getField()`)

---

## Phase 6 — More Capabilities (selected)

> **After Phase 4. Feature expansion on clean foundation.**

Only the high-value items. The rest remain in the backlog.

### 6A — Programmatic layout manipulation

Inject virtual fields and sections that exist only at runtime — not in the DocType.
Useful for extensions that add UI without modifying the DocType definition.

```js
class CRMLead {
  onLoad() {
    // Add a virtual field after 'status'
    this.addField('basic_section', {
      fieldname: '_score_display',
      fieldtype: 'HTML',
      label: 'Lead Score',
      after: 'status',
    })

    // Add a virtual section
    this.addSection({
      name: '_ext_section',
      label: 'Extension Data',
      after: 'contact_section',
      fields: [
        { fieldname: '_ext_field1', fieldtype: 'Data', label: 'Custom Field' },
      ],
    })
  }
}
```

Virtual fields are managed in a separate `virtualFields` map on the document context
(not in `fieldPropertyOverrides`). They are merged into the layout at render time.

### 6B — `usePermLevel` composable

Move perm level restriction logic client-side. Currently `handle_perm_level_restrictions`
in `crm_fields_layout.py` modifies `read_only`/`hidden` on the server before returning
the layout. This means the client must re-fetch the layout to reflect permission changes.

A `usePermLevel(doctype)` composable would:
- Fetch the user's permitted perm levels per doctype (once, cached)
- Expose a `getPermOverrides(fields)` function that computes restrictions client-side
- Pass the result as `permOverrides` into `getMeta.getField()`

Server still validates on save (defense in depth). The client-side check is for UI only.

**Depends on Phase 4** (getMeta `getField()` accepts `permOverrides`).

### Checklist

- [ ] Phase 4 must be merged first
- [ ] 6A: `addField(sectionName, fieldDef)` prototype method in `script.js`
- [ ] 6A: `addSection(sectionDef)` prototype method
- [ ] 6A: `virtualFields` map on document context
- [ ] 6A: Layout resolution merges virtual fields
- [ ] 6B: `usePermLevel(doctype)` composable
- [ ] 6B: `crm_fields_layout.py` — stop modifying `read_only`/`hidden` server-side; return raw perm data instead
- [ ] 6B: Wire into `getMeta.getField()` via Phase 4

---

## Phase 5 — Scripting DX Rethink

> **Last. Do once the full capability set is known and stable.**

### Why last

- The syntax should reflect all capabilities (Phases 1–6), not a subset
- A syntax change is a breaking change for script authors — do it once
- `setFieldProperty` works well enough in the meantime

### Ideas to explore (not decided)

#### Builder / chainable API

```js
this.field('annual_revenue').hide()
this.field('status').setOptions('New\nOpen\nClosed')
this.field('email').makeRequired().setLabel('Work Email')
this.section('financial_section').collapse()
this.tab('advanced_tab').hide()
this.fields(['email', 'phone']).makeRequired()
```

#### Declarative rules

```js
class CRMLead {
  rules = {
    lost_reason: {
      hidden: (doc) => doc.status !== 'Lost',
      reqd:   (doc) => doc.status === 'Lost',
    },
    annual_revenue: {
      read_only: async () => !(await call('crm.api.can_edit_revenue')),
    },
  }
}
```

#### Reactive shortcuts

```js
this.field('lost_reason')
  .showWhen(() => this.doc.status === 'Lost')
  .requireWhen(() => this.doc.status === 'Lost')
```

### Backwards compatibility

`setFieldProperty`, `setFieldProperties`, `removeFieldProperty`, `getField` continue to
work. New syntax is additive. Deprecation warnings can be added later with a migration
guide.

---

## Deferred / Backlog

These items from Phase 6 are lower priority and independent of the above:

| Feature | Notes |
|---|---|
| List view scripting | Column visibility, custom cell renderers, bulk action hooks. Separate surface area. |
| Inter-script communication | `this.emit('event', data)` / `this.on('event', handler)` across multiple scripts. Low usage, high complexity. |
| Conditional field injection | Variant of 6A — scripts inject fields only when a condition is true. Can follow 6A. |

---

## Design Principles

These apply to all phases. When a decision could go multiple ways, **ask before implementing** rather than assuming.

1. **Generic-first** — No CRM-specific assumptions in FieldLayout, Grid, Field, or the scripting engine. CRM-specific behaviour lives in Form Script records and page components.

2. **Ask before deciding** — Document the options, pick the right one with the maintainer. Especially for: prop names, composable APIs, breaking changes.

3. **Props > inject for public API** — Components accept props for their core inputs. inject/provide is for internal wiring between tightly related parent-child pairs. External consumers should never need to understand the provide chain.

4. **Test pure logic first** — Extract functions to utility files, write unit tests, then wire into components. Vitest is already set up (96 tests, ~250ms).

5. **Incremental, independently shippable** — Each phase merges and is usable on its own. No phase requires a later phase to function.

6. **Extensibility via records** — Third-party apps extend via `CRM Form Script` records (fixtures or hooks). No source code modification. Multiple scripts per doctype run sequentially; last-write-wins for overrides.
