<template>
  <div :id="activity.name">
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <UserAvatar class="mr-1" :user="activity.owner" size="md" />
        <span class="font-medium text-ink-gray-8">
          {{ activity.owner_name }}
        </span>
        <span>{{ __('added a') }}</span>
        <span class="max-w-xs truncate font-medium text-ink-gray-8">
          {{ __('comment') }}
        </span>
      </div>
      <div class="ml-auto flex items-center gap-1 whitespace-nowrap">
        <TimelineTimestamp :date="activity.creation" />
        <Dropdown
          v-if="isOwner && !editing"
          :options="menuOptions"
          placement="right"
          @click="confirmingDelete = false"
        >
          <Button
            icon="lucide-more-horizontal"
            variant="ghost"
            class="!h-6 !w-6"
          />
        </Dropdown>
      </div>
    </div>
    <div
      class="rounded bg-surface-gray-1 px-3 py-[7.5px] text-base leading-6 transition-all duration-300 ease-in-out"
    >
      <template v-if="editing">
        <TextEditor
          :content="editContent"
          :editable="true"
          :editor-class="['prose-sm max-w-none min-h-[3rem]']"
          @change="editContent = $event"
        />
        <div class="mt-2 flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="cancelEdit" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="saveEdit"
          />
        </div>
      </template>
      <template v-else>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="prose-f" v-html="sanitizeHTML(activity.content)" />
        <div
          v-if="activity.attachments?.length"
          class="mt-2 flex flex-wrap gap-2"
        >
          <AttachmentItem
            v-for="a in activity.attachments"
            :key="a.file_url"
            :label="a.file_name"
            :url="a.file_url"
          />
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import { Dropdown, Button, TextEditor, call, toast } from 'frappe-ui'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { sanitizeHTML, ConfirmDelete } from '@/utils'
import { sessionStore } from '@/stores/session'
import { computed, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['reload'])

const { user } = sessionStore()

const isOwner = computed(() => props.activity.owner === user)

const editing = ref(false)
const saving = ref(false)
const editContent = ref('')
const confirmingDelete = ref(false)

const menuOptions = computed(() => [
  {
    label: __('Edit'),
    icon: 'edit-2',
    onClick: startEdit,
  },
  ...ConfirmDelete({
    onConfirmDelete: deleteComment,
    isConfirmingDelete: confirmingDelete,
  }),
])

function startEdit() {
  editContent.value = props.activity.content || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
}

async function saveEdit() {
  if (editContent.value === props.activity.content) {
    editing.value = false
    return
  }
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'Comment',
      name: props.activity.name,
      fieldname: 'content',
      value: editContent.value,
    })
    editing.value = false
    emit('reload')
  } catch (e) {
    toast.error(__('Failed to update comment'))
  } finally {
    saving.value = false
  }
}

async function deleteComment() {
  try {
    await call('frappe.client.delete', {
      doctype: 'Comment',
      name: props.activity.name,
    })
    emit('reload')
  } catch (e) {
    toast.error(__('Failed to delete comment'))
  }
}
</script>
