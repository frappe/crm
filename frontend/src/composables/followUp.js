import { useDoctypeModal } from '@/composables/doctypeModal'
import { sessionStore } from '@/stores/session'
import { call } from 'frappe-ui'

export function createFollowUp({ doctype, docname, title, dueDate }) {
  return call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Task',
      ...followUpDefaults({ doctype, docname, title }),
      due_date: dueDate,
    },
  })
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
