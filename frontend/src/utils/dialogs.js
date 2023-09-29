import { Dialog, ErrorMessage } from 'frappe-ui'
import { h, reactive, ref } from 'vue'

let dialogs = ref([])

export let Dialogs = {
  name: 'Dialogs',
  render() {
    return dialogs.value.map((dialog) => {
      return h(
        Dialog,
        {
          options: dialog,
          modelValue: dialog.show,
          'onUpdate:modelValue': (val) => (dialog.show = val),
        },
        () => [
          h('p', { class: 'text-p-base text-gray-700' }, dialog.message),
          h(ErrorMessage, { class: 'mt-2', message: dialog.error }),
        ]
      )
    })
  },
}

export function createDialog(options) {
  let dialog = reactive(options)
  dialog.key = `dialog-${Math.random().toString(36).slice(2, 9)}`
  dialogs.value.push(dialog)
  dialog.show = true
}
