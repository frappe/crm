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

  return {
    document: documentsCache[doctype][docname],
    getActions: () =>
      documentsCache[doctype][docname]?.controller?.actions || [],
    setupFormScript,
  }
}
