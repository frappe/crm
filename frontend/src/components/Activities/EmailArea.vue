<template>
  <EmailItem :email="email">
    <template #actions>
      <Badge
        v-if="activity.communication_type == 'Automated Message'"
        :label="__('Notification')"
        variant="subtle"
        theme="green"
      />
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
    </template>
  </EmailItem>
</template>
<script setup>
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import { EmailItem } from '@framework/ui/components/ActivityTimeline'
import { Badge } from 'frappe-ui'
import { reactive, computed } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  emailBox: { type: Object, default: () => ({}) },
})

const emailBox = reactive(props.emailBox)

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

    editor.cc = cc ? true : false
    editor.bcc = bcc ? true : false

    editor.ccEmails = cc
    editor.bccEmails = bcc
  }

  let repliedMessage = `<blockquote>${message}</blockquote>`

  editor.editor
    .chain()
    .clearContent()
    .updateAttributes('paragraph', { class: 'reply-to-content' })
    .insertContent(repliedMessage)
    .focus('all')
    .insertContentAt(0, { type: 'paragraph' })
    .focus('start')
    .run()
}

const email = computed(() => {
  const { data } = props.activity
  return {
    type: 'email',
    key: props.activity.communication_date,
    timestamp: props.activity.communication_date,
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
