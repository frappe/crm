<template>
  <EmailItem :email="email">
    <template #actions>
      <Badge
        v-if="activity.communication_type == 'Automated Message'"
        :label="__('Notification')"
        variant="subtle"
        theme="green"
      />
      <Dropdown v-if="scheduled" :options="scheduledActions" align="end">
        <Button
          variant="ghost"
          icon="lucide-ellipsis"
          :aria-label="__('Scheduled email actions')"
          :loading="busy"
        />
      </Dropdown>
      <Button
        v-if="!scheduled"
        :tooltip="__('Reply')"
        variant="ghost"
        class="text-ink-gray-7"
        :icon="ReplyIcon"
        @click="reply(activity.data)"
      />
      <Button
        v-if="!scheduled"
        :tooltip="__('Reply All')"
        variant="ghost"
        :icon="ReplyAllIcon"
        class="text-ink-gray-7"
        @click="reply(activity.data, true)"
      />
    </template>
  </EmailItem>
</template>
<script setup>
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import { createDialog } from '@/utils/dialogs'
import { EmailItem } from '@framework/ui/components/ActivityTimeline'
import { Badge, Dropdown, call, dayjsLocal, toast } from 'frappe-ui'
import { reactive, computed, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  emailBox: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['reload'])

const emailBox = reactive(props.emailBox)

const scheduled = computed(() => {
  const { delivery_status, send_after } = props.activity.data
  return delivery_status === 'Scheduled' && !!send_after
})

const busy = ref(false)

const scheduledActions = [
  { label: __('Send now'), icon: 'lucide-send', onClick: sendNow },
  { label: __('Edit'), icon: 'lucide-pencil', onClick: edit },
  {
    label: __('Delete'),
    icon: 'lucide-trash-2',
    theme: 'red',
    onClick: deleteScheduled,
  },
]

function confirm(title, message, label, onConfirm, theme = 'gray') {
  createDialog({
    title,
    message,
    actions: [
      {
        label,
        theme,
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          onConfirm()
        },
      },
    ],
  })
}

async function run(method, success, error) {
  busy.value = true
  try {
    const result = await call(method, { name: props.activity.name })
    toast.success(success)
    emit('reload')
    return result
  } catch (e) {
    toast.error(e?.messages?.[0] || error)
  } finally {
    busy.value = false
  }
}

function sendNow() {
  const at = dayjsLocal(props.activity.data.send_after).format(
    'ddd, D MMM, h:mm A',
  )
  confirm(
    __('Send now?'),
    __('It will be sent right away instead of on {0}.', [at]),
    __('Send now'),
    () =>
      run(
        'crm.api.email.send_scheduled_email_now',
        __('Email sent'),
        __('Failed to send email'),
      ),
  )
}

async function edit() {
  // Editing moves the email into the composer, so don't overwrite a draft
  if (emailBox.hasDraft) {
    toast.error(__('Send or discard the email you are writing first'))
    return
  }
  const draft = await run(
    'crm.api.email.cancel_scheduled_email',
    __('Moved to the composer. Schedule it again when ready.'),
    __('Failed to edit scheduled email'),
  )
  if (draft) emailBox.restoreDraft(draft)
}

function deleteScheduled() {
  confirm(
    __('Delete scheduled email?'),
    __("It won't be sent. This can't be undone."),
    __('Delete'),
    () =>
      run(
        'crm.api.email.cancel_scheduled_email',
        __('Scheduled email deleted'),
        __('Failed to delete scheduled email'),
      ),
    'red',
  )
}

function reply(email, reply_all = false) {
  emailBox.openEmailBox()
  let editor = emailBox.editor
  let message = email.content
  let recipients = email.recipients.split(',').map((r) => r.trim())
  let replyAddresses = []
  for (let addresses of [email.sender, email.recipients, email.cc, email.bcc]) {
    if (!addresses) continue
    for (let address of addresses.split(',')) {
      replyAddresses.push(address.trim())
    }
  }
  editor.replyAddresses = replyAddresses
  editor.toEmails = [email.sender]
  editor.cc = editor.bcc = false
  editor.ccEmails = []
  editor.bccEmails = []

  if (!email.subject.startsWith('Re:')) {
    editor.subject = `Re: ${email.subject}`
  } else {
    editor.subject = email.subject
  }

  if (reply_all) {
    let cc = email.cc?.split(',').map((r) => r.trim())
    let bcc = email.bcc?.split(',').map((r) => r.trim())

    if (cc?.length) {
      recipients = recipients.filter((r) => !cc?.includes(r))
      cc.push(...recipients)
    } else {
      cc = recipients
    }

    editor.cc = !!cc?.length
    editor.bcc = !!bcc?.length

    // An email without cc/bcc gives undefined here; the composer needs arrays
    editor.ccEmails = cc || []
    editor.bccEmails = bcc || []
  }

  let repliedMessage = `<blockquote>${message}</blockquote>`
  let draft = draftBeforeQuote(editor.editor)

  editor.editor
    .chain()
    .clearContent()
    .updateAttributes('paragraph', { class: 'reply-to-content' })
    .insertContent(repliedMessage)
    .focus('all')
    .insertContentAt(0, draft.length ? draft : { type: 'paragraph' })
    .focus('start')
    .run()
}

// Keep what the user already typed, dropping any previously quoted email
function draftBeforeQuote(editor) {
  let draft = []
  let quoted = false
  editor.state.doc.forEach((node) => {
    quoted ||= node.type.name === 'blockquote'
    if (!quoted) draft.push(node.toJSON())
  })
  return draft
}

const email = computed(() => {
  const { data } = props.activity
  return {
    type: 'email',
    key: props.activity.communication_date,
    // a scheduled email shows when it goes out ("in 17 hours"), not when it was written
    timestamp: scheduled.value
      ? props.activity.data.send_after
      : props.activity.communication_date,
    author: { fullname: data.sender_full_name, email: data.sender },
    data: {
      subject: data.subject,
      sender: data.sender,
      to: data.recipients,
      cc: data.cc,
      bcc: data.bcc,
      content: data.content,
      deliveryStatus: data.delivery_status,
      attachments: data.attachments,
    },
  }
})
</script>
