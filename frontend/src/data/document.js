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
    if (documentsCache[doctype][docname]['controllers']) return

    const controllers = setupScript(documentsCache[doctype][docname])
    if (!controllers) return

    documentsCache[doctype][docname]['controllers'] = controllers
  }

  function getControllers(row = null, dt = null) {
    let controllers = documentsCache[doctype][docname]?.controllers || {}
    if (Object.keys(controllers).length === 0) return

    dt = dt || doctype
    if (!controllers[dt].length) return []

    const _dt = row?.doctype ? row.doctype : doctype
    const _controllers = controllers[dt].filter(
      (c) => c.constructor.name === _dt.replace(/\s+/g, ''),
    )
    return _controllers || []
  }

  async function triggerOnRefresh() {
    const controllers = getControllers()
    if (!controllers.length) return
    for (const c of controllers) {
      await c.refresh()
    }
  }

  async function triggerOnChange(fieldname, row) {
    const controllers = getControllers(row)
    if (!controllers.length) return

    for (const c of controllers) {
      if (row) {
        c.currentRowIdx = row.idx
        c.value = row[fieldname]
        c.oldValue = getOldValue(fieldname, row)
      } else {
        c.value = documentsCache[doctype][docname].doc[fieldname]
        c.oldValue = getOldValue(fieldname)
      }
      await c[fieldname]?.()
    }
  }

  async function triggerOnRowAdd(row) {
    const controllers = getControllers(row)
    if (!controllers.length) return

    for (const c of controllers) {
      c.currentRowIdx = row.idx
      c.value = row

      await c[row.parentfield + '_add']?.()
    }
  }

  async function triggerOnRowRemove(selectedRows, rows) {
    if (!selectedRows) return
    const controllers = getControllers(rows[0])
    if (!controllers.length) return

    for (const c of controllers) {
      if (selectedRows.size === 1) {
        const selectedRow = Array.from(selectedRows)[0]
        c.currentRowIdx = rows.find((r) => r.name === selectedRow).idx
      } else {
        delete c.currentRowIdx
      }

      c.selectedRows = Array.from(selectedRows)
      c.rows = rows

      await c[rows[0].parentfield + '_remove']?.()
    }
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
    triggerOnChange,
    triggerOnRowAdd,
    triggerOnRowRemove,
    triggerOnRefresh,
    setupFormScript,
  }
}
