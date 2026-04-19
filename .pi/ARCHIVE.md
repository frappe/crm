# CRM — Completed Work Archive

> **This file**: Completed phases only — decision rationale, what was built, implementation detail.  
> **Current API contracts**: [SPEC.md](./SPEC.md)  
> **Upcoming work**: [PLAN.md](./PLAN.md)

---

## Phase 1 — setFieldProperty & Meta Refactor

> **Completed.** Implemented `setFieldProperty`, `setFieldProperties`, `removeFieldProperty`, `getField` for fields, sections, tabs, and child table rows.

### New pure utility files

| File | Purpose |
|---|---|
| `src/utils/expressions.js` | `_eval`, `evaluateDependsOnValue`, `evaluateExpression` — extracted from `utils/index.js` to allow import without pulling in Vue components |
| `src/utils/fieldTransforms.js` | `processField()`, `findMissingMandatory()`, `parseLinkFilters()` — pure functions, independently testable |
| `src/utils/scriptHelpers.js` | `getClassNames()`, `createDocProxy()` — extracted from `script.js` closure |

### Mutation fixes

Every place that previously mutated shared field objects now clones first:
- `Field.vue` computed: `let field = { ...props.field }`
- `SidePanelLayout.vue` `parsedField()`: `field = { ...field }`
- `Grid.vue` `getFieldObj()`: `field = { ...field }`

`JSON.parse(field.link_filters)` (6 call sites, would throw when `link_filters` was already an object) replaced everywhere with `parseLinkFilters(field.link_filters)`.

### `fieldPropertyOverrides` map structure

Added to the document cache entry alongside `fieldHtmlMap`:

```js
fieldPropertyOverrides = {
  // parent/side-panel fields
  'annual_revenue': { hidden: true },
  'status': { options: 'New\nIn Progress' },

  // sections and tabs (by name)
  'financial_section': { hidden: true },
  'advanced_tab': { hidden: true, label: 'Expert' },

  // child table columns (dot notation)
  'products.qty': { read_only: true },
  'products.discount': { hidden: true },

  // child table per-row (dot notation + colon + row.name)
  'products.rate:row_abc123': { read_only: false },
}
```

### `checkMandatory` rewritten

Old: called `getFields()` which filtered out hidden fields and only checked `mandatory_depends_on`.  
New: `findMissingMandatory()` from `fieldTransforms.js` which:
- Uses raw `doctypesMeta[doctype].fields` (all fields including hidden)
- Checks both `reqd: 1` and `mandatory_depends_on` expressions
- Respects `hidden` and `reqd` from `fieldPropertyOverrides` (script overrides win)
- Hidden fields are always skipped regardless of `reqd`

### Rendering flow (still accurate as of Phase 2)

```
script.js setFieldProperty()
  └─► ctx.fieldPropertyOverrides[target][property] = value
          │
          ├─ SidePanelLayout.vue
          │    parsedField() → Object.assign(field, overrides)
          │    parsedSection() → Object.assign(section, overrides)
          │
          ├─ FieldLayout.vue
          │    processedTabs computed → tab/section overrides merged → hidden tabs filtered
          │    │
          │    └─ Field.vue (non-grid)
          │         computed field → getFieldOverrides(fieldname) → Object.assign(field, overrides)
          │         provide('fieldPropertyOverrides', ...) → Grid.vue injects it
          │
          └─ Field.vue (isGridRow=true, inside GridRowModal)
               inject fieldPropertyOverrides from Grid.vue
               resolves: col key (products.qty) + row key (products.qty:rowName)

Grid.vue
  getFieldObj(field)
    → colKey = `${parentFieldname}.${field.fieldname}`
    → Object.assign(field, overrides[colKey])     ← column-level
    → hidden columns filtered → gridTemplateColumns recalculated

  getRowFieldObj(field, row)
    → rowKey = `${colKey}:${row.name}`
    → merged = { ...colOverrides, ...rowOverrides }  ← row wins over column
    → per-row hidden → empty cell (preserves grid alignment)
```

### Known remaining issues (as of Phase 1 completion)

| Issue | Status |
|---|---|
| `getFields()` still mutates `doctypesMeta` field objects (Select options, Link→User) | Deferred — rendering components clone first now, acceptable until Phase 4 |
| Layout APIs return redundant full field meta | Deferred — full getMeta refactor (Phase 4) |
| `getMeta` `getFields()` filters hidden fields | Intentional for now; raw `doctypesMeta` used where hidden fields needed |

