import { getScript } from '@/data/script'
import { createToast, runSequentially } from '@/utils'
import { createDocumentResource } from 'frappe-ui'

const documentsCache = {}
const controllersCache = {}

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
    if (controllersCache[doctype]) return

    controllersCache[doctype] = setupScript(documentsCache[doctype][docname])
  }

  function getControllers(row = null) {
    const _doctype = row?.doctype || doctype
    return (controllersCache[doctype] || []).filter(
      (c) => c.constructor.name === _doctype.replace(/\s+/g, ''),
    )
  }

  async function triggerOnRefresh() {
    const controllers = getControllers()
    if (!controllers.length) return

    const tasks = controllers.map((c) => async () => await c.refresh())
    await runSequentially(tasks)
  }

  async function triggerOnChange(fieldname, row) {
    const controllers = getControllers(row)
    if (!controllers.length) return

    const tasks = controllers.map((c) => async () => {
      if (row) {
        c.currentRowIdx = row.idx
        c.value = row[fieldname]
        c.oldValue = getOldValue(fieldname, row)
      } else {
        c.value = documentsCache[doctype][docname].doc[fieldname]
        c.oldValue = getOldValue(fieldname)
      }
      await c[fieldname]?.()
    })

    await runSequentially(tasks)
  }

  async function triggerOnRowAdd(row) {
    const controllers = getControllers(row)
    if (!controllers.length) return

    const tasks = controllers.map((c) => async () => {
      c.currentRowIdx = row.idx
      c.value = row
      await c[row.parentfield + '_add']?.()
    })

    await runSequentially(tasks)
  }

  async function triggerOnRowRemove(selectedRows, rows) {
    if (!selectedRows) return
    const controllers = getControllers(rows[0])
    if (!controllers.length) return

    const tasks = controllers.map((c) => async () => {
      if (selectedRows.size === 1) {
        const selectedRow = Array.from(selectedRows)[0]
        c.currentRowIdx = rows.find((r) => r.name === selectedRow).idx
      } else {
        delete c.currentRowIdx
      }

      c.selectedRows = Array.from(selectedRows)
      c.rows = rows

      await c[rows[0].parentfield + '_remove']?.()
    })

    await runSequentially(tasks)
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
