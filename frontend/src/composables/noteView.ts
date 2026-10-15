import { call } from 'frappe-ui'
import { reactive, ref } from 'vue'

export interface NoteRef {
  name: string
  title?: string
  content?: string
  owner?: string
  modified?: string
  reference_doctype?: string
  reference_docname?: string
}

type LinkedDoctype = 'CRM Lead' | 'CRM Deal'

interface LinkedDoc {
  label: string
  route: string
  param: string
  titleField: string
}

const show = ref(false)
const note = ref<NoteRef | null>(null)
const onEdit = ref<(() => void) | null>(null)

const linkedDocs: Record<LinkedDoctype, LinkedDoc> = {
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
const linkedTitles = reactive<Record<string, string>>({})

function linkedDoc(note?: NoteRef | null): LinkedDoc | undefined {
  return linkedDocs[note?.reference_doctype as LinkedDoctype]
}

function openNote(
  _note: NoteRef,
  { edit = null }: { edit?: (() => void) | null } = {},
) {
  note.value = _note
  onEdit.value = edit
  show.value = true
}

function noteLink(name: string): string {
  return `${window.location.origin}/crm/notes/view/list?open=${name}`
}

async function loadLinkedTitles(notes?: NoteRef[] | null) {
  for (const [doctype, { titleField }] of Object.entries(linkedDocs)) {
    const names = [
      ...new Set(
        (notes || [])
          .filter((n) => n.reference_doctype === doctype && n.reference_docname)
          .map((n) => n.reference_docname as string)
          .filter((name) => !(`${doctype}:${name}` in linkedTitles)),
      ),
    ]
    if (!names.length) continue
    const docs: Record<string, string>[] = await call(
      'frappe.client.get_list',
      {
        doctype,
        filters: { name: ['in', names] },
        fields: ['name', titleField],
        limit_page_length: names.length,
      },
    )
    for (const d of docs) linkedTitles[`${doctype}:${d.name}`] = d[titleField]
  }
}

function linkedRoute(note?: NoteRef | null) {
  const linked = linkedDoc(note)
  if (!linked || !note?.reference_docname) return null
  return {
    name: linked.route,
    params: { [linked.param]: note.reference_docname },
    hash: '#notes',
  }
}

function linkedLabel(note: NoteRef): string {
  const title =
    linkedTitles[`${note.reference_doctype}:${note.reference_docname}`]
  return `${linkedDoc(note)?.label} · ${title || note.reference_docname}`
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
