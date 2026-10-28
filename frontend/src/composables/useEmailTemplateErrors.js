import { toast } from 'frappe-ui'
import { ref, watch } from 'vue'

// raised by crm/overrides/email_template.py when a variable doesn't exist on the doctype
const FIELD_BY_EXC_TYPE = {
  InvalidSubjectVariableError: 'subject',
  InvalidContentVariableError: 'content',
}

export function useEmailTemplateErrors(template) {
  const errors = ref({})

  // clear a field's error as soon as the user edits it
  watch(
    () => template.value.name,
    () => (errors.value.name = ''),
  )
  watch(
    () => template.value.subject,
    () => (errors.value.subject = ''),
  )
  watch(
    () => [
      template.value.response,
      template.value.response_html,
      template.value.content_type,
    ],
    () => (errors.value.content = ''),
  )

  function validate() {
    errors.value = {}
    if (!template.value.name) {
      errors.value.name = __('Name is required')
    }
    if (!template.value.subject) {
      errors.value.subject = __('Subject is required')
    }
    const content =
      template.value.content_type === 'HTML'
        ? template.value.response_html
        : template.value.response
    if (!content) {
      errors.value.content = __('Content is required')
    }
    return !Object.values(errors.value).some(Boolean)
  }

  function setServerError(error, fallback) {
    const message = error.messages?.[0] || fallback
    const field = FIELD_BY_EXC_TYPE[error.exc_type]
    if (field) {
      errors.value[field] = message
    } else {
      toast.error(message)
    }
  }

  return { errors, validate, setServerError }
}
