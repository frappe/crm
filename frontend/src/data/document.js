import { getScript } from '@/data/script'
import { createToast } from '@/utils'
import { createDocumentResource } from 'frappe-ui'
import { computed } from 'vue'

const documentsCache = {}

export function useDocument(doctype, docname) {
  const { setupScript } = getScript(doctype)

  documentsCache[doctype] = documentsCache[doctype] || {}

  if (!documentsCache[doctype][docname]) {
    documentsCache[doctype][docname] = createDocumentResource({
      doctype: doctype,
      name: docname,
      onSuccess: () => setupFormScript(),
      setValue: {
        onSuccess: () => {
          createToast({
            title: 'Data Updated',
            icon: 'check',
            iconClasses: 'text-ink-green-3',
          })
        },
        onError: (err) => {
          createToast({
            title: 'Error',
            text: err.messages[0],
            icon: 'x',
            iconClasses: 'text-red-600',
          })
        },
      },
    })
  }

  function setupFormScript() {
    if (documentsCache[doctype][docname]['controllers']) return

    const controllers = setupScript(documentsCache[doctype][docname])
    if (!controllers) return

    documentsCache[doctype][docname]['controllers'] = controllers
  }

  function getController(dt = null) {
    let controllers = documentsCache[doctype][docname]?.controllers || {}
    if (Object.keys(controllers).length === 0) return

    dt = dt || doctype
    let doctypeClassName = dt.replace(/\s+/g, '')
    const c = controllers[doctypeClassName]
    return c || null
  }

  function getActions() {
    let c = getController() || setupFormScript()
    if (!c) return []
    return c?.actions || []
  }

  async function triggerOnRefresh() {
    const c = getController()
    if (!c) return
    return await c.refresh()
  }

  async function triggerOnChange(fieldname, row) {
    const dt = row?.doctype ? row.doctype : doctype
    const c = getController(dt)
    if (!c) return

    if (row) {
      c.currentRowIdx = row.idx
      c.value = row[fieldname]
      c.oldValue = getOldValue(fieldname, row)
    } else {
      c.value = documentsCache[doctype][docname].doc[fieldname]
      c.oldValue = getOldValue(fieldname)
    }

    return await c[fieldname]?.()
  }

  function getOldValue(fieldname, row) {
    if (!documentsCache[doctype][docname]) return ''

    const document = documentsCache[doctype][docname]
    const oldDoc = document.originalDoc

    if (row?.name) {
      return oldDoc?.[row.parentfield]?.find((r) => r.name === row.name)?.[
        fieldname
      ]
    }

    return oldDoc?.[fieldname] || document.doc[fieldname]
  }

  return {
    document: documentsCache[doctype][docname],
    actions: computed(() => getActions()),
    getOldValue,
    triggerOnChange,
    triggerOnRefresh,
    setupFormScript,
  }
}
