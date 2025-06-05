import { getScript } from '@/data/script'
import { runSequentially } from '@/utils'
import { createDocumentResource, toast } from 'frappe-ui'
import { reactive } from 'vue'

const documentsCache = {}
const controllersCache = {}

export function useDocument(doctype, docname) {
  const { setupScript } = getScript(doctype)

  documentsCache[doctype] = documentsCache[doctype] || {}

  if (!documentsCache[doctype][docname || '']) {
    if (docname) {
      documentsCache[doctype][docname] = createDocumentResource({
        doctype: doctype,
        name: docname,
        onSuccess: async () => await setupFormScript(),
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
    } else {
      documentsCache[doctype][''] = reactive({
        doc: {},
      })
      setupFormScript()
    }
  }

  async function setupFormScript() {
    if (
      controllersCache[doctype] &&
      typeof controllersCache[doctype][docname || ''] === 'object'
    ) {
      return
    }

    if (!controllersCache[doctype]) {
      controllersCache[doctype] = {}
    }

    controllersCache[doctype][docname || ''] = {}

    const controllersArray = await setupScript(
      documentsCache[doctype][docname || ''],
    )

    if (!controllersArray || controllersArray.length === 0) return

    const organizedControllers = {}
    for (const controller of controllersArray) {
      const controllerKey = controller.constructor.name // e.g., "CRMLead", "CRMProducts"
      if (!organizedControllers[controllerKey]) {
        organizedControllers[controllerKey] = []
      }
      organizedControllers[controllerKey].push(controller)
    }
    controllersCache[doctype][docname || ''] = organizedControllers
  }

  function getControllers(row = null) {
    const _doctype = row?.doctype || doctype
    const controllerKey = _doctype.replace(/\s+/g, '')

    const docControllers = controllersCache[doctype]?.[docname || '']

    if (
      typeof docControllers === 'object' &&
      docControllers !== null &&
      !Array.isArray(docControllers)
    ) {
      return docControllers[controllerKey] || []
    }
    return []
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
        this.value = documentsCache[doctype][docname || ''].doc[fieldname]
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
      await this.on_create_lead?.(...args)
    }
    await trigger(handler)
  }

  async function triggerConvertToDeal() {
    const args = Array.from(arguments)
    const handler = async function () {
      await this.convert_to_deal?.(...args)
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
    if (!documentsCache[doctype][docname || '']) return ''

    const document = documentsCache[doctype][docname || '']
    const oldDoc = document.originalDoc

    if (row?.name) {
      return oldDoc?.[row.parentfield]?.find((r) => r.name === row.name)?.[
        fieldname
      ]
    }

    return oldDoc?.[fieldname] || document.doc[fieldname]
  }

  return {
    document: documentsCache[doctype][docname || ''],
    triggerOnChange,
    triggerOnRowAdd,
    triggerOnRowRemove,
    triggerOnRefresh,
    setupFormScript,
    triggerOnCreateLead,
    triggerConvertToDeal,
  }
}
