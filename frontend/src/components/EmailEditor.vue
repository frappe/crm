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
      <div
        class="mx-10 flex items-center gap-2 border-t py-2.5"
        :class="[cc || bcc ? '' : 'border-b']"
      >
        <span class="text-xs text-gray-500">TO:</span>
        <MultiselectInput
          class="flex-1"
          v-model="toEmails"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
      <div
        v-if="cc"
        class="mx-10 flex items-center gap-2 py-2.5"
        :class="bcc ? '' : 'border-b'"
      >
        <span class="text-xs text-gray-500">CC:</span>
        <MultiselectInput
          class="flex-1"
          v-model="ccEmails"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
      <div v-if="bcc" class="mx-10 flex items-center gap-2 border-b py-2.5">
        <span class="text-xs text-gray-500">BCC:</span>
        <MultiselectInput
          class="flex-1"
          v-model="bccEmails"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
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
        <div
          class="flex justify-between gap-2 overflow-hidden border-t px-10 py-2.5"
        >
          <div class="flex items-center overflow-x-auto">
            <TextEditorFixedMenu
              class="-ml-1"
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
            <Button v-bind="discardButtonProps || {}" label="Discard" />
            <Button
              variant="solid"
              v-bind="submitButtonProps || {}"
              label="Submit"
            />
          </div>
        </div>
      </div>
    </template>
  </TextEditor>
</template>

<script setup>
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import MultiselectInput from '@/components/Controls/MultiselectInput.vue'
import { TextEditorFixedMenu, TextEditor, FileUploader } from 'frappe-ui'
import { validateEmail } from '@/utils'
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
const cc = ref(false)
const bcc = ref(false)

const toEmails = ref(modelValue.value.email ? [modelValue.value.email] : [])
const ccEmails = ref([])
const bccEmails = ref([])

const editor = computed(() => {
  return textEditor.value.editor
})

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment)
}

defineExpose({ editor, cc, bcc, toEmails, ccEmails, bccEmails })

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
