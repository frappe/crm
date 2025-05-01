import { globalStore } from '@/stores/global'
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
    const controllers = {}

    for (let scriptName in scriptStrings) {
      let script = scriptStrings[scriptName]?.script
      if (!script) continue
      try {
        const className = getClassName(script)
        if (!className) throw new Error('No class found')

        const FormClass = evaluateFormClass(script, className, helpers)
        controllers[className] = setupFormController(FormClass, document)
      } catch (err) {
        console.error('Failed to load form controller:', err)
      }
    }

    return controllers
  }

  function setupFormController(FormClass, document) {
    const controller = new FormClass()

    for (const key in document) {
      if (document.hasOwnProperty(key)) {
        controller[key] = document[key]
      }
    }

    controller.actions = (controller.actions || []).filter(
      (action) => typeof action.condition !== 'function' || action.condition(),
    )

    return controller
  }

  // utility function to setup a form controller
  function getClassName(script) {
    const match = script.match(/class\s+([A-Za-z0-9_]+)/)
    return match ? match[1] : null
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

  return {
    scripts,
    setupScript,
    setupFormController,
  }
}
