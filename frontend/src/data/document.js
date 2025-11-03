import { getScript } from '@/data/script'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { runSequentially, parseAssignees, evaluateExpression } from '@/utils'
import { createDocumentResource, createResource, toast } from 'frappe-ui'
import { ref, reactive } from 'vue'

const documentsCache = {}
const controllersCache = {}
const assigneesCache = {}
const permissionsCache = {}

export function useDocument(doctype, docname, resourceOverrides = {}) {
  const { setupScript, scripts } = getScript(doctype)
  const meta = getMeta(doctype)

  documentsCache[doctype] = documentsCache[doctype] || {}

  const error = ref('')

  if (!documentsCache[doctype][docname || '']) {
    if (docname) {
      documentsCache[doctype][docname] = createDocumentResource({
        doctype: doctype,
        name: docname,
        onSuccess: async () => await setupFormScript(),
        onError: (err) => {
          error.value = err
          if (err.exc_type === 'DoesNotExistError') {
            toast.error(__(err.messages[0] || 'Document does not exist'))
          }
          if (err.exc_type === 'PermissionError') {
            toast.error(
              __(
                err.messages[0] ||
                  'You do not have permission to access this document',
              ),
            )
          }
        },
        setValue: {
          validate,
          onSuccess: () => {
            triggerOnSave()
            toast.success(__('Document updated successfully'))
          },
          onError: (err) => {
            triggerOnError(err)

            if (err.exc_type == 'MandatoryError') {
              const fieldName = err.messages
                .map((msg) => {
                  let arr = msg.split(': ')
                  return arr[arr.length - 1].trim()
                })
                .join(', ')
              toast.error(__('Mandatory field error: {0}', [fieldName]))
              return
            }

            err.messages?.forEach((msg) => {
              toast.error(msg)
            })

            if (err.messages?.length === 0) {
              toast.error(__('An error occurred while updating the document'))
            }

            console.error(err)
          },
        },
        ...resourceOverrides
      })
    } else {
      documentsCache[doctype][''] = reactive({
        doc: {},
      })
      setupFormScript()
    }
  }

  assigneesCache[doctype] = assigneesCache[doctype] || {}

  if (!assigneesCache[doctype][docname || '']) {
    assigneesCache[doctype][docname || ''] = createResource({
      url: 'crm.api.doc.get_assigned_users',
      cache: `assignees:${doctype}:${docname}`,
      auto: docname ? true : false,
      params: {
        doctype: doctype,
        name: docname,
      },
      transform: (data) => parseAssignees(data),
    })
  }

  permissionsCache[doctype] = permissionsCache[doctype] || {}

  if (!permissionsCache[doctype][docname || '']) {
    permissionsCache[doctype][docname || ''] = createResource({
      url: 'frappe.client.get_doc_permissions',
      cache: `permissions:${doctype}:${docname}`,
      auto: docname ? true : false,
      params: {
        doctype: doctype,
        docname: docname,
      },
      initialData: { permissions: {} },
    })
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

    const { makeCall } = globalStore()

    let helpers = {}

    helpers.crm = {
      makePhoneCall: makeCall,
      openSettings: (page) => {
        showSettings.value = true
        activeSettingsPage.value = page
      },
    }

    const controllersArray = await setupScript(
      documentsCache[doctype][docname || ''],
      helpers,
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

  function validate(d) {
    checkMandatory(d.doc || d.fieldname)
  }

  function checkMandatory(doc) {
    let fields = meta?.getFields() || []

    if (!fields || fields.length === 0) return

    let missingFields = []

    fields.forEach((df) => {
      let parent = meta?.doctypeMeta?.[df.parent] || null
      if (evaluateExpression(df.mandatory_depends_on, doc, parent)) {
        const value = doc[df.fieldname]
        if (
          value === undefined ||
          value === null ||
          (typeof value === 'string' && value.trim() === '') ||
          (Array.isArray(value) && value.length === 0)
        ) {
          missingFields.push(df.label || df.fieldname)
        }
      }
    })

    if (missingFields.length > 0) {
      toast.error(
        __('Mandatory fields required: {0}', [missingFields.join(', ')]),
      )
      throw new Error(
        __('Mandatory fields required: {0}', [missingFields.join(', ')]),
      )
    }
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

  async function triggerOnError() {
    const handler = async function () {
      await (this.onError?.() || this.on_error?.())
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
    assignees: assigneesCache[doctype][docname || ''],
    permissions: permissionsCache[doctype][docname || ''],
    scripts,
    error,
    validate,
    getControllers,
    triggerOnLoad,
    triggerOnBeforeCreate,
    triggerOnSave,
    triggerOnError,
    triggerOnRefresh,
    triggerOnChange,
    triggerOnRowAdd,
    triggerOnRowRemove,
    setupFormScript,
    triggerOnCreateLead,
    triggerConvertToDeal,
  }
}
