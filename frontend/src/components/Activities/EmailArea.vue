<template>
  <div
    class="cursor-pointer flex flex-col rounded-5 shadow-sm bg-surface-elevation-1 px-3 py-1.5 text-base transition-all duration-300 ease-in-out"
  >
    <div
      class="-mb-0.5 flex items-center justify-between gap-2 truncate text-ink-gray-9"
    >
      <div class="flex items-center gap-2 truncate">
        <span>{{ activity.data.sender_full_name }}</span>
        <span class="sm:flex hidden text-sm text-ink-gray-5">
          {{ '<' + activity.data.sender + '>' }}
        </span>
        <Badge
          v-if="activity.communication_type == 'Automated Message'"
          :label="__('Notification')"
          variant="subtle"
          theme="green"
        />
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <Badge
          v-if="status.label"
          :label="__(status.label)"
          variant="subtle"
          :theme="status.color"
        />
        <TimelineTimestamp
          :date="
            scheduled ? activity.data.send_after : activity.communication_date
          "
        />
        <Dropdown v-if="scheduled" :options="scheduledActions" align="end">
          <Button
            variant="ghost"
            icon="lucide-ellipsis"
            :aria-label="__('Scheduled email actions')"
            :loading="busy"
          />
        </Dropdown>
        <div v-else class="flex gap-0.5">
          <Button
            :tooltip="__('Reply')"
            variant="ghost"
            class="text-ink-gray-7"
            :icon="ReplyIcon"
            @click="reply(activity.data)"
          />
          <Button
            :tooltip="__('Reply All')"
            variant="ghost"
            :icon="ReplyAllIcon"
            class="text-ink-gray-7"
            @click="reply(activity.data, true)"
          />
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-1 text-base leading-5 text-ink-gray-8">
      <div>{{ activity.data.subject }}</div>
      <div>
        <span class="mr-1 text-ink-gray-5"> {{ __('To') }}: </span>
        <span>{{ activity.data.recipients }}</span>
        <span v-if="activity.data.cc">, </span>
        <span v-if="activity.data.cc" class="mr-1 text-ink-gray-5">
          {{ __('CC') }}:
        </span>
        <span v-if="activity.data.cc">{{ activity.data.cc }}</span>
        <span v-if="activity.data.bcc">, </span>
        <span v-if="activity.data.bcc" class="mr-1 text-ink-gray-5">
          {{ __('BCC') }}:
        </span>
        <span v-if="activity.data.bcc">{{ activity.data.bcc }}</span>
      </div>
    </div>
    <div class="border-0 border-t mt-3 mb-1 border-outline-elevation-2" />
    <EmailContent :content="activity.data.content" />
    <div v-if="activity.data?.attachments?.length" class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in activity.data.attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
</template>
<script setup>
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import EmailContent from '@/components/Activities/EmailContent.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { createDialog } from '@/utils/dialogs'
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

const status = computed(() => {
  let _status = props.activity?.data?.delivery_status
  let indicator_color = 'red'
  if (['Sent', 'Clicked'].includes(_status)) {
    indicator_color = 'green'
  } else if (['Sending', 'Scheduled'].includes(_status)) {
    indicator_color = 'amber'
  } else if (['Opened', 'Read'].includes(_status)) {
    indicator_color = 'blue'
  } else if (_status == 'Error') {
    indicator_color = 'red'
  }
  return { label: _status, color: indicator_color }
})
</script>
