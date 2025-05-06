import { getScript } from '@/data/script'
import { createToast } from '@/utils'
import { createDocumentResource } from 'frappe-ui'

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
    const controllers = setupScript(documentsCache[doctype][docname])
    if (!controllers) return

    documentsCache[doctype][docname]['controllers'] = controllers
  }

  async function triggerOnChange(fieldname, row) {
    let controllers = documentsCache[doctype][docname]?.controllers
    if (Object.keys(controllers).length === 0) return

    let _dt = row?.doctype ? row.doctype : doctype
    let doctypeClassName = _dt.replace(/\s+/g, '')
    const c = controllers[doctypeClassName]
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
    getActions: () =>
      documentsCache[doctype][docname]?.controller?.actions || [],
    getOldValue,
    triggerOnChange,
    setupFormScript,
  }
}
