import { getScript } from '@/data/script'
import { runSequentially } from '@/utils'
import { createDocumentResource, toast } from 'frappe-ui'

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
          toast.success(__('Document updated successfully'))
        },
        onError: (err) => {
          toast.error(__('Error updating document'))
          console.error(err)
        },
      },
    })
  }

  function setupFormScript() {
    if (controllersCache[doctype]?.[docname]) return

    if (!controllersCache[doctype]) {
      controllersCache[doctype] = {}
    }

    controllersCache[doctype][docname] = setupScript(
      documentsCache[doctype][docname],
    )
  }

  function getControllers(row = null) {
    const _doctype = row?.doctype || doctype
    return (controllersCache[doctype]?.[docname] || []).filter(
      (c) => c.constructor.name === _doctype.replace(/\s+/g, ''),
    )
  }

  async function triggerOnRefresh() {
    const handler = async function () {
      await this.refresh()
    }
    await trigger(handler)
  }

  async function triggerOnChange(fieldname, row) {
    const handler = async function () {
      if (row) {
        this.currentRowIdx = row.idx
        this.value = row[fieldname]
        this.oldValue = getOldValue(fieldname, row)
      } else {
        this.value = documentsCache[doctype][docname].doc[fieldname]
        this.oldValue = getOldValue(fieldname)
      }
      await this[fieldname]?.()
    }

    await trigger(handler, row)
  }

  async function triggerOnRowAdd(row) {
    const handler = async function () {
      this.currentRowIdx = row.idx
      this.value = row
      await this[row.parentfield + '_add']?.()
    }

    await trigger(handler, row)
  }

  async function triggerOnRowRemove(selectedRows, rows) {
    const handler = async function () {
      if (selectedRows.size === 1) {
        const selectedRow = Array.from(selectedRows)[0]
        this.currentRowIdx = rows.find((r) => r.name === selectedRow).idx
      } else {
        delete this.currentRowIdx
      }

      this.selectedRows = Array.from(selectedRows)
      this.rows = rows

      await this[rows[0].parentfield + '_remove']?.()
    }

    await trigger(handler, rows[0])
  }

  async function triggerOnCreateLead() {
    const args = Array.from(arguments)
    const handler = async function () {
      await this.on_create_lead(...args)
    }
    await trigger(handler)
  }

  async function trigger(taskFn, row = null) {
    const controllers = getControllers(row)
    if (!controllers.length) return

    const tasks = controllers.map(
      (controller) => async () => await taskFn.call(controller),
    )

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
    triggerOnCreateLead,
  }
}
