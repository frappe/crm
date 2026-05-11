> **Archived.** This file is superseded. See [SPEC.md](../SPEC.md), [PLAN.md](../PLAN.md), [ARCHIVE.md](../ARCHIVE.md), or [feats/form-scripting/](../feats/form-scripting/).

---

# Frontend Testing

> **Status:** Infrastructure set up; unit tests implemented  
> **Related:** [custom-scripting.md](./custom-scripting.md), [meta-refactor.md](./meta-refactor.md)

---

## Setup

**Test runner:** [Vitest](https://vitest.dev/) — same toolchain as Vite, no separate config needed  
**Environment:** `happy-dom` — lightweight DOM for Vue reactivity without a browser  
**Location:** `frontend/tests/`

```bash
cd frontend
yarn test          # watch mode
yarn test:run      # single run (CI)
```

---

## Structure

```
frontend/
  vitest.config.js
  tests/
    setup.js                            # globals: __(), window.sysdefaults
    fixtures/
      leadMeta.js                       # mock CRM Lead field definitions
    unit/
      processField.test.js              # field clone + transform + override logic
      fieldPropertyOverrides.test.js    # setFieldProperty / remove / batch / per-row
      checkMandatory.test.js            # findMissingMandatory with override scenarios
      scriptHelpers.test.js             # getClassNames, createDocProxy
      parseLinkFilters.test.js          # safe JSON/object link_filters parsing
```

**5 files · 96 tests · ~250ms**

---

## What Is Tested

### `processField` (26 tests)

Pure function: `processField(rawField, { permOverrides, propertyOverrides })`.

- Returns a new object (never mutates input)
- `null` / `undefined` → `null`
- Select string → `[{label, value}]`, blank option prepended for non-required, skipped for `reqd`
- Already-array options passed through unchanged
- `Link` + `options='User'` → `fieldtype='User'`
- Perm overrides applied before script overrides
- Script overrides win (read_only from script beats read_only from perm)
- Override changes Select options string before array conversion
- Non-overridden properties preserved

### `fieldPropertyOverrides` map operations (25 tests)

Mirrors the actual `setFieldProperty` / `removeFieldProperty` logic from `script.js`.

- Set / overwrite single property
- Set multiple properties on same field
- Batch set (`setFieldProperties`)
- Remove property, clean up empty key
- Safe on non-existent target/property
- Dot notation (`products.qty`)
- Section and tab names
- **Per-row** — 4th param `rowName` stores as `products.qty:rowName`
- Per-row and column-level coexist independently
- `removeFieldProperty(target, property, rowName)` removes only the row-specific entry

### `findMissingMandatory` (21 tests)

Pure function: `findMissingMandatory(fields, doc, { propertyOverrides, doctypesMeta })`.

- Empty / null inputs → `[]`
- Catches missing `reqd: 1` field (null, undefined, empty string, whitespace, empty array)
- Does not flag filled fields
- Skips `hidden: 1` fields in meta
- `mandatory_depends_on` evaluated correctly (truthy condition → required)
- **Script `reqd: true`** forces mandatory even without `mandatory_depends_on`
- **Script `reqd: false`** removes mandatory from a `reqd: 1` field
- **Script `hidden: true`** skips mandatory check even when `reqd: true`
- **Script `hidden: false`** un-hides + with `reqd: true` → validates
- Script `hidden` wins over `reqd` (hidden + reqd → not validated)
- Script `reqd` wins over `mandatory_depends_on`
- Falls back to `fieldname` when `label` is missing

### `getClassNames` (10 tests) + `createDocProxy` (9 tests)

- Class name extraction from script strings
- Single-line and multi-line comment stripping
- Multiple classes in one script
- Proxy reads/writes to source object
- Getter function source
- `trigger()` calls method on correct instance with correct `this`
- `in` operator, `Object.keys()`

### `parseLinkFilters` (5 tests)

- `null` / `undefined` / `''` → `null`
- Valid JSON string → parsed object
- Already-object → returned as-is (no clone, no parse)
- Invalid JSON → `null`

---

## What Is Not Tested Yet

| Area | Why deferred |
|---|---|
| `Field.vue` rendering | Needs `@vue/test-utils` + extensive frappe-ui mocking |
| `SidePanelLayout.vue` rendering | Same |
| Full script lifecycle (onLoad → overrides → field hides) | Needs running Frappe site |
| Layout API integration | Server-dependent |

Component tests and E2E tests are future work once the architecture is stable.

---

## Adding Tests

1. Add a file to `tests/unit/`
2. Import the function under test from `@/utils/...` (the `@` alias resolves to `src/`)
3. Use standard `describe` / `it` / `expect` — no imports needed (vitest globals)

Functions under test must be **pure** and **importable without side effects**. If a function needs extraction from a Vue component or composable closure, extract it to a utility file first.

```js
import { processField } from '@/utils/fieldTransforms'

describe('processField', () => {
  it('clones the field', () => {
    const raw = { fieldname: 'x', fieldtype: 'Data' }
    expect(processField(raw)).not.toBe(raw)
  })
})
```
