# Form Dialog — `formDialog()`

> **Status:** Implemented  
> **Available since:** Phase 2 of custom scripting  
> **Full scripting guide**: [guide.md](./guide.md)  
> **API contracts**: [SPEC.md](../../SPEC.md)

---

## Overview

`formDialog()` opens a dialog containing a full FieldLayout — the same component that renders fields on Lead/Deal/Contact pages. It collects data from the user and hands it back to your script.

Available as a **bare helper** inside any CRM Form Script — no `this.` needed:

```js
const result = await formDialog({ title: 'My Dialog', fields: [...] })
```

---

## Three Usage Patterns

All three patterns work together. The Promise always resolves regardless of which style you use.

### 1. Promise — sequential workflows

```js
class CRMLead {
  async multi_step() {
    const step1 = await formDialog({
      title: 'Step 1: Contact Info',
      fields: [
        { fieldname: 'email', fieldtype: 'Data', label: 'Email', reqd: 1 },
        { fieldname: 'phone', fieldtype: 'Data', label: 'Phone' },
      ],
    })
    if (!step1) return // cancelled

    const step2 = await formDialog({
      title: 'Step 2: Confirm',
      fields: [
        { fieldname: 'notes', fieldtype: 'Small Text', label: 'Notes' },
      ],
      defaults: { notes: 'Contact: ' + step1.email },
    })
    if (!step2) return

    await call('crm.api.lead.process', { ...step1, ...step2 })
    toast.success('Done')
  }
}
```

### 2. `onSubmit` callback — fire-and-forget

Code after `formDialog()` runs immediately. The `onSubmit` callback fires when the user submits and validation passes. If `onSubmit` throws, the dialog stays open and shows the error.

```js
class CRMLead {
  mark_as_lost() {
    formDialog({
      title: 'Mark as Lost',
      fields: [
        { fieldname: 'lost_reason', fieldtype: 'Link', label: 'Lost Reason', options: 'CRM Lost Reason', reqd: 1 },
        { fieldname: 'lost_notes', fieldtype: 'Small Text', label: 'Notes' },
      ],
      submitLabel: 'Mark as Lost',
      cancelLabel: 'Cancel',
      onSubmit: async (data) => {
        await call('crm.api.lead.mark_lost', {
          lead: this.doc.name,
          reason: data.lost_reason,
          notes: data.lost_notes,
        })
        toast.success('Marked as lost')
      },
      onCancel: () => {
        toast.info('Cancelled')
      },
    })
    // This runs immediately — does not wait for dialog
  }
}
```

### 3. Custom `actions` — full control

When `actions` is provided, no default Submit button is rendered. Each action handles its own logic via `onClick({ data, close, validate })`.

```js
class CRMDeal {
  review_deal() {
    formDialog({
      title: 'Review Deal',
      fields: [
        { fieldname: 'notes', fieldtype: 'Small Text', label: 'Review Notes', reqd: 1 },
      ],
      actions: [
        {
          label: 'Approve',
          variant: 'solid',
          async onClick({ data, close, validate }) {
            if (!validate()) return
            await call('crm.api.deal.approve', { deal: this.doc.name, notes: data.notes })
            toast.success('Deal approved')
            close('approved')
          },
        },
        {
          label: 'Reject',
          variant: 'subtle',
          theme: 'red',
          async onClick({ data, close, validate }) {
            if (!validate()) return
            await call('crm.api.deal.reject', { deal: this.doc.name, notes: data.notes })
            toast.warning('Deal rejected')
            close('rejected')
          },
        },
        {
          label: 'Cancel',
          onClick({ close }) { close(null) },
        },
      ],
    })
  }
}
```

---

## API

```js
formDialog(options)  // → Promise<object|null>
```

### Options

