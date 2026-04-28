<template>
<<<<<<< HEAD
  <CallLogModal
    v-if="showCallLogModal"
    v-model="showCallLogModal"
    :data="callLog"
    :referenceDoc="referenceDoc"
    :options="{ afterInsert: () => activities.reload() }"
  />
<<<<<<< HEAD
=======
=======
>>>>>>> 7ecd30cb (refactor: remove CallLogModal and streamline call log handling through useDoctypeModal)
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    :event="activeEvent"
    :doctype="doctype"
    :docname="doc?.name"
  />
<<<<<<< HEAD
  <DoctypeModal
    v-if="showDoctypeModal"
    v-model="showDoctypeModal"
    :doctypeTitle="modalDoctypeTitle"
    :doctype="modalDoctype"
    :docname="modalDocname"
    :defaults="modalDefaults"
    @afterInsert="after"
    @afterUpdate="after"
  />
>>>>>>> 4917cb73 (feat: replace NoteModal with DoctypeModal for improved document handling in AllModals, Deals, and Leads pages)
=======
>>>>>>> 239cf06e (refactor: use global doctypeModal composable in AllModals)
</template>
<script setup>
<<<<<<< HEAD
import CallLogModal from '@/components/Modals/CallLogModal.vue'
<<<<<<< HEAD
=======
=======
>>>>>>> 7ecd30cb (refactor: remove CallLogModal and streamline call log handling through useDoctypeModal)
import EventModal from '@/components/Modals/EventModal.vue'
import { showEventModal, activeEvent } from '@/composables/event'
<<<<<<< HEAD
>>>>>>> 4917cb73 (feat: replace NoteModal with DoctypeModal for improved document handling in AllModals, Deals, and Leads pages)
=======
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
>>>>>>> 239cf06e (refactor: use global doctypeModal composable in AllModals)
import { call } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const activities = defineModel({ type: Object })
<<<<<<< HEAD
const doc = defineModel('doc', { type: Object })
=======

const { showModal } = useDoctypeModal()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// Event
function showEvent(e) {
  showEventModal.value = true
  activeEvent.value = e
}
>>>>>>> 239cf06e (refactor: use global doctypeModal composable in AllModals)

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
