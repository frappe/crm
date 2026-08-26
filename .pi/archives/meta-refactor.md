> **Archived.** This file is superseded. See [SPEC.md](../SPEC.md), [PLAN.md](../PLAN.md), [ARCHIVE.md](../ARCHIVE.md), or [feats/form-scripting/](../feats/form-scripting/).

---

# Meta Architecture — Partial Refactor

> **Status:** Phase 1 complete, Phase 2 deferred  
> **Related:** [custom-scripting.md](./custom-scripting.md), [testing-strategy.md](./testing-strategy.md)

---

## What Was Done (Phase 1)

The goal was to make `setFieldProperty` work cleanly without breaking existing behaviour. We did the minimum necessary refactoring:

### New pure utility files

| File | Purpose |
|---|---|
| `src/utils/expressions.js` | `_eval`, `evaluateDependsOnValue`, `evaluateExpression` — extracted from `utils/index.js` so they can be imported without pulling in Vue components and icon imports |
| `src/utils/fieldTransforms.js` | `processField()`, `findMissingMandatory()`, `parseLinkFilters()` — pure functions, independently testable |
| `src/utils/scriptHelpers.js` | `getClassNames()`, `createDocProxy()` — extracted from `script.js` closure |

### Mutation fixes

Every place that previously mutated shared field objects now clones first:

- `Field.vue` computed: `let field = { ...props.field }` before any transforms
- `SidePanelLayout.vue` `parsedField()`: `field = { ...field }` at the top
- `Grid.vue` `getFieldObj()`: `field = { ...field }` at the top

`JSON.parse(field.link_filters)` was called in 6 places and would throw when `link_filters` was an object (e.g. set via script). Replaced with `parseLinkFilters(field.link_filters)` which handles both string and object input safely.

### `fieldPropertyOverrides` map

Added to the document cache entry alongside `fieldHtmlMap`:

```js
// document.js — existing doc
documentsCache[doctype][docname].fieldPropertyOverrides = {}

// document.js — new doc
documentsCache[doctype][''] = reactive({
  doc: { __newDocument: true, doctype },
  fieldPropertyOverrides: {},
})
```

Structure:

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

The old implementation called `getFields()` which filtered out hidden fields, and only checked `mandatory_depends_on` (missing plain `reqd` fields). Replaced with `findMissingMandatory()` from `fieldTransforms.js` which:

- Uses raw `doctypesMeta[doctype].fields` (all fields, including hidden)
- Checks both `reqd: 1` and `mandatory_depends_on` expressions
- Respects `hidden` and `reqd` from `fieldPropertyOverrides` (script overrides win)
- Hidden fields are always skipped regardless of `reqd`

### `utils/index.js` — no duplicate code

The three expression functions are now defined once in `expressions.js` and re-exported from `utils/index.js`:

```js
export { _eval, evaluateDependsOnValue, evaluateExpression } from '@/utils/expressions'
```

All existing imports from `'@/utils'` continue to work unchanged.

---

## What Was Not Done (Deferred)

### `getMeta` single-source-of-truth refactor

The plan to make `getMeta`'s `getField()` the single place for field transformation (with `processField()` called from there) was scoped out. The layout APIs (`get_fields_layout`, `get_sidepanel_sections`) still return full `field.as_dict()` objects embedded in the layout response.

`processField()` exists and is used by `findMissingMandatory()` and the tests, but Field.vue / SidePanelLayout.vue still do their own Select/Link transforms locally. This is intentional — a full getMeta centralisation would require:
- Layout APIs to return fieldnames only + perm overrides map
- All rendering components to resolve fields via getMeta
- Risk of breaking the 13+ modals that consume the layout APIs

This remains the next priority refactor.

### `getFields()` still filters hidden fields

`meta.js` `getFields()` still has `!f.hidden` in its filter. This is left as-is because many consumers (ColumnSettings, ViewControls, KanbanSettings, FieldLayoutEditor) expect only non-hidden fields. `checkMandatory` was updated to use the raw fields array directly, bypassing this filter.

### Perm level composable

`handle_perm_level_restrictions` in `crm_fields_layout.py` remains server-side. No `usePermLevel` composable was created. This is future work.

---

## Rendering — How Overrides Reach the UI

```
script.js setFieldProperty()
  └─► ctx.fieldPropertyOverrides[target][property] = value
          │
          ├─ SidePanelLayout.vue
          │    parsedField()  → Object.assign(field, overrides) → isFieldVisible(field, overrides?.hidden)
          │    parsedSection() → Object.assign(section, overrides) → section.visible
          │
          ├─ FieldLayout.vue
          │    processedTabs computed → tab/section overrides merged → hidden tabs filtered
          │    │
          │    └─ Field.vue (non-grid)
          │         computed field → getFieldOverrides(fieldname) → Object.assign(field, overrides)
          │         isFieldVisible(field, scriptHidden)
          │         provide('fieldPropertyOverrides', ...) → Grid.vue injects it
          │
          └─ Field.vue (isGridRow=true, inside GridRowModal)
               computed field → getFieldOverrides(fieldname)
                 → injects fieldPropertyOverrides from Grid.vue
                 → resolves: col key (products.qty) + row key (products.qty:rowName)
```

```
Grid.vue
  getFieldObj(field)
    → colKey = `${parentFieldname}.${field.fieldname}`
    → Object.assign(field, overrides[colKey])     ← column-level
    → fields computed filters hidden columns
    → gridTemplateColumns uses fields.value (already filtered)

  getRowFieldObj(field, row)
    → colKey = `${parentFieldname}.${field.fieldname}`
    → rowKey = `${colKey}:${row.name}`
    → merged = { ...colOverrides, ...rowOverrides }   ← row wins over column
    → per-row hidden → empty cell (preserves grid alignment)

  provide('fieldPropertyOverrides', parentFieldPropertyOverrides)
  provide('parentFieldname', props.parentFieldname)
        │
        └─ GridRowModal.vue
             provide('parentFieldname', props.parentFieldname)
               │
               └─ FieldLayout (isGridRow=true) → Field.vue (isGridRow=true)
                    getFieldOverrides() uses injected overrides + parentFieldname
```

---

## Known Remaining Issues

| Issue | Status |
|---|---|
| `getFields()` still mutates `doctypesMeta` field objects (Select options, Link→User fieldtype) | Not fixed — rendering components now clone first, so mutations in `getFields()` only affect the meta store copy once, which is acceptable until full getMeta refactor |
| Layout APIs return redundant full field meta | Deferred — full getMeta refactor needed |
| `getMeta` `getFields()` filters hidden fields | Intentional for now; consumers that need hidden fields use raw `doctypesMeta` directly |