---

## Phase 3A — FieldLayout Standalone Mode

> **Completed.** Added `context` prop to FieldLayout enabling standalone rendering without `useDocument`.

### Problem solved

`FieldLayout.vue` always called `useDocument(props.doctype, props.data?.name)` to get `fieldPropertyOverrides`. For a dialog with inline fields (no doctype), this called `useDocument('', undefined)` creating a garbage entry in `documentsCache`. For a dialog with a real doctype like `'CRM Lost Reason'`, it would trigger script loading unintentionally.

### Decision: Option B — `context` prop

The `context` prop carries the externally managed context object (`{ fieldPropertyOverrides, fieldHtmlMap }`). When provided, `useDocument` is skipped entirely.

**Not chosen: Option A** (`standalone` boolean) — `context` is more extensible, can carry more in future (triggerOnChange, triggerButton, etc.) without adding more props.

### What was built

**`FieldLayout.vue`**:
- Added `context: { type: Object, default: null }` prop
- When `context` is present: uses `context.fieldPropertyOverrides` for tab/section overrides instead of calling `useDocument`
- Provides `fieldLayoutContext` via inject for child Field components

**`Field.vue`**:
- Injects `fieldLayoutContext`. When present: skips `useDocument` entirely, field changes update data directly, scripting triggers are no-ops
- Guards `getMeta(doctype)` — only called when doctype is truthy. Inline mode uses `formatNumber`/`formatCurrency` fallback formatters directly

---

## Phase 2 — formDialog()

> **Completed.** Script authors can open a FieldLayout-based dialog, collect data, and act on it.

### Decision: Option C — Promise + onSubmit callback + custom actions (all three work)

Three patterns were considered:
- **Option A** (callbacks only, consistent with `createDialog`) — too verbose for simple cases
- **Option B** (`onSubmit` only) — doesn't support sequential multi-step workflows
- **Option C** (all three, Promise always resolves) — chosen. Most flexible. Promise for sequential, callback for fire-and-forget, actions for full control.

**Dialog fields are NOT scriptable (intentional).** The dialog is a data collector only. `setFieldProperty` called inside a dialog action affects the **page** fields, not the dialog's fields. Full isolation would require a separate `fieldPropertyOverrides` scope per dialog — deferred.

### What was built

| File | Description |
|---|---|
| `frontend/src/components/Modals/FieldLayoutDialog.vue` | Dialog shell + standalone FieldLayout + local reactive doc. Validates before resolving. |
| `frontend/src/components/Modals/FieldLayoutDialogContainer.vue` | Renders entries from the `fieldLayoutDialogs` reactive array |
| `frontend/src/utils/renderFieldLayoutDialog.js` | Pushes config to array, returns Promise. Internal `onResolve` is distinct from user's `onSubmit`. |
| `frontend/src/components/Modals/GlobalModals.vue` | Mounts `<FieldLayoutDialogContainer />` |
| `frontend/src/data/script.js` | `helpers.formDialog = renderFieldLayoutDialog` — bare helper in script scope |

### Key fixes during implementation

- **Buttons stuck in loading**: `_loading` was a `ref()` inside `computed()`. Vue doesn't auto-unwrap refs nested inside plain objects in templates. Fixed with `reactive({})` `actionLoadingMap` outside the computed.
- **Double-event bug**: `v-bind="dialog.props"` passed `onResolve` as a `@resolve` listener AND `@resolve` explicitly added it again. Fixed by stripping `onResolve` from the spread in `FieldLayoutDialogContainer`.
- **`getMeta('')` console error**: `Field.vue` called `getMeta(doctype)` unconditionally. When doctype is empty (inline mode) this triggers an API call that fails. Fixed with doctype guard.
- **`v-bind="action"` spreading internals**: Template was spreading entire action objects including `_loading` ref, wrapped `onClick`, etc. onto Button. Fixed with explicit prop bindings.

### Layout priority

1. `tabs` — full custom layout (highest)
2. `fields` — flat list, auto-wrapped
3. `doctype` + `fieldnames` — specific fields from doctype meta
4. `doctype` alone — full Quick Entry layout

> Current stable API: [SPEC.md — formDialog API](./SPEC.md#formdialog-api)  
> Full guide with examples: [feats/form-scripting/form-dialog.md](./feats/form-scripting/form-dialog.md)
