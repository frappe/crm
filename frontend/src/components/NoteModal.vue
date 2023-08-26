<template>
  <Dialog v-model="show" :options="{ size: '4xl' }" @close="updateNote">
    <template #body-title><div></div></template>
    <template #body-content>
      <div
        class="flex flex-col gap-2 px-20 mt-5 mb-10 min-h-[400px] max-h-[500px] overflow-auto"
      >
        <TextInput
          ref="title"
          type="text"
          class="!text-[30px] !h-10 !font-semibold bg-white border-none hover:bg-white focus:!shadow-none focus-visible:!ring-0"
          v-model="updatedNote.title"
          placeholder="Untitled note"
        />
        <TextEditor
          ref="content"
          editor-class="!prose-sm !leading-5 max-w-none p-2 overflow-auto focus:outline-none"
          :bubbleMenu="true"
          :content="updatedNote.content"
          @change="(val) => (updatedNote.content = val)"
          placeholder="Type something and press enter"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextInput, TextEditor, Dialog } from 'frappe-ui'
import { ref, defineModel, nextTick, watch } from 'vue'

const props = defineProps({
  note: {
    type: Object,
    default: {
      title: '',
      content: '',
    },
  },
})

const show = defineModel()
const emit = defineEmits(['updateNote'])

const title = ref(null)

let updatedNote = ref({
  title: '',
  content: '',
})

function updateNote() {
  if (
    props.note.title !== updatedNote.value.title ||
    props.note.content !== updatedNote.value.content
  ) {
    emit('updateNote', updatedNote.value)
  }
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    nextTick(() => {
      title.value.el.focus()
      updatedNote.value = { ...props.note }
    })
  }
)
</script>
