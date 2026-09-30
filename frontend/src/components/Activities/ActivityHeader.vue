<template>
  <div
    v-if="title !== 'Data'"
    class="mx-3 my-3 flex items-center justify-between text-lg-medium sm:mx-10 sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-2xl-semibold text-ink-gray-8">
      {{ __(title) }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      :label="__('New Email')"
      iconLeft="lucide-plus"
      @click="emailBox.openEmailBox()"
    />
    <Button
      v-else-if="title == 'Comments'"
      variant="solid"
      :label="__('New Comment')"
      iconLeft="lucide-plus"
      @click="emailBox.openCommentBox()"
    />
    <MultiActionButton
      v-else-if="title == 'Calls'"
      variant="solid"
      :options="callActions"
    />
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      :label="__('New Note')"
      iconLeft="lucide-plus"
      @click="modalRef.showNote()"
    />
    <Button
      v-else-if="title == 'Tasks'"
      variant="solid"
      :label="__('New Task')"
      iconLeft="lucide-plus"
      @click="modalRef.showTask()"
    />
    <Button
      v-else-if="title == 'Attachments'"
      variant="solid"
      :label="__('Upload Attachment')"
      iconLeft="lucide-plus"
      @click="showFilesUploader = true"
    />
    <!-- WhatsApp composes from the input itself, so the header offers no action here -->
    <Dropdown
      v-else-if="title != 'WhatsApp'"
      :options="defaultActions"
      @click.stop
    >
      <template #default="{ open }">
        <Button
          variant="solid"
          class="flex items-center gap-1"
          :label="__('New')"
          iconLeft="lucide-plus"
          :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import MultiActionButton from '@/components/MultiActionButton.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import { Dropdown } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  modalRef: { type: Object, default: () => ({}) },
})

const { makeCall } = globalStore()

const activeTab = defineModel({ type: String })
const showFilesUploader = defineModel('showFilesUploader', { type: Boolean })
const emailBox = defineModel('emailBox', { type: Object, default: () => ({}) })

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('Email'),
      onClick: () => emailBox.value.openEmailBox(),
    },
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('Comment'),
      onClick: () => emailBox.value.openCommentBox(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Log a Call'),
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('Note'),
      onClick: () => props.modalRef.showNote(),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('Task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('WhatsApp Message'),
      onClick: () => (activeTab.value = 'whatsapp'),
      condition: () => whatsappEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a Call'),
      icon: 'lucide-plus',
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      label: __('Make a Call'),
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
  ]

  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})
</script>
