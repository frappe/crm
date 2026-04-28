import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { getClassNames, createDocProxy } from '@/utils/scriptHelpers'
import { renderFieldLayoutDialog } from '@/utils/renderFieldLayoutDialog'
import { call, createListResource, toast } from 'frappe-ui'
import { reactive } from 'vue'
import router from '@/router'

const doctypeScripts = reactive({})
const fileScriptModules = import.meta.glob('../doctypes/*/*.js')
const fileScriptCache = {}

async function loadFileScript(doctype, view) {
  const key = `${doctype}:${view}`
  if (key in fileScriptCache) return fileScriptCache[key]

  const slug = doctype.toLowerCase().replaceAll(' ', '_')
  const viewSlug = view.toLowerCase()
  const path = `../doctypes/${slug}/${viewSlug}.js`

  const loader = fileScriptModules[path]
  if (!loader) {
    fileScriptCache[key] = null
    return null
  }

  try {
    fileScriptCache[key] = await loader()
  } catch {
    fileScriptCache[key] = null
  }

  return fileScriptCache[key]
}

export function getScript(doctype, view = 'Form') {
  const scripts = createListResource({
    doctype: 'CRM Form Script',
    cache: ['Form Scripts', doctype, view],
    fields: ['name', 'dt', 'view', 'script'],
    filters: { view, dt: doctype, enabled: 1 },
    onSuccess: (_scripts) => {
      for (let script of _scripts) {
        if (!doctypeScripts[doctype]) {
          doctypeScripts[doctype] = {}
        }
        doctypeScripts[doctype][script.name] = script || {}
      }
    },
    onError: (err) => {
      console.error(
        `Error loading CRM Form Scripts for ${doctype} (view: ${view}):`,
        err,
      )
    },
  })

  if (!doctypeScripts[doctype] && !scripts.loading) {
    scripts.fetch()
  }

  async function setupScript(document, helpers = {}) {
    const [fileModule] = await Promise.all([
      loadFileScript(doctype, view),
      scripts.list.promise,
    ])

    const { $dialog, $socket } = globalStore()

    helpers.createDialog = $dialog
    helpers.toast = toast
    helpers.socket = $socket
    helpers.router = router
    helpers.call = call
    helpers.formDialog = renderFieldLayoutDialog

    helpers.throwError = (message) => {
      toast.error(message || __('An error occurred'))
      throw new Error(message || __('An error occurred'))
    }

    let scriptDefs = doctypeScripts[doctype]
    const hasFileScript = fileModule != null
    const hasDbScripts = scriptDefs && Object.keys(scriptDefs).length > 0

    if (!hasFileScript && !hasDbScripts) return null

    return setupMultipleFormControllers(
      fileModule,
      scriptDefs,
      document,
      helpers,
    )
  }

  function setupMultipleFormControllers(
    fileModule,
    scriptStrings,
    document,
    helpers,
  ) {
    const controllers = []
    let parentInstanceIdx = null
    const doctypeName = doctype.replace(/\s+/g, '')
    const { doctypesMeta } = getMeta(doctype)

    function addController(FormClass, className) {
      setupHelperMethods(FormClass)

      let parentInstance = null
      let isChildDoctype = className !== doctypeName

      if (isChildDoctype) {
        if (!controllers.length) {
          console.error(
            __(
              '⚠️ No class found for doctype: {0}, it is mandatory to have a class for the parent doctype. it can be empty, but it should be present.',
              [doctype],
            ),
          )
          return
        }
        parentInstance = controllers[parentInstanceIdx]
      } else {
        parentInstanceIdx = controllers.length || 0
      }

      const instance = setupFormController(
        FormClass,
        doctypesMeta,
        document,
        helpers,
        parentInstance,
        isChildDoctype,
      )

      controllers.push(instance)
    }

    if (fileModule) {
      try {
        for (const [name, exported] of Object.entries(fileModule)) {
          if (typeof exported === 'function') {
            addController(exported, name)
          }
        }
      } catch (err) {
        console.error(
          __('Failed to load file-based form controller: {0}', [err]),
        )
      }
    }

    for (let scriptName in scriptStrings) {
      let script = scriptStrings[scriptName]?.script
      if (!script) continue
      try {
        const classNames = getClassNames(script)
        if (!classNames) continue

        classNames.forEach((className) => {
          const FormClass = evaluateFormClass(script, className, helpers)
          if (!FormClass) return
          addController(FormClass, className)
        })
      } catch (err) {
        console.error(__('Failed to load form controller: {0}', [err]))
      }
    }

    return controllers
  }

  function setupFormController(
    FormClass,
    meta,
    document,
    helpers,
    parentInstance = null,
    isChildDoctype = false,
  ) {
    document.actions = document.actions || []
    document.statuses = document.statuses || []

    let instance = new FormClass()

    // Store the original document context to be used by properties like 'actions'
    instance._originalDocumentContext = document
    instance._isChildDoctype = isChildDoctype

    for (const key in helpers) {
      instance[key] = helpers[key]
    }

    for (const key in document) {
      if (Object.hasOwn(document, key)) {
        instance[key] = document[key]
      }
    }

    instance.getMeta = async (doctype) => {
      if (!meta[doctype]) {
        await getMeta(doctype)
        return meta[doctype]
      }
      return meta[doctype]
    }

    const getDoc = () => document.doc

    if (isChildDoctype) {
      instance.doc = createDocProxy(getDoc, parentInstance, instance)

      if (!parentInstance._childInstances) {
        parentInstance._childInstances = []
      }

      parentInstance._childInstances.push(instance)
    } else {
      instance.doc = createDocProxy(getDoc, instance)
    }

    return instance
  }

  function setupHelperMethods(FormClass) {
    if (typeof FormClass.prototype.getRow !== 'function') {
      FormClass.prototype.getRow = function (parentField, idx) {
        idx = idx || this.currentRowIdx

        let dt = null

        if (this instanceof Array) {
          const { getFields } = getMeta(this.doc.doctype)
          let fields = getFields()
          let field = fields.find((f) => f.fieldname === parentField)
          dt = field?.options?.replace(/\s+/g, '')

          if (!idx && dt) {
            idx = this.find((r) => r.constructor.name === dt)?.currentRowIdx
          }
        }

        if (!this.doc[parentField]) {
          console.warn(
            __('⚠️ No data found for parent field: {0}', [parentField]),
          )
          return null
        }
        const row = this.doc[parentField].find((r) => r.idx === idx)

        if (!row) {
          console.warn(
            __('⚠️ No row found for idx: {0} in parent field: {1}', [
              idx,
              parentField,
            ]),
          )
          return null
        }

        row.parent = row.parent || this.doc.name

        if (this instanceof Array && dt) {
          return createDocProxy(
            row,
            this.find((r) => r.constructor.name === dt),
          )
        }

        return createDocProxy(row, this)
      }
    }

    if (!Object.prototype.hasOwnProperty.call(FormClass.prototype, 'actions')) {
      Object.defineProperty(FormClass.prototype, 'actions', {
        configurable: true,
        enumerable: true,
        get() {
          if (!this._originalDocumentContext) {
            console.warn(
              'CRM Script: _originalDocumentContext not found on instance for actions getter.',
            )
            return []
          }

          return this._originalDocumentContext.actions
        },
        set(newValue) {
          if (!this._originalDocumentContext) {
            console.warn(
              'CRM Script: _originalDocumentContext not found on instance for actions setter.',
            )
            return
          }
          if (!Array.isArray(newValue)) {
            console.warn(
              'CRM Script: "actions" property must be an array. Value was not set.',
              newValue,
            )
            this._originalDocumentContext.actions = []
            return
          }
          this._originalDocumentContext.actions = newValue
        },
      })
    }

    if (
      !Object.prototype.hasOwnProperty.call(FormClass.prototype, 'statuses')
    ) {
      Object.defineProperty(FormClass.prototype, 'statuses', {
        configurable: true,
        enumerable: true,
        get() {
          if (!this._originalDocumentContext) {
            console.warn(
              'CRM Script: _originalDocumentContext not found on instance for statuses getter.',
            )
            return []
          }

          return this._originalDocumentContext.statuses
        },
        set(newValue) {
          if (!this._originalDocumentContext) {
            console.warn(
              'CRM Script: _originalDocumentContext not found on instance for statuses setter.',
            )
            return
          }
          if (!Array.isArray(newValue)) {
            console.warn(
              'CRM Script: "statuses" property must be an array. Value was not set.',
              newValue,
            )
            this._originalDocumentContext.statuses = []
            return
          }
          this._originalDocumentContext.statuses = newValue
        },
      })
    }

    if (typeof FormClass.prototype.setFieldHtml !== 'function') {
      FormClass.prototype.setFieldHtml = function (fieldname, html) {
        if (!this._originalDocumentContext) {
          console.warn(
            'CRM Script: _originalDocumentContext not found on instance for setFieldHtml.',
          )
          return
        }
        if (!this._originalDocumentContext.fieldHtmlMap) {
          this._originalDocumentContext.fieldHtmlMap = {}
        }
        this._originalDocumentContext.fieldHtmlMap[fieldname] = html
      }
    }

    if (typeof FormClass.prototype.setFieldProperty !== 'function') {
      FormClass.prototype.setFieldProperty = function (
        target,
        property,
        value,
        rowName,
      ) {
        const ctx = this._originalDocumentContext
        if (!ctx) {
          console.warn(
            'CRM Script: _originalDocumentContext not found on instance for setFieldProperty.',
          )
          return
        }
        if (!ctx.fieldPropertyOverrides) ctx.fieldPropertyOverrides = {}
        const key = rowName ? `${target}:${rowName}` : target
        if (!ctx.fieldPropertyOverrides[key])
          ctx.fieldPropertyOverrides[key] = {}
        ctx.fieldPropertyOverrides[key][property] = value
      }
    }

    if (typeof FormClass.prototype.setFieldProperties !== 'function') {
      FormClass.prototype.setFieldProperties = function (
        target,
        properties,
        rowName,
      ) {
        if (!properties || typeof properties !== 'object') return
        for (const [key, value] of Object.entries(properties)) {
          this.setFieldProperty(target, key, value, rowName)
        }
      }
    }

    if (typeof FormClass.prototype.removeFieldProperty !== 'function') {
      FormClass.prototype.removeFieldProperty = function (
        target,
        property,
        rowName,
      ) {
        const ctx = this._originalDocumentContext
        const key = rowName ? `${target}:${rowName}` : target
        if (!ctx?.fieldPropertyOverrides?.[key]) return
        delete ctx.fieldPropertyOverrides[key][property]
        if (Object.keys(ctx.fieldPropertyOverrides[key]).length === 0) {
          delete ctx.fieldPropertyOverrides[key]
        }
      }
    }

    if (typeof FormClass.prototype.getField !== 'function') {
      FormClass.prototype.getField = function (fieldname) {
        const ctx = this._originalDocumentContext
        const dt = ctx?.doc?.doctype || ''
        if (!dt) return null

        const { doctypesMeta: allMeta } = getMeta(dt)
        const raw = allMeta[dt]?.fields?.find((f) => f.fieldname === fieldname)
        if (!raw) return null

        // Return a clone merged with any overrides
        const overrides = ctx?.fieldPropertyOverrides?.[fieldname] || {}
        return { ...raw, ...overrides }
      }
    }
  }

  // getClassNames and createDocProxy are imported from '@/utils/scriptHelpers'

  function evaluateFormClass(script, className, helpers = {}) {
    const helperKeys = Object.keys(helpers)
    const helperValues = Object.values(helpers)

    const wrappedScript = `
		${script}
		return ${className};
	`

    const FormClass = new Function(...helperKeys, wrappedScript)(
      ...helperValues,
    )

    return FormClass
  }

  return {
    scripts,
    setupScript,
    setupFormController,
  }
}
