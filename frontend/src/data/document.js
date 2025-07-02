import { getScript } from '@/data/script'
import { runSequentially, parseAssignees } from '@/utils'
import { createDocumentResource, createResource, toast } from 'frappe-ui'
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
            triggerOnSave()
            toast.success(__('Document updated successfully'))
          },
          onError: (err) => {
            let errorMessage = __('Error updating document')
            if (err.exc_type == 'MandatoryError') {
              const fieldName = err.messages
                .map((msg) => {
                  let arr = msg.split(': ')
                  return arr[arr.length - 1].trim()
                })
                .join(', ')
              errorMessage = __('Mandatory field error: {0}', [fieldName])
            }
            toast.error(errorMessage)
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

  const assignees = createResource({
    url: 'crm.api.doc.get_assigned_users',
    cache: `assignees:${doctype}:${docname}`,
    auto: docname ? true : false,
    params: {
      doctype: doctype,
      name: docname,
    },
    transform: (data) => parseAssignees(data),
  })

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

    triggerOnLoad()
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

  async function triggerOnLoad() {
    const handler = async function () {
      await (this.onLoad?.() || this.on_load?.() || this.onload?.())
    }
    await trigger(handler)
  }

  async function triggerOnBeforeCreate() {
    const args = Array.from(arguments)
    const handler = async function () {
      await (this.onBeforeCreate?.(...args) || this.on_before_create?.(...args))
    }
    await trigger(handler)
  }

  async function triggerOnSave() {
    const handler = async function () {
      await (this.onSave?.() || this.on_save?.())
    }
    await trigger(handler)
  }

  async function triggerOnRefresh() {
    const handler = async function () {
      await this.refresh?.()
    }
    await trigger(handler)
  }

  async function triggerOnChange(fieldname, value, row) {
    let oldValue = null
    if (row) {
      oldValue = row[fieldname]
      row[fieldname] = value
    } else {
      oldValue = documentsCache[doctype][docname || ''].doc[fieldname]
      documentsCache[doctype][docname || ''].doc[fieldname] = value
    }

    const handler = async function () {
      this.value = value
      this.oldValue = oldValue
      if (row) {
        this.currentRowIdx = row.idx
      }
      await this[fieldname]?.()
    }

    try {
      await trigger(handler, row)
    } catch (error) {
      if (row) {
        row[fieldname] = oldValue
      } else {
        documentsCache[doctype][docname || ''].doc[fieldname] = oldValue
      }
      console.error(handler)
      throw error
    }
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
      await (this.onCreateLead?.(...args) || this.on_create_lead?.(...args))
    }
    await trigger(handler)
  }

  async function triggerConvertToDeal() {
    const args = Array.from(arguments)
    const handler = async function () {
      await (this.convertToDeal?.(...args) || this.convert_to_deal?.(...args))
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

  return {
    document: documentsCache[doctype][docname || ''],
    assignees,
    getControllers,
    triggerOnLoad,
    triggerOnBeforeCreate,
    triggerOnSave,
    triggerOnRefresh,
    triggerOnChange,
    triggerOnRowAdd,
    triggerOnRowRemove,
    setupFormScript,
    triggerOnCreateLead,
    triggerConvertToDeal,
  }
}
