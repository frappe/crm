import { ref } from 'vue'

const show = ref(false)
const doctype = ref('')
const name = ref('')
const title = ref('')
const defaults = ref({})
const callbacks = ref({})

function showModal(_name, _doctype, _title, _defaults = {}, _callbacks = {}) {
  doctype.value = _doctype
  name.value = _name
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
