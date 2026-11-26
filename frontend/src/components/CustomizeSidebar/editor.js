import { sidebarItems } from '@/stores/sidebar'
import { call, dialog, frappeRequest, toast } from 'frappe-ui'
import { computed, reactive } from 'vue'
import * as Rows from './rows'

const SCOPED_FIELDS = {
  selected: null,
  adding: null,
  refusal: null,
  opensRefusal: null,
  error: null,
  stale: false,
  resetNote: false,
}

/** The Customize sidebar dialog: one layer at a time, edited as a draft and saved whole. */
export const editor = reactive({
  open: false,
  loading: false,
  saving: false,
  scope: 'user',
  canEditSite: false,
  builtInDoctypes: {},
  modified: null,
  opened: [],
  rows: [],
  below: [],
  showHidden: false,
  ...SCOPED_FIELDS,
})

export const changed = computed(() =>
  Rows.isChanged(editor.opened, editor.rows),
)
export const current = computed(() => Rows.find(editor.rows, editor.selected))

export async function openEditor() {
  Object.assign(editor, { open: true, showHidden: false })
  await load('user')
}

export async function switchTo(scope) {
  if (changed.value || scope === editor.scope) return
  if (scope === 'site' && !editor.canEditSite) return
  await load(scope)
}

async function load(scope) {
  editor.loading = true
  try {
    const layer = await frappeRequest({
      url: '/api/method/crm.api.sidebar.get_sidebar_layer',
      method: 'GET',
      params: { scope },
    })
    applyLayer(layer)
  } finally {
    editor.loading = false
  }
}

function applyLayer(layer) {
  Object.assign(editor, {
    ...SCOPED_FIELDS,
    scope: layer.scope,
    canEditSite: layer.can_edit_site,
    builtInDoctypes: layer.built_in_doctypes,
    modified: layer.modified,
    opened: layer.items,
    rows: layer.items,
    below: layer.below,
  })
}

export function choose(key) {
  Object.assign(editor, {
    selected: key,
    adding: null,
    refusal: null,
    opensRefusal: null,
  })
}

let adds = 0
export function startAdding(type) {
  Object.assign(editor, {
    adding: { type, id: ++adds },
    refusal: null,
  })
}

/** Apply an edit; a refusal is shown under the fields and leaves the draft as it was. */
function apply(next) {
  if (typeof next === 'string') {
    editor.refusal = next
    return false
  }
  editor.rows = next
  editor.refusal = null
  return true
}

export function update(fields) {
  apply(
    Rows.update(
      editor.rows,
      editor.selected,
      fields,
      editor.scope,
      editor.below,
    ),
  )
}

export function toggleHidden() {
  const key = editor.selected
  if (!apply(Rows.toggleHidden(editor.rows, key))) return
  if (Rows.find(editor.rows, key).hidden && !editor.showHidden)
    editor.selected = null
}

export function nest(parentKey) {
  apply(Rows.nest(editor.rows, editor.selected, parentKey))
}

export function moveBy(key, by) {
  const isShown = (row) => Rows.isListed(editor.rows, row, editor.showHidden)
  choose(key)
  apply(Rows.moveBy(editor.rows, key, by, isShown))
}

export function drop(key, onKey) {
  choose(key)
  apply(Rows.drop(editor.rows, key, onKey))
}

export function remove() {
  if (apply(Rows.remove(editor.rows, editor.selected, editor.scope))) {
    editor.selected = null
  }
}

/** Point a DocType row this layer added at another DocType, with the same rules as Add. */
export function changeDoctype(doctype) {
  const row = current.value
  if (!doctype || !row || row.link_to === doctype) return
  editor.opensRefusal = Rows.doctypeRefusal(
    editor.rows,
    doctype,
    editor.builtInDoctypes,
    row.key,
  )
  if (editor.opensRefusal) return
  const label = row.label === row.link_to ? doctype : row.label
  apply(
    Rows.update(
      editor.rows,
      row.key,
      { link_to: doctype, label },
      editor.scope,
    ),
  )
}

export function addDoctype(doctype) {
  const refusal = Rows.doctypeRefusal(
    editor.rows,
    doctype,
    editor.builtInDoctypes,
  )
  if (refusal) return (editor.refusal = refusal)
  const section = Rows.isCustomSection(current.value) ? current.value.key : null
  const row = {
    key: Rows.newKey(editor.scope),
    type: 'Link',
    label: doctype,
    link_type: 'DocType',
    link_to: doctype,
  }
  if (apply(Rows.add(editor.rows, row, section))) finishAdding(row.key)
}

export function addSection(label, collapsible, keepClosed) {
  const row = {
    key: Rows.newKey(editor.scope),
    type: 'Section',
    label: label.trim(),
    collapsible: collapsible ? 1 : 0,
    keep_closed: collapsible && keepClosed ? 1 : 0,
  }
  if (apply(Rows.add(editor.rows, row))) finishAdding(row.key)
}

function finishAdding(key) {
  Object.assign(editor, { adding: null, selected: key })
}

export function resetToDefault() {
  editor.rows = Rows.resetToDefault(editor.rows, editor.below, editor.scope)
  Object.assign(editor, {
    selected: null,
    adding: null,
    refusal: null,
    resetNote: true,
  })
}

export function discard() {
  editor.rows = editor.opened
  Object.assign(editor, SCOPED_FIELDS)
}

export async function save() {
  editor.saving = true
  try {
    const saved = await call('crm.api.sidebar.save_sidebar_layer', {
      scope: editor.scope,
      items: Rows.toPayload(editor.rows),
      modified: editor.modified,
    })
    sidebarItems.value = saved.sidebar
    editor.open = false
    toast.success(
      editor.scope === 'site'
        ? __('Sidebar saved for everyone')
        : __('Sidebar saved for you'),
    )
  } catch (error) {
    editor.stale = error.exc_type === 'TimestampMismatchError'
    editor.error = error.messages?.[0] || error.message
  } finally {
    editor.saving = false
  }
}

export function cancel() {
  if (!changed.value) return (editor.open = false)
  askToDiscard(
    __('Closing drops the edits you made. Nothing you changed is saved.'),
    __('Discard and close'),
    () => (editor.open = false),
  )
}

export function reload() {
  const fresh = () => load(editor.scope)
  if (!changed.value) return fresh()
  askToDiscard(
    __('Reloading drops the edits you made. Nothing you changed is saved.'),
    __('Discard and reload'),
    fresh,
  )
}

function askToDiscard(message, label, then) {
  dialog.confirm({
    title: __('Discard your changes?'),
    message,
    confirmLabel: label,
    cancelLabel: __('Keep editing'),
    theme: 'red',
    onConfirm: then,
  })
}

export async function searchDoctypes(txt) {
  return frappeRequest({
    url: '/api/method/crm.api.sidebar.search_sidebar_doctypes',
    method: 'GET',
    params: { txt },
  })
}
