import { call } from 'frappe-ui'
import { reactive, ref } from 'vue'

const show = ref(false)
const note = ref(null)
const onEdit = ref(null)

const linkedDocs = {
  'CRM Lead': {
    label: __('Lead'),
    route: 'Lead',
    param: 'leadId',
    titleField: 'lead_name',
  },
  'CRM Deal': {
    label: __('Deal'),
    route: 'Deal',
    param: 'dealId',
    titleField: 'organization',
  },
}

// names of the leads and deals notes belong to, keyed by "doctype:name"
const linkedTitles = reactive({})

function openNote(_note, { edit = null } = {}) {
  note.value = _note
  onEdit.value = edit
  show.value = true
}

function noteLink(name) {
  return `${window.location.origin}/crm/notes/view/list?open=${name}`
}

async function loadLinkedTitles(notes) {
  for (const [doctype, { titleField }] of Object.entries(linkedDocs)) {
    const names = [
      ...new Set(
        (notes || [])
          .filter((n) => n.reference_doctype === doctype && n.reference_docname)
          .map((n) => n.reference_docname)
          .filter((name) => !(`${doctype}:${name}` in linkedTitles)),
      ),
    ]
    if (!names.length) continue
    const docs = await call('frappe.client.get_list', {
      doctype,
      filters: { name: ['in', names] },
      fields: ['name', titleField],
      limit_page_length: names.length,
    })
    for (const d of docs) linkedTitles[`${doctype}:${d.name}`] = d[titleField]
  }
}

function linkedRoute(note) {
  const linked = linkedDocs[note?.reference_doctype]
  if (!linked || !note.reference_docname) return null
  return {
    name: linked.route,
    params: { [linked.param]: note.reference_docname },
    hash: '#notes',
  }
}

function linkedLabel(note) {
  const title =
    linkedTitles[`${note.reference_doctype}:${note.reference_docname}`]
  return `${linkedDocs[note.reference_doctype].label} · ${title || note.reference_docname}`
}

export function useNoteView() {
  return {
    show,
    note,
    onEdit,
    openNote,
    noteLink,
    loadLinkedTitles,
    linkedRoute,
    linkedLabel,
  }
}
