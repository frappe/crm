# Form Scripts on desk v2

A CRM Form Script runs only on CRM v1, at `/crm`. CRM on desk v2, at `/apps/crm`, does not run it. On desk v2, a script for a record page is a `Client Script` row with `view = Record`. This guide turns a CRM Form Script into that row, one v1 call at a time.

The reference for every `page` verb in this guide is [Writing a Client Script for the record page](https://github.com/frappe/frappe/blob/desk-v2/frontend/SCRIPTING.md) (`SCRIPTING.md`).

## How to read the report

The report is the CRM Form Script list at `/apps/crm/crm-form-script` on your site: `https://<your site>/apps/crm/crm-form-script`. A System Manager can open it. Each row shows these columns:

- **Shape**: `Class-based`, `setupForm`, `setupList` or `Unknown`. The three shapes have a worked rewrite below. `Unknown` means the script matches no v1 shape. CRM v1 cannot run it either.
- **Doctype**, **View** and **Enabled**: the row's own fields.
- **Status**: what to do with the script.
  - **Rewrite**: every call has a desk v2 counterpart.
  - **Rewrite: has calls with no counterpart**: some calls cannot port. Their sections say what to do.
  - **Unknown shape**: read the script yourself. Its calls can still have sections here.
  - **Ported by CRM**: the row is one of CRM's standard scripts. CRM ships its own rewrite, so you do nothing.

Open a row to see its **V1 Calls** section. It lists each call with its line, the v1 call, the desk v2 verb or **No counterpart**, and a link to its section in this guide. A call with no counterpart also links its gap: the issue or the map that tracks it.

## How a rewrite and its v1 row live side by side

Keep the v1 row until the cutover. CRM v1 at `/crm` keeps running it, and desk v2 never reads it. The rewrite is a new row. CRM v1 does not run a `Client Script` row with `view = Record`, so the two rows do not clash.

To add the rewrite:

1. Open the `Client Script` list on `/apps/desk`.
2. Make a new row.
3. Set **DocType** to the v1 row's doctype, for example `CRM Deal`.
4. Set **View** to `Record`.
5. Paste the rewrite into **Script**, and turn on **Enabled**.
6. Save. A bad module or template stops the save and names its line.
7. Open a record of that doctype on `/apps/crm`, and check that the rewrite does its v1 job.

A `view = Record` script runs on its doctype in every app, `/apps/desk` too. To limit it to CRM, start each handler with `if (page.app !== 'crm') return`.

## What changes in every script

These rules apply to every call below:

- **One module, one object.** A rewrite is an ES module. Its default export is one object of handlers, keyed by event or by fieldname.
- **`this` becomes `page`.** Every handler gets `page` as its first argument. `this.doc` is `page.doc`, the draft. `page.saved` is the record as the server last showed it.
- **No bare helpers.** `call`, `toast`, `createDialog` and the rest are members of `page`. A plain function in the module gets `page` as an argument.
- **Draw in `onRefresh`.** The page clears every surface and runs `onRefresh` again on each replay. An action or a field change that v1 sets once in `onLoad` goes in `onRefresh`. A conditional change is a plain `if`, with no `else` to undo it.
- **Imports.** A stored script imports by bare name from `vue`, `vue-router`, `frappe-ui`, `@framework/ui` and `frappe/i18n`.

## Worked rewrites

Each rewrite starts from one fixture in `crm/tests/form_scripts/`. The fixture is the v1 row's script.

### A class-based script

The v1 row is a `CRM Form Script` on `CRM Deal`, view `Form`, with a `CRMDeal` class and a `CRMProducts` child class: [`class_crm_deal.js`](../crm/tests/form_scripts/class_crm_deal.js).

The rewrite is a `Client Script` on `CRM Deal`, view `Record`:

```js
import { h } from 'vue'
import { Button } from 'frappe-ui'
import { __ } from 'frappe/i18n'

async function updateProbability(page) {
  const status = await page.call('frappe.client.get_value', {
    doctype: 'CRM Deal Status',
    fieldname: 'probability',
    filters: { name: page.doc.status },
  })
  page.doc.probability = status.probability
}

function updateTotal(page) {
  page.doc.total = page.rows('products').reduce((total, row) => total + (row.amount || 0), 0)
  page.doc.net_total = page.doc.total
}

const NextStep = {
  components: { Button },
  props: { nextStep: String, close: Function },
  template: `
    <div class="flex flex-col gap-4">
      <p class="text-base text-ink-gray-8">{{ nextStep || __('No next step yet') }}</p>
      <Button variant="solid" :label="__('Close')" @click="close()" />
    </div>
  `,
}

function showNextStep(page) {
  page.dialog.open(NextStep, { nextStep: page.doc.next_step }, { title: __('Next step') })
}

async function editNextStep(page) {
  const label = page.meta.fields.find((field) => field.fieldname === 'next_step').label
  const values = await page.dialog.form({
    title: __('Edit next step'),
    fields: [{ fieldname: 'next_step', fieldtype: 'Data', label }],
    defaults: { next_step: page.doc.next_step },
  })
  if (values) page.doc.next_step = values.next_step
}

function openList(page, doctype) {
  const { params } = page.router.currentRoute.value
  page.router.push({ name: 'list', params: { ...params, doctype } })
}

const Summary = {
  props: { page: Object },
  render() {
    return h('p', { class: 'p-4 text-base text-ink-gray-8' }, this.page.doc.next_step)
  },
}

const WonNote = {
  template: `<p class="text-base text-ink-gray-8">{{ __('Deal won') }}</p>`,
}

export default {
  onRefresh(page) {
    if (page.isNew) return
    page.header.add(
      [
        { name: 'refresh_probability', label: __('Refresh probability'), display: 'button', run: updateProbability },
        { name: 'more', label: __('More'), display: 'dropdown' },
        { name: 'show_next_step', label: __('Show next step'), group: 'more', run: showNextStep },
        { name: 'edit_next_step', label: __('Edit next step'), group: 'more', run: editNextStep },
        { name: 'open_settings', label: __('Open settings'), group: 'more', run: (page) => page.openSettings('crm', 'general') },
        { name: 'all_leads', label: __('All leads'), group: 'more', run: (page) => openList(page, 'crm-lead') },
      ],
      { before: 'save' },
    )
    page.tabs.add({ name: 'summary', label: __('Summary'), component: Summary })

    if (!page.doc.probability) page.fields.hide('next_step')
    page.form.update('details_section', { label: __('Deal details') })
    page.panelSections.update('organization_section', { opened: true })
    page.form.tabs.update('first_tab', { label: __('Overview') })
    page.fields.update('probability', { description: __('Set from the status') })
    page.fields.hide('products.discount_percentage')
    if (page.doc.status === 'Won') page.fields.update('next_step', { component: WonNote })
  },

  async beforeSave(page) {
    if (page.fields.get('probability').reqd && !page.doc.probability) {
      throw new Error(__('Set a probability'))
    }
    if (page.doc.status !== page.saved.status) await updateProbability(page)
  },

  afterSave(page) {
    page.toast.success(__('Deal saved'))
  },

  status: updateProbability,

  probability(page) {
    if (page.doc.probability > 100) page.toast.error(__('Probability cannot be above 100'))
  },

  products: {
    onAdd(page, row) {
      row.qty = row.qty || 1
      row.trigger('qty')
    },
    onRemove(page) {
      page.toast.success(__('{0} products left', [page.rows('products').length]))
      updateTotal(page)
    },
    qty(page, row) {
      row.amount = row.qty * row.rate
      updateTotal(page)
    },
  },
}
```

What changed, and why:

- `status(page)` runs only when the reader changes the Status field in the form. The status control in CRM's header saves a pick as a script write, and a script write runs no field handler. To react to every status change, `beforeSave` compares the status with `page.saved.status`. A header pick saves, so `beforeSave` updates the probability for it too.
- The class methods `updateProbability`, `updateTotal`, `showNextStep` and `editNextStep` are plain functions. `this.doc.trigger('updateProbability')` and `this.showNextStep()` call them with `page`.
- The actions and the tab moved from `onLoad` to `onRefresh`, because each replay clears the header and the tabs.
- `hideLabel: true` has no desk v2 key. The **More** dropdown shows its label.
- `this.setFieldProperty('status', 'button_color', 'green')` is gone. `status` is a Link field, and `button_color` colors only a Button field, so the line does nothing on CRM v1 either.
- `this.removeFieldProperty('next_step', 'hidden')` is gone. The condition in `onRefresh` decides on each replay.
- The `typeof h === 'function'` check is gone. The rewrite imports `h` from `vue`.
- The v1 route names, `{ name: 'Leads' }`, do not exist on desk v2. `openList` builds the list route from the current route's params.

### A legacy `setupForm` script

The v1 row is a `CRM Form Script` on `CRM Lead`, view `Form`, with a `setupForm` function: [`setup_form_crm_lead.js`](../crm/tests/form_scripts/setup_form_crm_lead.js).

The rewrite is a `Client Script` on `CRM Lead`, view `Record`:

```js
import { __ } from 'frappe/i18n'

async function checkEmail(page) {
  const count = await page.call('frappe.client.get_count', {
    doctype: 'CRM Lead',
    filters: { email: page.doc.email, name: ['!=', page.doc.name] },
  })
  if (count) page.toast.error(__('Another lead has this email'))
  else page.toast.success(__('No other lead has this email'))
}

async function markAsContacted(page) {
  page.doc.status = 'Contacted'
  await page.save()
  page.toast.success(__('Lead marked as contacted'))
}

function openList(page, doctype) {
  const { params } = page.router.currentRoute.value
  page.router.push({ name: 'list', params: { ...params, doctype } })
}

export default {
  onRefresh(page) {
    if (page.isNew) return
    page.header.add(
      [
        { name: 'mark_as_contacted', label: __('Mark as contacted'), display: 'button', run: markAsContacted },
        { name: 'more', label: __('More'), display: 'dropdown' },
        { name: 'check_email', label: __('Check email'), group: 'more', run: checkEmail },
        { name: 'all_deals', label: __('All deals'), group: 'more', run: (page) => openList(page, 'crm-deal') },
        { name: 'delete_lead', label: __('Delete'), group: 'more', run: (page) => page.run('header.delete') },
      ],
      { before: 'save' },
    )
  },
}
```

What changed, and why:

- The function's arguments are `page` members: `doc` is `page.doc`, `call` is `page.call`, `toast` is `page.toast`, `router` is `page.router`.
- The returned `actions` are `page.header.add` calls in `onRefresh`.
- `updateField('status', 'Contacted')` saves one field at once. The rewrite sets the field, then calls `page.save()`. The save also sends the reader's other unsaved edits.
- The `$dialog` and `deleteDoc()` pair is `page.run('header.delete')`. The built-in delete asks the reader first, then opens the list.

### A `setupList` script

The v1 row is a `CRM Form Script` on `CRM Lead`, view `List`, with a `setupList` function: [`setup_list_crm_lead.js`](../crm/tests/form_scripts/setup_list_crm_lead.js).

**This script cannot port yet.** Desk v2 has no list script. A script cannot add a list action or a bulk action. That gap is G6, the list beyond columns, on map 4 of [CRM on desk v2 — the build maps and their order](https://github.com/frappe/frappe/issues/45839).

Keep the v1 row. CRM v1 keeps running it on `/crm`. Make no `Client Script` row for it. When map 4 gives the list a script surface, this section gets the rewrite.

## Calls in the order public scripts use them

This order comes from [Research: which v1 calls real CRM Form Scripts use](https://github.com/frappe/frappe/issues/45965). The most used call comes first.

<a id="call"></a>
### `call(method, params)`

**Desk v2:** `page.call(method, params)`. It resolves with what the method returns, as v1 does. `this.call` is the same call.

```js
const count = await page.call('frappe.client.get_count', { doctype: 'CRM Lead' })
```

To read server data in `onRefresh`, wrap the call in `page.cached(key, fetcher)`. It returns `undefined` until the fetch lands, then the page replays with the value.

Read `page.cached` before the handler's first `await`, in `onRefresh` and in a field handler too. After an `await`, the page cannot tell which script asks for the value.

<a id="dom-access"></a>
### DOM access: `document.`, `querySelector`, `MutationObserver`

**No counterpart, by design.** Desk v2 gives a script surfaces and verbs, not the DOM. Its markup differs from CRM v1's, so a selector from v1 finds nothing.

Do the job with a verb or a component instead:

- To hide a button, a section or a field, use `page.header.hide`, `page.form.hide`, `page.panelSections.hide` or `page.fields.hide`.
- To add a button, use `page.header.add`.
- To draw your own markup in a field's place, give the field a component:

```js
const Score = {
  props: { page: Object },
  template: `<p class="text-base text-ink-gray-8">{{ page.doc.probability }}%</p>`,
}

export default {
  onRefresh(page) {
    page.fields.update('probability', { component: Score })
  },
}
```

- To draw markup in the side panel, add a panel section with `page.panelSections.add({ name, label, component })`.

<a id="legacy-doc"></a>
### `doc` (legacy `setupForm`)

**Desk v2:** `page.doc`. It is the draft. A write to it marks the record dirty, and **Save** sends it.

<a id="header-actions"></a>
### `this.actions`, legacy `return { actions }`

**Desk v2:** `page.header.add({ name, label, display: 'button', run })` in `onRefresh`.

```js
export default {
  onRefresh(page) {
    page.header.add({ name: 'refresh', label: 'Refresh', display: 'button', run: (page) => page.reload() }, { before: 'save' })
  },
}
```

- Each item needs a `name`. Other verbs use it: `page.header.hide('refresh')`.
- Without `display`, the item is an entry in the `⋯` menu.
- The right zone keeps three controls, `Save` among them. Extra buttons move into `⋯` from the end.
- Without a position, a new item comes after `Save`. Use `{ before: 'save' }` to put it on the left of `Save`.
- v1 sets `this.actions` once, in `onLoad`. Desk v2 clears the header on each replay, so add the items in `onRefresh`.

<a id="toast-error"></a>
### `toast.error`

**Desk v2:** `page.toast.error(message)`. `this.toast.error` is the same call.

<a id="toast-success"></a>
### `toast.success`

**Desk v2:** `page.toast.success(message)`. `this.toast.success` is the same call.

<a id="on-render"></a>
### `onRender()`, aliases `on_render` and `refresh`

**Desk v2:** `onRefresh(page)`. It runs on every replay: on load, after a save, and when a field changes. Each replay starts from a clean page, so state each change as a plain `if`.

```js
export default {
  onRefresh(page) {
    if (page.doc.status === 'Won') page.header.hide('save')
  },
}
```

Keep `onRefresh` synchronous. To read server data, use `page.cached`, as in [`call`](#call).

<a id="this-method-call"></a>
### `this.<method>()`

**Desk v2:** a plain function in the module. Pass it `page`.

```js
function updateTotal(page) {
  page.doc.total = page.rows('products').reduce((total, row) => total + (row.amount || 0), 0)
}

export default {
  products: { onRemove: updateTotal },
}
```

<a id="create-dialog"></a>
### `createDialog(options)`, legacy `$dialog`

**Desk v2:** `page.dialog.confirm(options)`, or `page.dialog.danger(options)` for a red, destructive one. Each resolves `true` when the reader confirms, and `null` when they dismiss it.

```js
const confirmed = await page.dialog.danger({ title: 'Close deal', message: 'Close this deal?' })
if (!confirmed) return
```

The options are `title`, `message`, `confirmLabel`, `cancelLabel`, `theme`, `icon`, `size`, `onConfirm`, `onCancel` and `actions`. A v1 action's `onClick({ close })` is an action's `onClick(control)`, and `control.close()` closes the dialog. The verb drops an option it does not name, `html` among them: see [`createDialog({ html })`](#create-dialog-html).

<a id="create-dialog-html"></a>
### `createDialog({ html })`

**Desk v2:** `page.dialog.open(component, props, { title })`. No dialog verb takes HTML, so a component draws the body. The component gets your `props` and a `close` function.

```js
const Body = {
  props: { text: String, close: Function },
  template: `<p class="text-base text-ink-gray-8" @click="close()">{{ text }}</p>`,
}

page.dialog.open(Body, { text: page.doc.next_step }, { title: 'Next step' })
```

<a id="translate"></a>
### `__()`

**Desk v2:** `import { __ } from 'frappe/i18n'` at the top of the module. Inside a component's `template:` string, `__` needs no import.

<a id="form-dialog"></a>
### `formDialog(options)`

**Desk v2:** `page.dialog.form(options)`. It takes the same option names: `title`, `fields`, `tabs`, `doctype`, `fieldnames`, `defaults`, `required`, `size`, `actions`, `onSubmit`, `onCancel`, `submitLabel` and `cancelLabel`. It resolves with the values, keyed by fieldname, or `null` when the reader dismisses it.

```js
const values = await page.dialog.form({
  title: 'Edit next step',
  fields: [{ fieldname: 'next_step', fieldtype: 'Data', label: 'Next step' }],
  defaults: { next_step: page.doc.next_step },
})
if (values) page.doc.next_step = values.next_step
```

A field takes fewer keys than in v1: `fieldname`, `fieldtype`, `label`, `options`, `reqd`, `read_only`, `hidden`, `depends_on`, `mandatory_depends_on`, `read_only_depends_on` and `description`.

<a id="toast-info"></a>
### `toast.info`

**No counterpart.** `page.toast` has `success` and `error` only. The gap is [Desk v2: page.toast — info, warning and a plain toast](https://github.com/frappe/frappe/issues/46005).

Until it lands, show a neutral message with `page.toast.success(message)`.

<a id="field-handler"></a>
### A method named like a field: `status()`

**Desk v2:** a key named like the field: `status(page)`. It runs when the reader commits a change to the field, before any save.

```js
async function updateProbability(page) {
  const status = await page.call('frappe.client.get_value', {
    doctype: 'CRM Deal Status',
    fieldname: 'probability',
    filters: { name: page.doc.status },
  })
  page.doc.probability = status.probability
}

export default {
  status: updateProbability,
}
```

A script's own write to a field does not run that field's handler. If the v1 script relies on that, call the function yourself.

On `CRM Deal` and `CRM Lead`, the status control in the header saves a pick as a script write: it writes `status` and saves the record. A script write runs no field handler, so no `status` handler runs. To act on every status change, also compare the status with the saved one in `beforeSave`. A header pick saves, so `beforeSave` runs for it:

```js
export default {
  status: updateProbability,
  async beforeSave(page) {
    if (page.doc.status !== page.saved.status) await updateProbability(page)
  },
}
```

<a id="on-load"></a>
### `onLoad()`, aliases `on_load` and `onload`

**Desk v2:** it depends on what the handler does.

- To draw, such as adding an action, a tab or a field change, use `onRefresh(page)`. Each replay clears what `onOpen` drew.
- To make a one-time move, such as opening a tab or focusing a field, use `onOpen(page)`. It runs once per visit, after the first replay has drawn.

```js
export default {
  onOpen(page) {
    page.fields.focus('next_step')
  },
}
```

v1 runs `onLoad` once while the document stays cached. Desk v2 runs `onOpen` once per visit.

<a id="doc-trigger"></a>
### `this.doc.trigger('method')`

**Desk v2:** a plain function in the module. Call it with `page`: `updateProbability(page)`. See [`this.<method>()`](#this-method-call).

To run a field's own handler, call the function that the field's key holds. To run a child field's handler on a row, use [`row.trigger`](#row-trigger).

<a id="frappe-global"></a>
### `frappe.*`

**No counterpart.** This is the desk v1 API. CRM v1 has no `frappe` global, so this line fails on `/crm` too. Rewrite what the line meant with a `page` verb, or drop it.

<a id="unread-handler"></a>
### `afterSubmit()`, `after_load()` and other handler names

**No counterpart.** CRM v1 never calls a handler by this name, so the code does nothing now. Drop it. If you want it to run, move its body into a desk v2 event: `onRefresh`, `onOpen`, `beforeSave` or `afterSave`.

On desk v2, a key that is not an event is a field handler. A key named `afterSubmit` runs only when a field of that name changes.

<a id="unread-return-key"></a>
### A returned key that CRM v1 never reads: `return { sections }`

**No counterpart.** CRM v1 reads only `actions` and `statuses` from `setupForm`, and only `actions` and `bulk_actions` from `setupList`. Any other key does nothing now. Drop it.

<a id="toast-create"></a>
### `toast.create`, legacy `createToast`

**No counterpart.** `page.toast` has `success` and `error` only, and takes a message, not `{ title, icon, iconClasses }`. The gap is [Desk v2: page.toast — info, warning and a plain toast](https://github.com/frappe/frappe/issues/46005).

Until it lands, pass the title to `page.toast.success(title)`.

<a id="set-field-html"></a>
### `this.setFieldHtml(field, html)`

**Desk v2:** `page.fields.update(field, { component, props })`. No verb takes HTML. A component draws the field, and gets `props` and `page`.

```js
const WonNote = {
  props: { text: String },
  template: `<p class="text-base text-ink-gray-8">{{ text }}</p>`,
}

export default {
  onRefresh(page) {
    if (page.doc.status === 'Won') page.fields.update('next_step', { component: WonNote, props: { text: 'Deal won' } })
  },
}
```

<a id="child-class"></a>
### A child class: `class CRMProducts { ... }`

**Desk v2:** a block under the parent's export, keyed by the Table fieldname. The child doctype's name does not matter.

```js
export default {
  products: {
    qty(page, row) {
      row.amount = row.qty * row.rate
    },
  },
}
```

A rewrite is one module for the parent doctype, `CRM Deal` here. It holds the parent's handlers and the block for each table.

<a id="child-field-handler"></a>
### A child class method: `qty()`

**Desk v2:** a key under the table's block: `products: { qty(page, row) {} }`. It gets the row as its second argument. See [A child class](#child-class).

<a id="on-validate"></a>
### `onValidate()`, aliases `on_validate` and `validate`

**Desk v2:** `beforeSave(page)`. It runs before the page sends the record. A throw stops the save and shows its message.

```js
export default {
  beforeSave(page) {
    if (!page.doc.probability) throw new Error('Set a probability')
  },
}
```

<a id="get-row"></a>
### `this.doc.getRow(table, idx)`, `this.getRow(...)`

**Desk v2:** in a table handler, use the `row` argument. Elsewhere, `page.rows(table)` returns the table's rows as handles, in order.

```js
const first = page.rows('products')[0]
first.qty = 2
```

A handle reads and writes the row's fields by name, and has `trigger`, `setError` and `clearError`.

<a id="router"></a>
### `router` (injected helper)

**Desk v2:** `page.router`, the vue-router instance. The route names differ from CRM v1's, so `{ name: 'Leads' }` finds no route. Build a route from the current one:

```js
const { params } = page.router.currentRoute.value
page.router.push({ name: 'list', params: { ...params, doctype: 'crm-lead' } })
```

<a id="row-add"></a>
### `<table>_add()`

**Desk v2:** `onAdd` under the table's block. It gets the new row.

```js
export default {
  products: {
    onAdd(page, row) {
      row.qty = 1
    },
  },
}
```

A key spelled `products_add` is a field handler for a field of that name, so it never runs.

<a id="row-remove"></a>
### `<table>_remove()`

**Desk v2:** `onRemove` under the table's block. It gets `page` only, because the row is gone.

```js
export default {
  products: {
    onRemove(page) {
      page.doc.total = page.rows('products').reduce((total, row) => total + (row.amount || 0), 0)
    },
  },
}
```

<a id="update-field"></a>
### `updateField(field, value)` (legacy `setupForm`)

**Desk v2:** write the field, then save.

```js
page.doc.status = 'Contacted'
await page.save()
```

`updateField` saves one field. `page.save()` sends the whole draft, the reader's other unsaved edits too.

<a id="action-group"></a>
### An action group: `{ group, items }`, `buttonLabel`

**Desk v2:** add a dropdown, then each member with `group` set to the dropdown's name.

```js
page.header.add({ name: 'more', label: 'More', display: 'dropdown' }, { before: 'save' })
page.header.add({ name: 'quotation', label: 'Quotation', group: 'more', run: createQuotation })
```

`buttonLabel` is the dropdown's `label`. `hideLabel` has no key: the dropdown shows its label.

<a id="throw-error"></a>
### `throwError(message)`

**Desk v2:** `throw new Error(message)` in `beforeSave`. To mark a field as well, throw what `setError` returns:

```js
export default {
  beforeSave(page) {
    if (!page.doc.email) throw page.fields.setError('email', 'Set an email')
  },
}
```

<a id="toast-warning"></a>
### `toast.warning`

**No counterpart.** `page.toast` has `success` and `error` only. The gap is [Desk v2: page.toast — info, warning and a plain toast](https://github.com/frappe/frappe/issues/46005).

Until it lands, show the warning with `page.toast.error(message)`.

<a id="list-actions"></a>
### `setupList`: `return { actions }`

**No counterpart.** A script cannot add a list action yet. The gap is G6, the list beyond columns, on map 4 of [CRM on desk v2 — the build maps and their order](https://github.com/frappe/frappe/issues/45839). Keep the v1 row: see [A `setupList` script](#a-setuplist-script).

<a id="list-bulk-actions"></a>
### `setupList`: `return { bulk_actions }`

**No counterpart.** A script cannot add a bulk action yet. The gap is G6, the list beyond columns, on map 4 of [CRM on desk v2 — the build maps and their order](https://github.com/frappe/frappe/issues/45839). Keep the v1 row.

For one record at a time, a header action on the record page can do the same work. See [`this.actions`](#header-actions).

<a id="new-document"></a>
### `this.doc.__newDocument`

**Desk v2:** `page.isNew`. It is true until the first save.

A new record has a header and a form only: no panel, no Activity and no quick actions.

<a id="on-before-create"></a>
### `onBeforeCreate()`, alias `on_before_create`

**No counterpart in the create dialog.** The dialog runs no handlers.

On the full-page new record, two handlers do the same job:

- To set first values, use `onOpen` with `page.isNew`.
- To check values before the insert, use `beforeSave` with `page.isNew`.

```js
export default {
  onOpen(page) {
    if (page.isNew) page.doc.priority = 'High'
  },
}
```

<a id="row-trigger"></a>
### `row.trigger('field')`

**Desk v2:** `row.trigger('field')`, the same call. It runs the row's handler for that child field, such as `products.qty`.

<a id="set-field-property"></a>
### `this.setFieldProperty(field, prop, value)`

**Desk v2:** `page.fields.update(field, { [prop]: value })`, or `page.fields.hide(field)` and `page.fields.show(field)`. Put it in `onRefresh`, under a plain `if`.

```js
export default {
  onRefresh(page) {
    if (!page.doc.probability) page.fields.hide('next_step')
    page.fields.update('status', { link_filters: { type: 'Open' } })
  },
}
```

`update` takes `label`, `placeholder`, `description`, `hidden`, `read_only`, `reqd`, `options`, `link_filters`, `precision`, `cannot_add_rows`, `cannot_delete_rows`, `component` and `props`. One change reaches the form and the side panel. For a section, a panel section, a tab, a child column or one row, see the sections below.

<a id="this-old-value"></a>
### `this.oldValue`

**No counterpart.** Desk v2 does not keep the value from before the edit. `page.saved.<field>` is the last saved value, which can be older.

<a id="this-value"></a>
### `this.value`

**Desk v2:** `page.doc.<field>` in a field handler. In a table handler, read `row.<field>`.

## Calls no public script uses

The research found no public script that uses these calls. They follow the order of the catalog.

<a id="on-save"></a>
### `onSave()`, alias `on_save`

**Desk v2:** `afterSave(page)`. It runs only after the server accepts the save.

<a id="on-error"></a>
### `onError()`, alias `on_error`

**No counterpart.** No handler runs on a failed save. The page shows the server's message and marks the fields it names.

<a id="on-create-lead"></a>
### `onCreateLead()`, alias `on_create_lead`

**No counterpart.** CRM on desk v2 has no hook for it, because no public script uses it.

For server work when the lead is made, use a Server Script with the DocType Event **After Insert** on `CRM Lead`.

<a id="convert-to-deal"></a>
### `convertToDeal()`, alias `convert_to_deal`

**No counterpart.** CRM on desk v2 has no hook for it, because no public script uses it.

For server work when the deal is made, use a Server Script with the DocType Event **After Insert** on `CRM Deal`.

<a id="current-row-idx"></a>
### `this.currentRowIdx`

**Desk v2:** the `row` argument of a table handler. See [`this.doc.getRow`](#get-row).

<a id="remaining-rows"></a>
### `this.rows` in `<table>_remove()`

**Desk v2:** `page.rows(table)` in `onRemove`. It returns the rows that are left.

<a id="removed-rows"></a>
### `this.selectedRows` in `<table>_remove()`

**No counterpart.** `onRemove` does not get the removed rows. To find the rows removed since the last save, compare `page.rows(table)` with `page.saved[table]`.

<a id="button-field-method"></a>
### A method named like a Button field

**Desk v2:** a key named like the Button field: `send_quote(page)`. A click on the Button runs it. A read-only Button is disabled. A Button in a child table's row runs nothing yet.

```js
export default {
  async send_quote(page) {
    await page.call('my_app.api.send_quote', { deal: page.docname })
  },
}
```

<a id="action-on-click"></a>
### `onClick` on an action

**Desk v2:** `run(page, value)` on the header item. It gets `page`, so it does not need `this` or a closure.

<a id="statuses"></a>
### `this.statuses`, legacy `return { statuses }`

**No counterpart.** CRM on desk v2 has no hook for it, because no public script uses it.

`page.fields.update('status', { link_filters })` narrows the search of a Link field. It is not the same control as CRM v1's status dropdown.

<a id="field-props"></a>
### `setFieldProperty` with `button_color`

**Desk v2:** `page.fields.update(field, { props })`. The props bind onto the field's control. For a Button field, give frappe-ui Button props:

```js
page.fields.update('send_quote', { props: { theme: 'green', variant: 'solid' } })
```

`button_color` colors only a Button field on CRM v1. On another field, drop the line.

<a id="section-property"></a>
### `setFieldProperty` on a Details section

**Desk v2:** `page.form.hide(name)`, `page.form.show(name)` and `page.form.update(name, { label })`. The name is the section's name in the Form Layout.

```js
page.form.update('details_section', { label: 'Deal details' })
```

A section takes `label` only. `collapsible`, `opened`, `hideLabel` and `hideBorder` have no verb.

<a id="panel-section-property"></a>
### `setFieldProperty` on a Side Panel section

**Desk v2:** `page.panelSections.hide(name)`, `show(name)` and `update(name, { label, opened })`. To open or close a section once, use `page.panelSections.open(name)` or `close(name)` in `onOpen`.

```js
page.panelSections.update('organization_section', { opened: true })
```

<a id="tab-property"></a>
### `setFieldProperty` on a tab

**Desk v2:** `page.form.tabs.hide(name)`, `show(name)` and `update(name, { label })`, for the tabs of the Details form.

```js
page.form.tabs.update('first_tab', { label: 'Overview' })
```

<a id="child-column-property"></a>
### `setFieldProperty('table.column', ...)`

**Desk v2:** `page.fields` names a child column by its table, `'<table>.<column>'`. `hide`, `show`, `update`, `has` and `get` take that name, with the keys of a field. One change reaches every row: the grid, and the row's form.

```js
page.fields.hide('products.discount_percentage')
```

`hidden` takes the column out of the grid. `show` does not add a column to the grid: the child's **In List View** fields pick its columns. A change for one row has no verb: see [one row](#row-property).

<a id="row-property"></a>
### `setFieldProperty(..., rowName)`, one row

**No counterpart.** A field change reaches every row. Only an error is per row: `row.setError(field, message)` in a table handler.

<a id="set-field-properties"></a>
### `this.setFieldProperties(field, {...})`

**Desk v2:** `page.fields.update(field, {...})`, with the keys listed under [`setFieldProperty`](#set-field-property).

<a id="remove-field-property"></a>
### `this.removeFieldProperty(...)`

**Desk v2:** nothing to call. Each replay clears every field change. State the condition in `onRefresh`, and the change holds only while the condition is true.

<a id="get-field"></a>
### `this.getField(field)`

**Desk v2:** `page.fields.get(field)`. It returns the field as it is now, with script changes and `depends_on` applied. It is read-only.

<a id="get-meta"></a>
### `this.getMeta(doctype)`

**Desk v2:** `page.meta`, for the record's own doctype only. Another doctype's meta has no verb.

```js
const label = page.meta.fields.find((field) => field.fieldname === 'next_step').label
```

<a id="tabs"></a>
### `this.tabs` (CRM develop)

**Desk v2:** `page.tabs.add({ name, label, component })` in `onRefresh`. The component gets `page` as a prop.

```js
const Summary = {
  props: { page: Object },
  template: `<p class="p-4 text-base text-ink-gray-8">{{ page.doc.next_step }}</p>`,
}

export default {
  onRefresh(page) {
    page.tabs.add({ name: 'summary', label: 'Summary', component: Summary })
  },
}
```

<a id="toast-callable"></a>
### `toast(message)` (CRM develop)

**No counterpart.** `page.toast` is not callable. The gap is [Desk v2: page.toast — info, warning and a plain toast](https://github.com/frappe/frappe/issues/46005).

Until it lands, use `page.toast.success(message)`.

<a id="router-previous-route"></a>
### `router.previousRoute`

**No counterpart.** It is a CRM v1 addition to the router. To go back, use `page.router.back()`.

<a id="socket"></a>
### `socket`, legacy `$socket`

**No counterpart.** A script gets no socket.

<a id="make-phone-call"></a>
### `crm.makePhoneCall(number)`

**No counterpart yet.** Map 5 of [CRM on desk v2 — the build maps and their order](https://github.com/frappe/frappe/issues/45839) adds the act `shell.crm.make_a_call`. Until then, a script cannot start a call.

<a id="open-settings"></a>
### `crm.openSettings(page)`

**Desk v2:** `page.openSettings(prefix, pane, block)`. It opens the settings dialog at `#settings/<prefix>/<pane>/<block>`. Each argument is optional. CRM's prefix is `crm`, and v1's `General` pane is `general`:

```js
page.openSettings('crm', 'general')
```

<a id="h-helper"></a>
### `h()` (CRM develop)

**Desk v2:** `import { h } from 'vue'`. Use it in a component's `render` function. A `template:` string is often easier to read.

```js
import { h } from 'vue'

const Note = {
  props: { page: Object },
  render() {
    return h('p', { class: 'text-base text-ink-gray-8' }, this.page.doc.next_step)
  },
}
```

<a id="delete-doc"></a>
### `deleteDoc()` (legacy `setupForm`)

**Desk v2:** `page.run('header.delete')`. It runs the built-in delete, which asks the reader first, then opens the list.
