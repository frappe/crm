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
</template>
<script setup>
import TaskModal from '@/components/Modals/TaskModal.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
import DoctypeModal from '@/components/Modals/DoctypeModal.vue'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const activities = defineModel({ type: Object })
const doc = defineModel('doc', { type: Object })

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
function showNote(note) {
  showDoctype(note?.name, 'FCRM Note', 'Note', {
    reference_doctype: props.doctype,
    reference_docname: props.doc?.name,
  })
}

// Doctype Modal (Notes, Emails, etc)
const showDoctypeModal = ref(false)
const modalDoctypeTitle = ref('')
const modalDoctype = ref('')
const modalDocname = ref('')
const modalDefaults = ref({})

function showDoctype(name, doctype, doctypeTitle, defaults = {}) {
  modalDoctypeTitle.value = doctypeTitle
  modalDoctype.value = doctype
  modalDocname.value = name || null
  modalDefaults.value = defaults
  showDoctypeModal.value = true
}

function after(d) {
  activities.value.reload()

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
