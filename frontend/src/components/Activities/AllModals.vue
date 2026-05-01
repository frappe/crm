<template>
  <div></div>
</template>
<script setup>
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { call } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
})

const activities = defineModel({ type: Object })

const { showModal } = useDoctypeModal()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// Tasks
function showTask(task) {
  showModal({
    name: task?.name,
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  activities.value.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    activities.value.reload()
  })
}

// Notes
function showNote(note) {
  showModal({
    name: note?.name,
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

function afterDoctype(d, isInsert = false) {
  activities.value.reload()

  let name =
    d.doctype == 'FCRM Note'
      ? 'note'
      : d.doctype == 'CRM Task'
        ? 'task'
        : 'call_log'

  let redirectHash = name + 's'
  if (d.doctype == 'CRM Call Log') {
    redirectHash = 'calls'
  }

  if (isInsert) {
    updateOnboardingStep('create_first_' + name)
    capture(name + '_created')
  } else {
    capture(name + '_updated')
  }

  redirect(redirectHash)
}

// Call Logs
function createCallLog() {
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
      reference_doc: { ...props.doc },
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

// common
const route = useRoute()
const router = useRouter()

function redirect(tabName) {
  if (route.name == 'Lead' || route.name == 'Deal') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  createCallLog,
})
</script>
