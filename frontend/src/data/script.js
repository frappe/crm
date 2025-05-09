import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { createToast } from '@/utils'
import { call, createListResource } from 'frappe-ui'
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
  })

  if (!doctypeScripts[doctype] && !scripts.loading) {
    scripts.fetch()
  }

  function setupScript(document, helpers = {}) {
    let scripts = doctypeScripts[doctype]
    if (!scripts) return null

    const { $dialog, $socket, makeCall } = globalStore()

    helpers.createDialog = $dialog
    helpers.createToast = createToast
    helpers.socket = $socket
    helpers.router = router
    helpers.call = call

    helpers.crm = {
      makePhoneCall: makeCall,
    }

    return setupMultipleFormControllers(scripts, document, helpers)
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
                `⚠️ No class found for doctype: ${doctype}, it is mandatory to have a class for the parent doctype. it can be empty, but it should be present.`,
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
        console.error('Failed to load form controller:', err)
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
    let instance = new FormClass()

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

    setupHelperMethods(FormClass, instance, parentInstance, document)

    if (isChildDoctype) {
      instance.doc = createDocProxy(document.doc, parentInstance)
    } else {
      instance.doc = createDocProxy(document.doc, instance)
    }

    return instance
  }

  function setupHelperMethods(FormClass, instance, parentInstance, document) {
    if (typeof FormClass.prototype.getRow !== 'function') {
      FormClass.prototype.getRow = (parentField, idx) =>
        getRow(parentField, idx, document.doc, instance)
    }
    exposeHiddenMethods(instance, parentInstance, ['getRow'])
  }

  function getRow(parentField, idx, data, instance) {
    idx = idx || instance.currentRowIdx

    if (!data[parentField]) {
      console.warn(`⚠️ No data found for parent field: ${parentField}`)
      return null
    }
    const row = data[parentField].find((r) => r.idx === idx)

    if (!row) {
      console.warn(
        `⚠️ No row found for idx: ${idx} in parent field: ${parentField}`,
      )
      return null
    }

    row.parent = row.parent || data.name

    return createDocProxy(row, instance)
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
    return FormClass
  }

  function createDocProxy(data, instance) {
    return new Proxy(data, {
      get(target, prop) {
        if (prop === 'trigger') {
          if ('trigger' in data) {
            console.warn(
              `⚠️ Avoid using "trigger" as a field name — it conflicts with the built-in trigger() method.`,
            )
          }

          return (methodName, ...args) => {
            const method = instance[methodName]
            if (typeof method === 'function') {
              return method.apply(instance, args)
            } else {
              console.warn(`⚠️ Method "${methodName}" not found in class.`)
            }
          }
        }

        return target[prop]
      },
      set(target, prop, value) {
        target[prop] = value
        return true
      },
    })
  }

  function exposeHiddenMethods(instance, parentInstance, methodNames = []) {
    for (const name of methodNames) {
      // remove the method from parent instance if it exists
      if (parentInstance && parentInstance[name]) {
        delete instance.doc[name]
      }

      if (typeof instance[name] === 'function' && !instance.doc[name]) {
        // Show as actual method on doc, bound to instance
        Object.defineProperty(instance.doc, name, {
          value: (...args) => instance[name](...args),
          writable: false,
          enumerable: false,
          configurable: true,
        })
      }
    }
  }

  return {
    scripts,
    setupScript,
    setupFormController,
  }
}
