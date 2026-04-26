<template>
  <TaskModal
    v-if="showTaskModal"
    v-model="showTaskModal"
    v-model:reloadTasks="activities"
    :task="task"
    :doctype="doctype"
    :docname="doc?.name"
    @after="redirect('tasks')"
  />
  <CallLogModal
    v-if="showCallLogModal"
    v-model="showCallLogModal"
    :data="callLog"
    :referenceDoc="referenceDoc"
    :options="{ afterInsert: () => activities.reload() }"
  />
<<<<<<< HEAD
=======
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
import TaskModal from '@/components/Modals/TaskModal.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
<<<<<<< HEAD
=======
import EventModal from '@/components/Modals/EventModal.vue'
import { showEventModal, activeEvent } from '@/composables/event'
<<<<<<< HEAD
>>>>>>> 4917cb73 (feat: replace NoteModal with DoctypeModal for improved document handling in AllModals, Deals, and Leads pages)
=======
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
>>>>>>> 239cf06e (refactor: use global doctypeModal composable in AllModals)
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const activities = defineModel({ type: Object })
<<<<<<< HEAD
const doc = defineModel('doc', { type: Object })
=======

const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// Event
function showEvent(e) {
  showEventModal.value = true
  activeEvent.value = e
}
>>>>>>> 239cf06e (refactor: use global doctypeModal composable in AllModals)

// Tasks
const showTaskModal = ref(false)
const task = ref({})

function showTask(t) {
  task.value = t || {
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    priority: 'Low',
    status: 'Backlog',
  }
  showTaskModal.value = true
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
const { showModal } = useDoctypeModal()

function showNote(note) {
  showModal(
    note?.name,
    'FCRM Note',
    'Note',
    {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    {
      afterInsert: afterDoctype,
      afterUpdate: afterDoctype,
    },
  )
}

function afterDoctype(d) {
  activities.value.reload()
  updateOnboardingStep('create_first_note')
  capture('note_created')

  let redirectHash = ''

  if (d.doctype == 'FCRM Note') {
    redirectHash = 'notes'
  }

  redirect(redirectHash)
}

// Call Logs
const showCallLogModal = ref(false)
const callLog = ref({})
const referenceDoc = ref({})

function createCallLog() {
  let doctype = props.doctype
  let docname = props.doc?.name
  referenceDoc.value = { ...props.doc }
  callLog.value = {
    reference_doctype: doctype,
    reference_docname: docname,
  }
  showCallLogModal.value = true
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
