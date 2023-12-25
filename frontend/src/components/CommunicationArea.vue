<template>
  <div class="flex justify-between gap-3 border-t px-10 py-2.5">
    <div class="flex gap-1.5">
      <Button
        ref="sendEmailRef"
        variant="ghost"
        :class="[showCommunicationBox ? '!bg-gray-300 hover:!bg-gray-200' : '']"
        label="Reply"
        @click="showCommunicationBox = !showCommunicationBox"
      >
        <template #prefix>
          <EmailIcon class="h-4" />
        </template>
      </Button>
      <!-- <Button variant="ghost" label="Comment">
        <template #prefix>
          <CommentIcon class="h-4" />
        </template>
      </Button> -->
    </div>
    <div v-if="showCommunicationBox" class="flex gap-1.5">
      <Button
        label="CC"
        @click="newEmailEditor.cc = !newEmailEditor.cc"
        :class="[newEmailEditor.cc ? 'bg-gray-300 hover:bg-gray-200' : '']"
      />
      <Button
        label="BCC"
        @click="newEmailEditor.bcc = !newEmailEditor.bcc"
        :class="[newEmailEditor.bcc ? 'bg-gray-300 hover:bg-gray-200' : '']"
      />
    </div>
  </div>
  <div
    v-show="showCommunicationBox"
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
      v-model:attachments="attachments"
      :doctype="doctype"
      placeholder="Add a reply..."
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { ref, watch, computed, defineModel } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const doc = defineModel()
const reload = defineModel('reload')

const emit = defineEmits(['scroll'])

const { getUser } = usersStore()

const showCommunicationBox = ref(false)
const newEmail = ref('')
const newEmailEditor = ref(null)
const sendEmailRef = ref(null)
const attachments = ref([])

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
    recipients: doc.value.data.email,
    attachments: attachments.value.map((x) => x.name),
    cc: '',
    bcc: '',
    subject: 'Email from Agent',
    content: newEmail.value,
    doctype: props.doctype,
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
  emit('scroll')
}

defineExpose({ show: showCommunicationBox, editor: newEmailEditor })
</script>
