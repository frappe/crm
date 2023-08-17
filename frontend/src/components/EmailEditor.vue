<template>
  <TextEditor
    ref="textEditor"
    :editor-class="['prose-sm max-w-none', editable && 'min-h-[4rem]']"
    :content="value"
    @change="editable ? $emit('change', $event) : null"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
  >
    <template #top>
      <div class="mb-2">
        <span class="text-base text-gray-600">To:</span>
        <span
          v-if="modelValue.email"
          class="ml-2 bg-gray-100 px-2 py-1 rounded-md text-sm text-gray-800 cursor-pointer"
          >{{ modelValue.email }}</span
        >
      </div>
    </template>
    <template v-slot:editor="{ editor }">
      <EditorContent
        :class="[editable && 'max-h-[50vh] overflow-y-auto']"
        :editor="editor"
      />
    </template>
    <template v-slot:bottom>
      <div
        v-if="editable"
        class="mt-2 flex flex-col justify-between sm:flex-row sm:items-center"
      >
        <TextEditorFixedMenu
          class="-ml-1 overflow-x-auto"
          :buttons="textEditorMenuButtons"
        />
        <div class="mt-2 flex items-center justify-end space-x-2 sm:mt-0">
          <Button v-bind="discardButtonProps || {}"> Discard </Button>
          <Button variant="solid" v-bind="submitButtonProps || {}">
            Submit
          </Button>
        </div>
      </div>
    </template>
  </TextEditor>
</template>

<script setup>
import { TextEditorFixedMenu, TextEditor } from 'frappe-ui'
import { EditorContent } from '@tiptap/vue-3'
import { ref, computed, defineModel } from 'vue'

const props = defineProps({
  value: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: null,
  },
  editable: {
    type: Boolean,
    default: true,
  },
  editorProps: {
    type: Object,
    default: () => ({}),
  },
  submitButtonProps: {
    type: Object,
    default: () => ({}),
  },
  discardButtonProps: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['change'])
const modelValue = defineModel()

const textEditor = ref(null)

const editor = computed(() => {
  return textEditor.value.editor
})

defineExpose({ editor })

const textEditorMenuButtons = [
  'Paragraph',
  ['Heading 2', 'Heading 3', 'Heading 4', 'Heading 5', 'Heading 6'],
  'Separator',
  'Bold',
  'Italic',
  'Separator',
  'Bullet List',
  'Numbered List',
  'Separator',
  'Align Left',
  'Align Center',
  'Align Right',
  'FontColor',
  'Separator',
  'Image',
  'Video',
  'Link',
  'Blockquote',
  'Code',
  'Horizontal Rule',
  [
    'InsertTable',
    'AddColumnBefore',
    'AddColumnAfter',
    'DeleteColumn',
    'AddRowBefore',
    'AddRowAfter',
    'DeleteRow',
    'MergeCells',
    'SplitCell',
    'ToggleHeaderColumn',
    'ToggleHeaderRow',
    'ToggleHeaderCell',
    'DeleteTable',
  ],
]
</script>
