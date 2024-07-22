<template>
  <div
    class="cursor-pointer flex flex-col rounded-md shadow bg-white px-3 py-1.5 text-base transition-all duration-300 ease-in-out"
  >
    <div class="-mb-0.5 flex items-center justify-between gap-2 truncate">
      <div class="flex items-center gap-2 truncate">
        <span>{{ activity.data.sender_full_name }}</span>
        <span class="sm:flex hidden text-sm text-gray-600">
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
        <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
          <div class="text-sm text-gray-600">
            {{ __(timeAgo(activity.creation)) }}
          </div>
        </Tooltip>
        <div class="flex gap-0.5">
          <Tooltip :text="__('Reply')">
            <div>
              <Button
                variant="ghost"
                class="text-gray-700"
                @click="reply(activity.data)"
              >
                <template #icon>
                  <ReplyIcon />
                </template>
              </Button>
            </div>
          </Tooltip>
          <Tooltip :text="__('Reply All')">
            <div>
              <Button
                variant="ghost"
                class="text-gray-700"
                @click="reply(activity.data, true)"
              >
                <template #icon>
                  <ReplyAllIcon />
                </template>
              </Button>
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-1 text-base text-gray-800">
      <div>
        <span class="mr-1 text-gray-600"> {{ __('To') }}: </span>
        <span>{{ activity.data.recipients }}</span>
        <span v-if="activity.data.cc">, </span>
        <span v-if="activity.data.cc" class="mr-1 text-gray-600">
          {{ __('CC') }}:
        </span>
        <span v-if="activity.data.cc">{{ activity.data.cc }}</span>
        <span v-if="activity.data.bcc">, </span>
        <span v-if="activity.data.bcc" class="mr-1 text-gray-600">
          {{ __('BCC') }}:
        </span>
        <span v-if="activity.data.bcc">{{ activity.data.bcc }}</span>
      </div>
      <div>
        <span class="mr-1 text-gray-600"> {{ __('Subject') }}: </span>
        <span>{{ activity.data.subject }}</span>
      </div>
    </div>
    <div class="border-0 border-t my-3.5 border-gray-200" />
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
import { Badge, Tooltip } from 'frappe-ui'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'

const props = defineProps({
  activity: Object,
  emailBox: Object,
})

function reply(email, reply_all = false) {
  props.emailBox.show = true
  let editor = props.emailBox.editor
  let message = email.content
  let recipients = email.recipients.split(',').map((r) => r.trim())
  editor.toEmails = [email.sender]
  editor.cc = editor.bcc = false
  editor.ccEmails = []
  editor.bccEmails = []

  if (!email.subject.startsWith('Re:')) {
    editor.subject = `Re: ${email.subject}`
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
    .insertContent('<p>.</p>')
    .updateAttributes('paragraph', { class: 'reply-to-content' })
    .insertContent(repliedMessage)
    .focus('all')
    .insertContentAt(0, { type: 'paragraph' })
    .focus('start')
    .run()
}
</script>
