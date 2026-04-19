> **Archived.** This file is superseded. See [SPEC.md](../SPEC.md), [PLAN.md](../PLAN.md), [ARCHIVE.md](../ARCHIVE.md), or [feats/form-scripting/](../feats/form-scripting/).

---

# Custom Scripting — Field Property Overrides

> **Status:** Implemented  
> **Scope:** `setFieldProperty` / `setFieldProperties` / `removeFieldProperty` / `getField` for fields, sections, tabs, and child table rows  
> **Related:** [form-scripts.md](./form-scripts.md) (full scripting docs), [meta-refactor.md](./meta-refactor.md) (architecture), [testing-strategy.md](./testing-strategy.md)

---

## Table of Contents

1. [API Reference](#api-reference)
2. [Supported Properties](#supported-properties)
3. [Override Priority](#override-priority)
4. [Child Table Fields](#child-table-fields)
5. [Per-Row Overrides](#per-row-overrides)
6. [Sections and Tabs](#sections-and-tabs)
7. [Create Modal Support](#create-modal-support)
8. [Examples](#examples)
9. [Future Phases](#future-phases)

---

## API Reference

### `this.setFieldProperty(target, property, value [, rowName])`

Set a single property on a field, section, or tab.

```js
// Parent/side-panel field
this.setFieldProperty('annual_revenue', 'hidden', true)

// Child table column (dot notation)
this.setFieldProperty('products.qty', 'read_only', true)

// Specific row in child table (4th param: row.name)
this.setFieldProperty('products.qty', 'read_only', true, row.name)

// Section (by section name from layout)
this.setFieldProperty('financial_section', 'hidden', true)

// Tab (by tab name from layout)
this.setFieldProperty('advanced_tab', 'hidden', true)
```

| Parameter | Type | Description |
|---|---|---|
| `target` | `string` | Field name, `parentfield.childfield`, section name, or tab name |
| `property` | `string` | Any DocField property (`hidden`, `read_only`, `reqd`, `options`, `label`, etc.) |
| `value` | `any` | New value |
| `rowName` | `string` | *(optional)* `row.name` for per-row override |

---

### `this.setFieldProperties(target, properties [, rowName])`

Set multiple properties in one call.

```js
this.setFieldProperties('annual_revenue', {
  read_only: true,
  label: 'Revenue (USD)',
  description: 'Auto-calculated from linked deals',
})

// Per-row batch
this.setFieldProperties('products.rate', { read_only: true, label: 'Fixed' }, row.name)
```

---

### `this.removeFieldProperty(target, property [, rowName])`

Remove a specific override, reverting to the original server meta value.

```js
this.removeFieldProperty('annual_revenue', 'hidden')
this.removeFieldProperty('products.qty', 'read_only', row.name)  // per-row only
```

---

### `this.getField(fieldname)`

Returns a snapshot of the effective field definition: raw server meta merged with current overrides. Not reactive — call again after changes if you need the latest.

```js
const field = this.getField('status')
console.log(field.options)    // current options (array after transform)
console.log(field.read_only)  // current effective read_only
console.log(field.hidden)     // current hidden state
```

---

## Supported Properties

All DocField properties are settable. The ones with visible UI effect:

### Field

| Property | Type | Effect |
|---|---|---|
| `hidden` | `boolean` | Show/hide the field |
| `read_only` | `boolean` | Make non-editable |
| `reqd` | `boolean` | Make mandatory (asterisk + pre-save validation) |
| `label` | `string` | Column header / field label |
| `placeholder` | `string` | Input placeholder text |
| `description` | `string` | Help text below the field |
| `options` | `string` | Select choices (newline-separated) or Link doctype |
| `link_filters` | `object` | Filter object for Link autocomplete |
| `precision` | `string` | Decimal precision for Float/Currency/Percent |
| `non_negative` | `boolean` | Disallow negative values |
| `bold` | `boolean` | Bold label |
| `button_color` | `string` | Button variant: `"Default"`, `"Primary"`, `"Info"`, `"Success"`, `"Warning"`, `"Danger"` |
| `max_height` | `string` | Max height CSS for Text/Code fields |

### Select `options` format

Always pass a **newline-separated string**. The UI converts it to `[{label, value}]` automatically.

```js
this.setFieldProperty('status', 'options', 'New\nIn Progress\nClosed')
```

### `link_filters` format

Pass a plain **object**. It is handled safely whether stored as object or JSON string.

```js
this.setFieldProperty('lead_owner', 'link_filters', { enabled: 1, user_type: 'System User' })
```

### Section

| Property | Type | Effect |
|---|---|---|
| `hidden` | `boolean` | Show/hide entire section |
| `label` | `string` | Section heading |
| `collapsible` | `boolean` | Make collapsible |
| `opened` | `boolean` | Expanded/collapsed default state |
| `hideLabel` | `boolean` | Hide the section label |
| `hide_border` | `boolean` | Remove the top border |

### Tab

| Property | Type | Effect |
|---|---|---|
| `hidden` | `boolean` | Show/hide the entire tab |
| `label` | `string` | Tab heading |

---

## Override Priority

Script overrides always win over server meta and `depends_on` expressions:

```
Final value =
  1. Script per-row override  (products.qty:row_name)    ← highest
  2. Script column override   (products.qty)
  3. Script field override    (fieldname)
  4. depends_on expression    (read_only_depends_on, etc.)
  5. Server meta default                                  ← lowest
```

**Hidden fields are skipped in mandatory validation.** A field hidden via script override is never checked for `reqd`, even if it is mandatory in the DocType.

---

## Child Table Fields

Use dot notation `parentfield.childfield` to target a column in a child table. This works in both the inline Grid and in the Edit Row modal.

```js
class CRMDeal {
  onLoad() {
    // Hide a column for all rows
    this.setFieldProperty('products.discount', 'hidden', true)

    // Make a column read-only
    this.setFieldProperty('products.amount', 'read_only', true)

    // Change label of a column header
    this.setFieldProperty('products.qty', 'label', 'Quantity')

    // Replace select options
    this.setFieldProperty('products.uom', 'options', 'Nos\nKg\nLitre\nBox')
  }
}
```

Hidden columns are removed from the grid entirely — both the header and all cells — and the CSS `grid-template-columns` is recalculated so remaining columns fill the space.

---

## Per-Row Overrides

Pass `row.name` as the optional 4th argument to target a specific row only.

**Priority:** per-row override → column-level override → server meta.

```js
class CRMDeal {
  async qty() {
    const row = this.getRow('products', this.currentRowIdx)
    if (!row) return

    // Lock rate for high-volume rows
    const isLarge = row.qty > 100
    this.setFieldProperty('products.rate', 'read_only', isLarge, row.name)

    // Revert when qty drops back
    if (!isLarge) {
      this.removeFieldProperty('products.rate', 'read_only', row.name)
    }
  }
}
```

Per-row `hidden` renders an empty cell rather than removing it, preserving grid column alignment.

---

## Sections and Tabs

Use the section/tab **name** (the `name` field in the layout JSON, not the label).

```js
class CRMLead {
  onLoad() {
    // Collapse a section by default
    this.setFieldProperties('financial_section', {
      collapsible: true,
      opened: false,
    })

    // Hide a tab entirely
    this.setFieldProperty('advanced_tab', 'hidden', true)
  }

  // Show financial section only for qualified leads
  status() {
    this.setFieldProperty(
      'financial_section',
      'hidden',
      this.doc.status !== 'Qualified',
    )
  }
}
```

---

## Create Modal Support

Scripts run for new documents (`useDocument(doctype, '')`) and their overrides flow into create modals (LeadModal, DealModal, CreateDocumentModal) automatically — no extra wiring needed.

```js
class CRMLead {
  onBeforeCreate() {
    // Validate inside the create modal
    if (!this.doc.email && !this.doc.mobile_no) {
      throwError('Provide at least one contact method')
    }
  }

  onLoad() {
    // This also runs when the create modal opens for a new doc
    this.setFieldProperty('lost_reason', 'hidden', true)
  }
}
```

---

## Examples

### Show/hide fields based on another field

```js
class CRMLead {
  onLoad() {
    this._syncVisibility()
  }

  status() {
    this._syncVisibility()
  }

  _syncVisibility() {
    const isLost = this.doc.status === 'Lost'
    this.setFieldProperty('lost_reason', 'hidden', !isLost)
    this.setFieldProperty('lost_reason', 'reqd', isLost)
  }
}
```

### Dynamic Link filters

```js
class CRMDeal {
  organization() {
    if (this.doc.organization) {
      this.setFieldProperty('contact', 'link_filters', {
        company_name: this.doc.organization,
      })
    } else {
      this.removeFieldProperty('contact', 'link_filters')
    }
  }
}
```

### Dynamic Select options from API

```js
class CRMDeal {
  async pipeline() {
    const stages = await call('crm.api.get_deal_stages', {
      pipeline: this.doc.pipeline,
    })
    this.setFieldProperty('stage', 'options', stages.join('\n'))
    this.doc.stage = stages[0] || ''
  }
}
```

### Async permission check

```js
class CRMLead {
  async onLoad() {
    const canEdit = await call('crm.api.check_permission', {
      action: 'edit_revenue',
    })
    this.setFieldProperty('annual_revenue', 'read_only', !canEdit)
  }
}
```

### Child table: column + per-row

```js
class CRMDeal {
  onLoad() {
    // All rows: hide discount column
    this.setFieldProperty('products.discount', 'hidden', true)
    // All rows: amount is calculated
    this.setFieldProperty('products.amount', 'read_only', true)
  }

  async qty() {
    const row = this.getRow('products', this.currentRowIdx)
    if (!row) return
    // Specific row: lock rate for large qty
    this.setFieldProperty(
      'products.rate',
      'read_only',
      row.qty > 100,
      row.name,
    )
  }
}
```

---

## Future Phases

| Phase | Scope |
|---|---|
| **Next** | [FieldLayout Dialog from Script](./future-phases.md#phase-2--fieldlayout-dialog-from-script) — `this.createFieldLayoutDialog()` |
| **Next** | [Decouple FieldLayout and Grid](./future-phases.md#phase-3--decouple-fieldlayout-and-grid) — `useFieldLayout` composable |
| **Later** | [getMeta single source of truth](./future-phases.md#phase-4--getmeta-single-source-of-truth) |
| **Later** | [Scripting DX rethink](./future-phases.md#phase-5--scripting-dx-rethink) — builder/chainable syntax |
| **Later** | [More capabilities](./future-phases.md#phase-6--more-capabilities) — layout manipulation, list scripting, perm level composable |

Full details: [future-phases.md](./future-phases.md)
