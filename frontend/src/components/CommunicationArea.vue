<template>
  <div class="flex justify-between gap-3 border-t px-10 py-2.5">
    <div class="flex gap-1.5">
      <Button
        ref="sendEmailRef"
        variant="ghost"
        :class="[showEmailBox ? '!bg-gray-300 hover:!bg-gray-200' : '']"
        label="Reply"
        @click="toggleEmailBox()"
      >
        <template #prefix>
          <EmailIcon class="h-4" />
        </template>
      </Button>
      <Button
        variant="ghost"
        label="Comment"
        :class="[showCommentBox ? '!bg-gray-300 hover:!bg-gray-200' : '']"
        @click="toggleCommentBox()"
      >
        <template #prefix>
          <CommentIcon class="h-4" />
        </template>
      </Button>
    </div>
    <div v-if="showEmailBox" class="flex gap-1.5">
      <Button
        label="CC"
        @click="toggleCC()"
        :class="[newEmailEditor.cc ? 'bg-gray-300 hover:bg-gray-200' : '']"
      />
      <Button
        label="BCC"
        @click="toggleBCC()"
        :class="[newEmailEditor.bcc ? 'bg-gray-300 hover:bg-gray-200' : '']"
      />
    </div>
  </div>
  <div
    v-show="showEmailBox"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showEmailBox = false
          newEmail = ''
        },
      }"
      :editable="showEmailBox"
      v-model="doc.data"
      v-model:attachments="attachments"
      :doctype="doctype"
      :subject="subject"
      placeholder="Add a reply..."
    />
  </div>
  <div v-show="showCommentBox">
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showCommentBox = false
          newComment = ''
        },
      }"
      :editable="showCommentBox"
      v-model="doc.data"
      v-model:attachments="attachments"
      :doctype="doctype"
      placeholder="Add a comment..."
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'
import { call } from 'frappe-ui'
import { ref, watch, computed, defineModel, nextTick } from 'vue'

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

const showEmailBox = ref(false)
const showCommentBox = ref(false)
const newEmail = useStorage('emailBoxContent', '')
const newComment = useStorage('commentBoxContent', '')
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)
const sendEmailRef = ref(null)
const attachments = ref([])

const subject = computed(() => {
  let prefix = ''
  if (doc.value.data?.lead_name) {
    prefix = doc.value.data.lead_name
  } else if (doc.value.data?.organization) {
    prefix = doc.value.data.organization
  }
  return `${prefix} (#${doc.value.data.name})`
})

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      newEmailEditor.value.editor.commands.focus()
    }
  }
)

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      newCommentEditor.value.editor.commands.focus()
    }
  }
)

const commentEmpty = computed(() => {
  return !newComment.value || newComment.value === '<p></p>'
})

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === '<p></p>'
})

async function sendMail() {
  let recipients = newEmailEditor.value.toEmails
  let subject = newEmailEditor.value.subject
  let cc = newEmailEditor.value.ccEmails
  let bcc = newEmailEditor.value.bccEmails
  await call('frappe.core.doctype.communication.email.make', {
    recipients: recipients.join(', '),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(', '),
    bcc: bcc.join(', '),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.data.name,
    send_email: 1,
    sender: getUser().name,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function sendComment() {
  await call('frappe.desk.form.utils.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
    content: newComment.value,
    comment_email: getUser().name,
    comment_by: getUser()?.full_name || undefined,
  })
}

async function submitEmail() {
  if (emailEmpty.value) return
  showEmailBox.value = false
  await sendMail()
  newEmail.value = ''
  reload.value = true
  emit('scroll')
}

async function submitComment() {
  if (commentEmpty.value) return
  showCommentBox.value = false
  await sendComment()
  newComment.value = ''
  reload.value = true
  emit('scroll')
}

function toggleCC() {
  newEmailEditor.value.cc = !newEmailEditor.value.cc
  newEmailEditor.value.cc &&
    nextTick(() => {
      newEmailEditor.value.ccInput.setFocus()
    })
}

function toggleBCC() {
  newEmailEditor.value.bcc = !newEmailEditor.value.bcc
  newEmailEditor.value.bcc &&
    nextTick(() => {
      newEmailEditor.value.bccInput.setFocus()
    })
}

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false
  }
  showEmailBox.value = !showEmailBox.value
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false
  }
  showCommentBox.value = !showCommentBox.value
}

defineExpose({ show: showEmailBox, editor: newEmailEditor })
</script>
