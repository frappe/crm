<template>
  <div
    v-if="title !== 'Data'"
    class="mx-4 my-3 flex items-center justify-between text-lg font-medium sm:mx-10 sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __(title) }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      :label="__('New email')"
      iconLeft="plus"
      @click="emailBox.show = true"
    />
    <Button
      v-else-if="title == 'Comments'"
      variant="solid"
      :label="__('New comment')"
      iconLeft="plus"
      @click="emailBox.showComment = true"
    />
    <MultiActionButton
      v-else-if="title == 'Calls'"
      variant="solid"
      :options="callActions"
    />
    <Button
      v-else-if="title == 'Events'"
      variant="solid"
      @click="modalRef.showEvent()"
    >
      <template #prefix>
        <EventIcon class="h-4 w-4" />
      </template>
      <span>{{ __('Schedule an event') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      :label="__('New note')"
      iconLeft="plus"
      @click="modalRef.showNote()"
    />
    <Button
      v-else-if="title == 'Tasks'"
      variant="solid"
      :label="__('New task')"
      iconLeft="plus"
      @click="modalRef.showTask()"
    />
    <Button
      v-else-if="title == 'Attachments'"
      variant="solid"
      :label="__('Upload attachment')"
      iconLeft="plus"
      @click="showFilesUploader = true"
    />
    <div class="flex gap-2 shrink-0" v-else-if="title == 'WhatsApp'">
      <Button
        :label="__('Send template')"
        @click="showWhatsappTemplates = true"
      />
      <Button
        variant="solid"
        :label="__('New message')"
        iconLeft="plus"
        @click="whatsappBox.show()"
      />
    </div>
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template v-slot="{ open }">
        <Button
          variant="solid"
          class="flex items-center gap-1"
          :label="__('New')"
          iconLeft="plus"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import MultiActionButton from '@/components/MultiActionButton.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { Dropdown } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  tabs: Array,
  title: String,
  doc: Object,
  modalRef: Object,
  emailBox: Object,
  whatsappBox: Object,
})

const { makeCall } = globalStore()

const tabIndex = defineModel()
const showWhatsappTemplates = defineModel('showWhatsappTemplates')
const showFilesUploader = defineModel('showFilesUploader')

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('New email'),
      onClick: () => (props.emailBox.show = true),
    },
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('New comment'),
      onClick: () => (props.emailBox.showComment = true),
    },
    {
      icon: h(EventIcon, { class: 'h-4 w-4' }),
      label: __('Schedule an event'),
      onClick: () => props.modalRef.showEvent(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Log a call'),
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a call'),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New note'),
      onClick: () => props.modalRef.showNote(),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('New WhatsApp message'),
      onClick: () => (tabIndex.value = getTabIndex('WhatsApp')),
      condition: () => whatsappEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

function getTabIndex(name) {
  return props.tabs.findIndex((tab) => tab.name === name)
}

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a call'),
      icon: 'plus',
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      label: __('Make a call'),
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
