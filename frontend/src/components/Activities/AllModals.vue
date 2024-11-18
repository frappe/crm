<template>
  <ToDoModal
    v-model="showToDoModal"
    v-model:reloadToDos="activities"
    :todo="todo"
    :doctype="doctype"
    :doc="doc.data?.name"
    @after="redirect('todos')"
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
import ToDoModal from '@/components/Modals/ToDoModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: String,
})

const activities = defineModel()
const doc = defineModel('doc')

// ToDos
const showToDoModal = ref(false)
const todo = ref({})

function showToDo(t) {
  todo.value = t || {
    title: '',
    description: '',
    allocated_to: '',
    date: '',
    priority: 'Low',
    status: 'Backlog',
  }
  showToDoModal.value = true
}

async function deleteToDo(name) {
  await call('frappe.client.delete', {
    doctype: 'ToDo',
    name,
  })
  activities.value.reload()
}

function updateToDoStatus(status, todo) {
  call('frappe.client.set_value', {
    doctype: 'ToDo',
    name: todo.name,
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
  if (route.name == 'Lead' || route.name == 'Opportunity') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showToDo,
  deleteToDo,
  updateToDoStatus,
  showNote,
})
</script>
