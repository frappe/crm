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

  async function triggerOnChange(fieldname, childTableObj) {
    let controllers = documentsCache[doctype][docname]?.controllers
    if (Object.keys(controllers).length === 0) return

    let _dt = childTableObj.dt ? childTableObj.dt : doctype
    let doctypeClassName = _dt.replace(/\s+/g, '')
    const c = controllers[doctypeClassName]
    if (!c) return

    if (childTableObj) {
      let grid = documentsCache[doctype][docname].doc[childTableObj.fieldname]
      c.row = grid.find((row) => row.name === childTableObj.dn)
      c.oldValue = getOldValue(fieldname, childTableObj)
      c.value = c.row[fieldname]
    } else {
      c.oldValue = getOldValue(fieldname)
      c.value = documentsCache[doctype][docname].doc[fieldname]
    }

    return await c[fieldname]?.()
  }

  function getOldValue(fieldname, childTableObj) {
    if (!documentsCache[doctype][docname]) return ''

    const document = documentsCache[doctype][docname]
    const oldDoc = document.originalDoc

    if (childTableObj?.dn) {
      return oldDoc?.[childTableObj.fieldname]?.find(
        (r) => r.name === childTableObj.dn,
      )?.[fieldname]
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
