import { ref } from 'vue'

/**
 * Reactive array of dialog config objects.
 * Rendered by FieldLayoutDialogContainer in GlobalModals.vue.
 */
export const fieldLayoutDialogs = ref([])

/**
 * Open a form dialog. Returns a Promise that resolves with data on submit
 * or null on cancel. Also supports onSubmit/onCancel callbacks.
 *
 * Three usage patterns (all composable):
 *
 *   // 1. Promise — sequential workflows
 *   const data = await formDialog({ fields: [...] })
 *
 *   // 2. onSubmit callback — fire-and-forget
 *   formDialog({ fields: [...], onSubmit(data) { ... } })
 *
 *   // 3. Custom actions — full control
 *   formDialog({ fields: [...], actions: [{ label: 'Go', onClick({data,close}) { close(data) } }] })
 *
 * @param {object}   options
 * @param {string}   options.title - Dialog title
 * @param {string}   [options.doctype] - Fetch Quick Entry layout for this doctype
 * @param {Array}    [options.tabs] - Full layout: tabs > sections > columns > fields
 * @param {Array}    [options.fields] - Flat field list (wrapped in single section)
 * @param {Array}    [options.fieldnames] - Pick specific fields from doctype meta
 * @param {object}   [options.defaults] - Pre-fill field values
 * @param {Array}    [options.required] - Extra required fieldnames (shows asterisk + validates)
 * @param {string}   [options.size] - Dialog size (default 'xl')
 * @param {Array}    [options.actions] - Custom action buttons (overrides onSubmit)
 * @param {Function} [options.onSubmit] - Called with data on submit (before close). Throw to stay open.
 * @param {Function} [options.onCancel] - Called when dialog is cancelled/closed
 * @param {string}   [options.submitLabel] - Label for the default Submit button (default 'Submit')
 * @param {string}   [options.cancelLabel] - If provided, shows a Cancel button with this label
 * @returns {Promise<object|null>}
 */
export function renderFieldLayoutDialog(options) {
  return new Promise((resolve) => {
    let resolved = false

    const dialogEntry = {
      key: `fld-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      props: {
        ...options,
        onResolve: (result) => {
          if (resolved) return
          resolved = true
          resolve(result)
          setTimeout(() => {
            const idx = fieldLayoutDialogs.value.indexOf(dialogEntry)
            if (idx !== -1) fieldLayoutDialogs.value.splice(idx, 1)
          }, 300)
        },
      },
    }

    fieldLayoutDialogs.value.push(dialogEntry)
  })
}
