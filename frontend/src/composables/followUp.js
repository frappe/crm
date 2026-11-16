import { useDoctypeModal } from '@/composables/doctypeModal'
import { sessionStore } from '@/stores/session'
import { useCrmOnboarding } from '@/composables/onboarding'
import { useTelemetry } from '@framework/ui/telemetry'
import { call, toast } from 'frappe-ui'

export function createFollowUp({ doctype, docname, title, dueDate }) {
  return call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Task',
      ...followUpDefaults({ doctype, docname, title }),
      due_date: dueDate,
    },
  })
}

// Each place that adds a follow-up shows the same toast and records it the same way.
export function useAddFollowUp(source) {
  const { completeStep } = useCrmOnboarding()
  const { capture } = useTelemetry()

  function recordCreated(doctype) {
    completeStep('create_first_task')
    capture('follow_up_created', { doctype, ...(source && { source }) })
  }

  async function addFollowUp(fields) {
    const task = await createFollowUp(fields)
    toast.success(__('Follow-up added'))
    recordCreated(fields.doctype)
    return task
  }

  return { addFollowUp, recordCreated }
}

export function rescheduleFollowUp(task, dueDate) {
  return call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: { due_date: dueDate, all_day: 1 },
  })
}

export function openFollowUpForm({ doctype, docname, title, afterInsert }) {
  const { showModal } = useDoctypeModal()
  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: followUpDefaults({ doctype, docname, title }),
    callbacks: { afterInsert },
  })
}

function followUpDefaults({ doctype, docname, title }) {
  return {
    title,
    status: 'Todo',
    priority: 'Low',
    all_day: 1,
    assigned_to: sessionStore().user,
    reference_doctype: docname ? doctype : null,
    reference_docname: docname || null,
  }
}
