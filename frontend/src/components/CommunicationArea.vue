<template>
  <div class="max-w-[81.7%] pl-16 p-4 pt-2">
    <button
      class="flex gap-2 w-full items-center rounded-lg p-2 bg-gray-100 hover:bg-gray-200"
      @click="showCommunicationBox = true"
      v-show="!showCommunicationBox"
    >
      <UserAvatar :user="getUser().name" size="sm" />
      <div class="text-base text-gray-600">Add a reply...</div>
    </button>
    <div
      v-show="showCommunicationBox"
      class="w-full rounded-lg border bg-white p-4 focus-within:border-gray-400"
      @keydown.ctrl.enter.capture.stop="submitComment"
      @keydown.meta.enter.capture.stop="submitComment"
    >
      <div class="mb-4 flex items-center">
        <UserAvatar :user="getUser().name" size="sm" />
        <span class="ml-2 text-base font-medium text-gray-900">
          {{ getUser().full_name }}
        </span>
      </div>
      <EmailEditor
        ref="newEmailEditor"
        :value="newEmail"
        @change="onNewEmailChange"
        :submitButtonProps="{
          variant: 'solid',
          onClick: submitComment,
          disabled: emailEmpty,
        }"
        :discardButtonProps="{
          onClick: () => {
            showCommunicationBox = false
            newEmail = ''
          },
        }"
        :editable="showCommunicationBox"
        v-model="modelValue.data"
        placeholder="Add a reply..."
      />
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailEditor from '@/components/EmailEditor.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { usersStore } from '@/stores/users'
import { Tooltip, call, Button } from 'frappe-ui'
import { ref, watch, computed, defineModel } from 'vue'

const modelValue = defineModel()

const { getUser } = usersStore()

const showCommunicationBox = ref(false)
const newEmail = ref('')
const newEmailEditor = ref(null)

watch(
  () => showCommunicationBox.value,
  (value) => {
    if (value) {
      newEmailEditor.value.editor.commands.focus()
    }
  }
)

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === '<p></p>'
})

const onNewEmailChange = (value) => {
  newEmail.value = value
}

async function sendMail() {
  await call('frappe.core.doctype.communication.email.make', {
    recipients: modelValue.value.data.email,
    cc: '',
    bcc: '',
    subject: 'Email from Agent',
    content: newEmail.value,
    doctype: 'CRM Lead',
    name: modelValue.value.data.name,
    send_email: 1,
    sender: getUser().name,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function submitComment() {
  if (emailEmpty.value) return
  showCommunicationBox.value = false
  await sendMail()
  newEmail.value = ''
  modelValue.value.reload()
}

function openPhoneCallDialog() {
  //
}
</script>
