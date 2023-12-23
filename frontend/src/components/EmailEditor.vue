<template>
  <TextEditor
    ref="textEditor"
    :editor-class="['prose-sm max-w-none', editable && 'min-h-[7rem]']"
    :content="value"
    @change="editable ? $emit('change', $event) : null"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
  >
    <template #top>
      <div class="mx-10 border-b border-t py-2.5">
        <span class="text-xs text-gray-500">TO:</span>
        <span
          v-if="modelValue.email"
          class="ml-2 cursor-pointer rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-800"
        >
          {{ modelValue.email }}
        </span>
      </div>
    </template>
    <template v-slot:editor="{ editor }">
      <EditorContent
        :class="[editable && 'mx-10 max-h-[50vh] overflow-y-auto py-3']"
        :editor="editor"
      />
    </template>
    <template v-slot:bottom>
      <div v-if="editable" class="flex flex-col gap-2">
        <div class="flex flex-wrap gap-2 px-10">
          <AttachmentItem
            v-for="a in attachments"
            :key="a.file_url"
            :label="a.file_name"
          >
            <template #suffix>
              <FeatherIcon
                class="h-3.5"
                name="x"
                @click.stop="removeAttachment(a)"
              />
            </template>
          </AttachmentItem>
        </div>
        <div class="flex justify-between border-t px-10 py-2.5">
          <div class="flex items-center">
            <TextEditorFixedMenu
              class="-ml-1 overflow-x-auto"
              :buttons="textEditorMenuButtons"
            />
            <FileUploader
              :upload-args="{
                doctype: doctype,
                docname: modelValue.name,
                private: true,
              }"
              @success="(f) => attachments.push(f)"
            >
              <template #default="{ openFileSelector }">
                <Button
                  theme="gray"
                  variant="ghost"
                  @click="openFileSelector()"
                >
                  <template #icon>
                    <AttachmentIcon class="h-4" />
                  </template>
                </Button>
              </template>
            </FileUploader>
          </div>
          <div class="mt-2 flex items-center justify-end space-x-2 sm:mt-0">
            <Button v-bind="discardButtonProps || {}"> Discard </Button>
            <Button variant="solid" v-bind="submitButtonProps || {}">
              Submit
            </Button>
          </div>
        </div>
      </div>
    </template>
  </TextEditor>
</template>

<script setup>
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import {
  TextEditorFixedMenu,
  TextEditor,
  FileUploader,
  FeatherIcon,
} from 'frappe-ui'
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
  doctype: {
    type: String,
    default: 'CRM Lead',
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
const attachments = defineModel('attachments')

const textEditor = ref(null)

const editor = computed(() => {
  return textEditor.value.editor
})

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment)
}

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
