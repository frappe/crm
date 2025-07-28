import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { call, createListResource, toast } from 'frappe-ui'
import { reactive } from 'vue'
import router from '@/router'

const doctypeScripts = reactive({})

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
    await scripts.list.promise

    let scriptDefs = doctypeScripts[doctype]
    if (!scriptDefs || Object.keys(scriptDefs).length === 0) return null

    const { $dialog, $socket } = globalStore()

    helpers.createDialog = $dialog
    helpers.toast = toast
    helpers.socket = $socket
    helpers.router = router
    helpers.call = call

    helpers.throwError = (message) => {
      toast.error(message || __('An error occurred'))
      throw new Error(message || __('An error occurred'))
    }

    return setupMultipleFormControllers(scriptDefs, document, helpers)
  }

  function setupMultipleFormControllers(scriptStrings, document, helpers) {
    const controllers = []
    let parentInstanceIdx = null

    for (let scriptName in scriptStrings) {
      let script = scriptStrings[scriptName]?.script
      if (!script) continue
      try {
        const classNames = getClassNames(script)
        if (!classNames) continue

        classNames.forEach((className) => {
          const FormClass = evaluateFormClass(script, className, helpers)
          if (!FormClass) return

          let parentInstance = null
          let doctypeName = doctype.replace(/\s+/g, '')

          let { doctypeMeta } = getMeta(doctype)

          // if className is not doctype name, then it is a child doctype
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
            doctypeMeta,
            document,
            parentInstance,
            isChildDoctype,
          )

          controllers.push(instance)
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
    parentInstance = null,
    isChildDoctype = false,
  ) {
    document.actions = document.actions || []
    document.statuses = document.statuses || []

    let instance = new FormClass()

    // Store the original document context to be used by properties like 'actions'
    instance._originalDocumentContext = document
    instance._isChildDoctype = isChildDoctype

    for (const key in document) {
      if (document.hasOwnProperty(key)) {
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
  }

  // utility function to setup a form controller
  function getClassNames(script) {
    const withoutComments = script
      .replace(/\/\/.*$/gm, '') // Remove single-line comments
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove multi-line comments

    // Match class declarations
    return (
      [...withoutComments.matchAll(/class\s+([A-Za-z0-9_]+)/g)].map(
        (match) => match[1],
      ) || []
    )
  }

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

    setupHelperMethods(FormClass)

    return FormClass
  }

  function createDocProxy(source, instance, childInstance = null) {
    const isFunction = typeof source === 'function'
    const getCurrentData = () => (isFunction ? source() : source)

    return new Proxy(
      {},
      {
        get(target, prop) {
          const currentDocData = getCurrentData()
          if (!currentDocData) return undefined

          if (prop === 'trigger') {
            if (currentDocData && 'trigger' in currentDocData) {
              console.warn(
                __(
                  '⚠️ Avoid using "trigger" as a field name — it conflicts with the built-in trigger() method.',
                ),
              )
            }

            return (methodName, ...args) => {
              const method = instance[methodName]
              if (typeof method === 'function') {
                return method.apply(instance, args)
              } else {
                console.warn(
                  __('⚠️ Method "{0}" not found in class.', [methodName]),
                )
              }
            }
          }

          if (prop === 'getRow') {
            return instance.getRow.bind(
              childInstance || instance._childInstances || instance,
            )
          }

          return currentDocData[prop]
        },
        set(target, prop, value) {
          const currentDocData = getCurrentData()
          if (!currentDocData) return false

          currentDocData[prop] = value
          return true
        },
        has(target, prop) {
          const currentDocData = getCurrentData()
          if (!currentDocData) return false
          return prop in currentDocData
        },
        ownKeys(target) {
          const currentDocData = getCurrentData()
          if (!currentDocData) return []
          return Reflect.ownKeys(currentDocData)
        },
        getOwnPropertyDescriptor(target, prop) {
          const currentDocData = getCurrentData()
          if (!currentDocData) return undefined
          return Reflect.getOwnPropertyDescriptor(currentDocData, prop)
        },
      },
    )
  }

  return {
    scripts,
    setupScript,
    setupFormController,
  }
}
