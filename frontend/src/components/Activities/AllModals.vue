<template>
  <TaskModal
    v-model="showTaskModal"
    v-model:reloadTasks="activities"
    :task="task"
    :doctype="doctype"
    :doc="doc.data?.name"
    @after="redirect('tasks')"
  />
  <NoteModal
    v-model="showNoteModal"
    v-model:reloadNotes="activities"
    :note="note"
    :doctype="doctype"
    :doc="doc.data?.name"
    @after="redirect('notes')"
  />
</template>
<script setup>
import TaskModal from '@/components/Modals/TaskModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: String,
})

const activities = defineModel()
const doc = defineModel('doc')

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
const showNoteModal = ref(false)
const note = ref({})

function showNote(n) {
  note.value = n || {
    title: '',
    content: '',
  }
  showNoteModal.value = true
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
})
</script>
