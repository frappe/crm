<template>
  <div class="flex gap-3 px-10 pb-6 pt-2">
    <UserAvatar
      :user="getUser().name"
      size="xl"
      :class="showCommunicationBox ? 'mt-3' : ''"
    />
    <Button
      ref="sendEmailRef"
      variant="outline"
      size="md"
      class="inline-flex h-8.5 w-full justify-between"
      @click="showCommunicationBox = true"
      v-show="!showCommunicationBox"
    >
      <div class="text-base text-gray-600">Add a reply...</div>
      <template #suffix>
        <div class="flex gap-3">
          <!-- <FeatherIcon name="paperclip" class="h-4" /> -->
        </div>
      </template>
    </Button>
    <div
      v-show="showCommunicationBox"
      class="w-full rounded-lg border bg-white p-4 focus-within:border-gray-400"
      @keydown.ctrl.enter.capture.stop="submitComment"
      @keydown.meta.enter.capture.stop="submitComment"
    >
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
        v-model="doc.data"
        placeholder="Add a reply..."
      />
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailEditor from '@/components/EmailEditor.vue'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { ref, watch, computed, defineModel } from 'vue'

const doc = defineModel()
const reload = defineModel('reload')

const { getUser } = usersStore()

const showCommunicationBox = ref(false)
const newEmail = ref('')
const newEmailEditor = ref(null)
const sendEmailRef = ref(null)

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
  let doctype = 'CRM Lead'
  if (doc.value.data.lead) {
    doctype = 'CRM Deal'
  }

  await call('frappe.core.doctype.communication.email.make', {
    recipients: doc.value.data.email,
    cc: '',
    bcc: '',
    subject: 'Email from Agent',
    content: newEmail.value,
    doctype: doctype,
    name: doc.value.data.name,
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
  reload.value = true
}

defineExpose({ show: showCommunicationBox })
</script>
