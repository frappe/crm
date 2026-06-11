import { ref } from 'vue'

const show = ref(false)
const doctype = ref('')
const name = ref('')
const title = ref('')
const defaults = ref({})
const callbacks = ref({})

function showModal({
  name: _name = null,
  doctype: _doctype,
  title: _title = '',
  defaults: _defaults = {},
  callbacks: _callbacks = {},
}) {
  name.value = _name
  doctype.value = _doctype
  title.value = _title
  defaults.value = _defaults
  callbacks.value = _callbacks
  show.value = true
}

function triggerCallback(event, ...args) {
  callbacks.value[event]?.(...args)
}

export function useDoctypeModal() {
  return {
    show,
    doctype,
    name,
    title,
    defaults,
    showModal,
    triggerCallback,
  }
}
