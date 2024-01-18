<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode ? 'Edit Note' : 'Create Note',
      size: 'xl',
      actions: [
        {
          label: editMode ? 'Update' : 'Create',
          variant: 'solid',
          onClick: () => updateNote(),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Title</div>
          <TextInput
            ref="title"
            variant="outline"
            v-model="_note.title"
            placeholder="Add title"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Content</div>
          <TextEditor
            variant="outline"
            ref="content"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubbleMenu="true"
            :content="_note.content"
            @change="(val) => (_note.content = val)"
            placeholder="Type a Content"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextEditor, call } from 'frappe-ui'
import { ref, defineModel, nextTick, watch } from 'vue'

const props = defineProps({
  note: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const notes = defineModel('reloadNotes')

const emit = defineEmits(['after'])

const title = ref(null)
const editMode = ref(false)
let _note = ref({})

async function updateNote() {
  if (
    props.note.title === _note.value.title &&
    props.note.content === _note.value.content
  )
    return

  if (_note.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: _note.value.name,
      fieldname: _note.value,
    })
    if (d.name) {
      notes.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Note',
        title: _note.value.title,
        content: _note.value.content,
        reference_doctype: props.doctype,
        reference_docname: props.doc || '',
      },
    })
    if (d.name) {
      notes.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      title.value.el.focus()
      _note.value = { ...props.note }
      if (_note.value.title) {
        editMode.value = true
      }
    })
  }
)
</script>