| Option | Type | Description |
|---|---|---|
| `title` | `string` | Dialog title. Default: `'Dialog'` |
| `fields` | `Array` | Flat list of field definitions — wrapped in a single section |
| `tabs` | `Array` | Full layout: `tabs > sections > columns > fields` |
| `doctype` | `string` | Fetch the Quick Entry layout for this doctype |
| `fieldnames` | `Array<string>` | With `doctype` — pick only these fields from doctype meta |
| `defaults` | `object` | Pre-fill field values |
| `required` | `Array<string>` | Force mandatory (shows asterisk + validates) |
| `size` | `string` | Dialog size: `'sm'`, `'md'`, `'lg'`, `'xl'`, `'2xl'`. Default: `'xl'` |
| `actions` | `Array` | Custom action buttons. Overrides default Submit and `onSubmit` |
| `onSubmit` | `Function` | Called with `data` on submit. Throw to stay open. Ignored when `actions` is set |
| `onCancel` | `Function` | Called when dialog is cancelled/closed (X, overlay, escape) |
| `submitLabel` | `string` | Label for the default Submit button. Default: `'Submit'` |
| `cancelLabel` | `string` | If provided, shows a Cancel button with this label |

### Return value

Always returns a `Promise<object|null>`:
- Resolves with `{ fieldname: value, ... }` on submit
- Resolves with `null` on cancel/close
- If you don't `await` it, the Promise is silently ignored — no unhandled rejection

### Layout priority

1. `tabs` — full custom layout (highest)
2. `fields` — flat field list, auto-wrapped
3. `doctype` + `fieldnames` — specific fields from doctype meta
4. `doctype` alone — full Quick Entry layout

### Behavior matrix

| `actions` | `onSubmit` | What happens |
|---|---|---|
| ✗ | ✗ | Default Submit button → validates → closes → Promise resolves with data |
| ✗ | ✓ | Default Submit button → validates → calls `onSubmit(data)` → closes → Promise resolves |
| ✓ | (ignored) | Custom buttons only. Each calls `close(result)` to resolve the Promise |

If `onSubmit` throws an error, the dialog stays open and shows the error message.

---

## Actions Reference

Each action in the `actions` array:

| Key | Type | Description |
|---|---|---|
| `label` | `string` | Button text |
| `variant` | `string` | `'solid'`, `'subtle'`, `'outline'`, `'ghost'` |
| `theme` | `string` | `'red'`, `'green'`, `'blue'`, `'orange'`, `'gray'` |
| `icon` | `string` | Icon name |
| `onClick` | `Function` | `({ data, close, validate }) => {}` |

**Action without `onClick`**: uses default behavior (validate → close with data).

**`close(result)`**: closes the dialog and resolves the Promise with `result`. Use `close(null)` for cancel buttons.

**`validate()`**: runs mandatory field validation. Returns `true`/`false`. Call before `close()` to prevent closing with invalid data.

---

## Layout Modes

### Flat fields (simplest)

```js
formDialog({
  title: 'Quick Input',
  fields: [
    { fieldname: 'name', fieldtype: 'Data', label: 'Name', reqd: 1 },
    { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
  ],
  onSubmit(data) {
    toast.success(data.name)
  },
})
```

### Two-column layout

```js
formDialog({
  title: 'Contact Details',
  tabs: [
    {
      name: 'main',
      label: '',
      sections: [
        {
          name: 'person',
          label: '',
          columns: [
            {
              name: 'left',
              fields: [
                { fieldname: 'first_name', fieldtype: 'Data', label: 'First Name', reqd: 1 },
                { fieldname: 'last_name', fieldtype: 'Data', label: 'Last Name' },
              ],
            },
            {
              name: 'right',
              fields: [
                { fieldname: 'email', fieldtype: 'Data', label: 'Email', reqd: 1 },
                { fieldname: 'phone', fieldtype: 'Data', label: 'Phone' },
              ],
            },
          ],
        },
      ],
    },
  ],
  onSubmit(data) {
    toast.success(`${data.first_name} ${data.last_name}`)
  },
})
```

### Sections with labels

```js
formDialog({
  title: 'Full Form',
  tabs: [
    {
      name: 'main',
      label: '',
      sections: [
        {
          name: 'basic',
          label: 'Basic Info',
          columns: [
            {
              name: 'c1',
              fields: [
                { fieldname: 'name', fieldtype: 'Data', label: 'Name', reqd: 1 },
                { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
              ],
            },
          ],
        },
        {
          name: 'extra',
          label: 'Additional',
          columns: [
            {
              name: 'c2',
              fields: [
                { fieldname: 'notes', fieldtype: 'Small Text', label: 'Notes' },
              ],
            },
          ],
        },
      ],
    },
  ],
})
```

### Multiple tabs

