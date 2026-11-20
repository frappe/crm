// Stands in for @whatsapp/ui when CRM is built without the whatsapp app beside it.
// `__WHATSAPP_UI__` is false in that build, so WhatsApp stays hidden and nothing here
// is shown: these only let the imports resolve and Activities set up its state.
import { reactive } from 'vue'

const nothing = () => null

export const AccountForm = nothing
export const MessageInput = nothing
export const MessageList = nothing
export const TemplateContent = nothing
export const TemplateForm = nothing
export const TemplatePreview = nothing

export function useMessages() {
  return reactive({
    messages: [],
    loading: false,
    error: null,
    reload() {},
    react() {},
    setReplyTo() {},
  })
}

export function useAccount() {
  return reactive({ doc: {}, loading: false })
}

export function useTemplate() {
  return reactive({ doc: {}, loading: false })
}

export function useTemplates() {
  return reactive({ templates: [], loading: false })
}

export function useAppendToggle() {
  return {}
}

export function serverErrorMessage() {
  return ''
}
