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
    const doctypeName = doctype.replace(/\s+/g, '')
    const doctypeController = controllers[doctypeName]

    if (!doctypeController) return

    documentsCache[doctype][docname]['controller'] = doctypeController
  }

  async function triggerOnChange(fieldname) {
    if (!documentsCache[doctype][docname]?.controller) return

    const c = documentsCache[doctype][docname].controller
    c.oldValue = getOldValue(fieldname)
    c.value = documentsCache[doctype][docname].doc[fieldname]

    return await c[fieldname]?.()
  }

  function getOldValue(fieldname) {
    if (!documentsCache[doctype][docname]) return ''

    const document = documentsCache[doctype][docname]
    const oldDoc = document.originalDoc
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