Give each tab a `label` to show the tab bar:

```js
formDialog({
  title: 'New Lead',
  size: '2xl',
  tabs: [
    {
      name: 'basic',
      label: 'Basic Info',
      sections: [
        {
          name: 's1',
          label: '',
          columns: [
            {
              name: 'c1',
              fields: [
                { fieldname: 'first_name', fieldtype: 'Data', label: 'First Name', reqd: 1 },
                { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
              ],
            },
          ],
        },
      ],
    },
    {
      name: 'company',
      label: 'Company',
      sections: [
        {
          name: 's2',
          label: '',
          columns: [
            {
              name: 'c2',
              fields: [
                { fieldname: 'organization', fieldtype: 'Link', label: 'Organization', options: 'CRM Organization' },
                { fieldname: 'website', fieldtype: 'Data', label: 'Website' },
              ],
            },
          ],
        },
      ],
    },
  ],
})
```

### Doctype mode — Quick Entry layout

```js
formDialog({
  title: 'New Contact',
  doctype: 'Contact',
  onSubmit(data) {
    toast.success('Contact: ' + data.first_name)
  },
})
```

### Doctype + fieldnames — pick specific fields

```js
formDialog({
  title: 'Quick Lead',
  doctype: 'CRM Lead',
  fieldnames: ['first_name', 'email', 'mobile_no', 'status'],
  required: ['email'],
  defaults: { status: 'New' },
  onSubmit(data) {
    toast.success('Lead: ' + data.first_name)
  },
})
```

---

## Required Fields

Fields in `required` are forced mandatory — red asterisk + validation — across all layout modes:

```js
formDialog({
  title: 'Contact',
  doctype: 'Contact',
  required: ['email_id', 'mobile_no'],
})
```

---

## Complete Form Script Examples

### Collect lost reason (onSubmit)

```js
class CRMLead {
  mark_as_lost() {
    formDialog({
      title: 'Mark Lead as Lost',
      fields: [
        { fieldname: 'lost_reason', fieldtype: 'Link', label: 'Lost Reason', options: 'CRM Lost Reason', reqd: 1 },
        { fieldname: 'lost_notes', fieldtype: 'Small Text', label: 'Notes' },
      ],
      submitLabel: 'Mark as Lost',
      cancelLabel: 'Cancel',
      onSubmit: async (data) => {
        this.doc.lost_reason = data.lost_reason
        this.doc.lost_notes = data.lost_notes
        this.doc.status = 'Lost'
        toast.success('Marked as lost')
      },
    })
  }
}
```

### Sequential prompts (Promise)

```js
class CRMLead {
  async convert_to_deal() {
    const dealInfo = await formDialog({
      title: 'Convert to Deal',
      doctype: 'CRM Lead',
      fieldnames: ['organization', 'website', 'annual_revenue'],
      required: ['organization'],
    })
    if (!dealInfo) return

    const confirm = await formDialog({
      title: 'Confirm Conversion',
      fields: [
        { fieldname: 'deal_name', fieldtype: 'Data', label: 'Deal Name', reqd: 1 },
        { fieldname: 'pipeline', fieldtype: 'Link', label: 'Pipeline', options: 'CRM Pipeline' },
      ],
      defaults: { deal_name: this.doc.lead_name },
    })
    if (!confirm) return

    await call('crm.api.lead.convert', { lead: this.doc.name, ...dealInfo, ...confirm })
    toast.success('Converted to deal')
  }
}
```

### Approve/Reject (custom actions)

```js
class CRMDeal {
  review() {
    formDialog({
      title: 'Review Deal',
      fields: [
        { fieldname: 'notes', fieldtype: 'Small Text', label: 'Review Notes', reqd: 1 },
      ],
      actions: [
        {
          label: 'Approve',
          variant: 'solid',
          async onClick({ data, close, validate }) {
            if (!validate()) return
            await call('crm.api.deal.approve', { deal: this.doc.name, notes: data.notes })
            toast.success('Approved')
            close('approved')
          },
        },
        {
          label: 'Reject',
          variant: 'subtle',
          theme: 'red',
          async onClick({ data, close, validate }) {
            if (!validate()) return
            await call('crm.api.deal.reject', { deal: this.doc.name, notes: data.notes })
            toast.warning('Rejected')
            close('rejected')
          },
        },
        {
          label: 'Cancel',
          onClick({ close }) { close(null) },
        },
      ],
    })
  }
}
```

### Server call in onSubmit (stays open on error)

```js
class CRMLead {
  assign_territory() {
    formDialog({
      title: 'Assign Territory',
      fields: [
        { fieldname: 'territory', fieldtype: 'Link', label: 'Territory', options: 'Territory', reqd: 1 },
      ],
      onSubmit: async (data) => {
        // If this throws, dialog stays open and shows the error
        await call('crm.api.lead.assign_territory', {
          lead: this.doc.name,
          territory: data.territory,
        })
        toast.success('Territory assigned: ' + data.territory)
      },
    })
  }
}
```

### Multi-column meeting notes

```js
class CRMLead {
  capture_meeting() {
    formDialog({
      title: 'Meeting Notes',
      tabs: [
        {
          name: 'main',
          label: '',
          sections: [
            {
              name: 'meeting',
              label: '',
              columns: [
                {
                  name: 'left',
                  fields: [
                    { fieldname: 'meeting_date', fieldtype: 'Date', label: 'Date', reqd: 1 },
                    { fieldname: 'attendees', fieldtype: 'Small Text', label: 'Attendees' },
                  ],
                },
                {
                  name: 'right',
                  fields: [
                    { fieldname: 'outcome', fieldtype: 'Select', label: 'Outcome', options: 'Positive\nNeutral\nNegative', reqd: 1 },
                    { fieldname: 'follow_up', fieldtype: 'Date', label: 'Follow Up' },
                  ],
                },
              ],
            },
            {
              name: 'notes_sec',
              label: 'Notes',
              columns: [
                {
                  name: 'notes_col',
                  fields: [
                    { fieldname: 'notes', fieldtype: 'Text', label: 'Meeting Notes' },
                  ],
                },
              ],
            },
          ],
        },
      ],
      onSubmit: async (data) => {
        await call('crm.api.lead.save_meeting', { lead: this.doc.name, ...data })
        toast.success('Meeting notes saved')
      },
    })
  }
}
```

### Dynamic select options from server

```js
class CRMDeal {
  async change_pipeline() {
    const pipelines = await call('crm.api.get_pipelines')
    formDialog({
      title: 'Change Pipeline',
      fields: [
        {
          fieldname: 'pipeline',
          fieldtype: 'Select',
          label: 'Pipeline',
          options: pipelines.join('\n'),
          reqd: 1,
        },
      ],
      onSubmit: (data) => {
        this.doc.pipeline = data.pipeline
        toast.success('Pipeline changed to ' + data.pipeline)
      },
    })
  }
}
```

---

## Layout Structure Reference

```
tabs[]                          — Array of tab objects
  ├── name: string              — Unique identifier
  ├── label: string             — Tab label (empty = hidden tab bar)
  └── sections[]
        ├── name: string
        ├── label: string       — Section heading (empty = no heading)
        ├── collapsible: bool
        ├── opened: bool
        ├── hideLabel: bool
        ├── hideBorder: bool
        └── columns[]
              ├── name: string
              ├── label: string
              └── fields[]
                    ├── fieldname: string
                    ├── fieldtype: string
                    ├── label: string
                    ├── options: string
                    ├── reqd: 1|0
                    ├── read_only: 1|0
                    ├── hidden: 1|0
                    ├── description: string
                    └── ... (any DocField property)
```

**Columns render side-by-side.** Two columns = two-column layout. Three = three-column. One = full width.

---

## How It Works

1. `formDialog(options)` pushes a config to a reactive array and returns a Promise
2. `FieldLayoutDialogContainer.vue` (in `GlobalModals.vue`) renders a `FieldLayoutDialog` for each entry
3. `FieldLayoutDialog.vue` creates a local `reactive({})` doc and mounts `<FieldLayout>` in standalone mode (via `context` prop — no `useDocument`, no script loading, no cache pollution)
4. On submit: validates → calls `onSubmit` if provided → closes → Promise resolves with data
5. On cancel: calls `onCancel` if provided → Promise resolves with `null`
6. If `onSubmit` throws: dialog stays open, error is shown inline
7. The local doc is garbage-collected on unmount — nothing persists
