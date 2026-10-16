<template>
  <div class="email-preview pointer-events-none absolute inset-0 select-none" inert>
    <SetupPreviewWindow :sidebar="false" :top="40">
      <div class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-outline-gray-1 px-4">
        <Breadcrumbs :items="[{ label: __('Leads') }, { label: 'Marcus Lee' }]" />
        <Button :label="__('Contacted')" icon-right="lucide-chevron-down">
          <template #prefix><span class="size-2 rounded-full bg-surface-amber-6" /></template>
        </Button>
      </div>
      <Tabs
        v-model="activeTab"
        :tabs="tabs"
        class="flex min-h-0 flex-1 flex-col overflow-hidden [&_[role='tab']]:shrink-0 [&_[role='tab']]:px-1 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-[22px] [&_[role='tablist']]:px-5 [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-1"
      >
        <template #tab-panel>
          <div class="flex h-full flex-col">
            <div class="mx-6 mb-5 mt-6 flex items-center justify-between">
              <span class="text-2xl-semibold text-ink-gray-8">{{ __('Emails') }}</span>
              <Button variant="solid" :label="__('New Email')" icon-left="lucide-plus" />
            </div>
            <div class="mx-6 flex flex-col gap-5">
              <div v-for="email in emails" :key="email.subject" class="flex items-start gap-3">
                <Avatar :label="email.author.fullname" size="md" class="mt-1 shrink-0" />
                <div class="min-w-0 flex-1">
                  <div class="mb-2 text-sm font-medium text-ink-gray-8">{{ email.subject }}</div>
                  <EmailItem :email="email">
                    <template #header>
                      <div class="flex items-center justify-between gap-2 px-3 py-2.5 text-sm">
                        <span class="font-medium text-ink-gray-6">{{ email.author.fullname }}</span>
                        <span class="text-xs text-ink-gray-5">{{ email.time }}</span>
                      </div>
                      <div class="px-3 pb-2 text-xs text-ink-gray-5">{{ __('To:') }} {{ email.data.to }}</div>
                    </template>
                    <template #footer>
                      <div class="mt-2 flex items-center gap-1 border-t border-outline-gray-1 pt-2">
                        <Button variant="ghost" :label="__('Reply')" :icon-left="ReplyIcon" />
                        <Button variant="ghost" :label="__('Reply All')" :icon-left="ReplyAllIcon" />
                      </div>
                    </template>
                  </EmailItem>
                </div>
              </div>
            </div>
            <div class="mt-auto flex items-center gap-1.5 border-t border-outline-gray-1 px-5 py-3 text-xs text-ink-gray-5">
              <img v-if="provider" :src="provider.icon" class="size-3.5" alt="" />
              <EmailIcon v-else class="size-3.5" />
              {{ provider?.name || __('Email') }}
            </div>
          </div>
        </template>
      </Tabs>
    </SetupPreviewWindow>
  </div>
</template>

<script setup>
import SetupPreviewWindow from '@/components/Setup/SetupPreviewWindow.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import { EmailItem } from '@framework/ui/components/ActivityTimeline'
import { Avatar, Breadcrumbs, Button, Tabs } from 'frappe-ui'
import { ref } from 'vue'

defineProps({ provider: { type: Object, default: null } })
const activeTab = ref('emails')
const tabs = [
  { value: 'activity', label: __('Activity'), iconLeft: ActivityIcon },
  { value: 'emails', label: __('Emails'), iconLeft: EmailIcon },
  { value: 'comments', label: __('Comments'), iconLeft: CommentIcon },
  { value: 'tasks', label: __('Tasks'), iconLeft: TaskIcon },
  { value: 'notes', label: __('Notes'), iconLeft: NoteIcon },
]
// Email content lives in an iframe; use the same theme surface as its card.
const emailSurface = '<div><style>html, body, .email-content { background: var(--surface-base) !important; }</style></div>'
const emails = [
  {
    subject: __('Re: Pricing for 40 seats'),
    author: { fullname: 'Marcus Lee' },
    time: __('Today, 9:42 AM'),
    data: {
      sender: 'marcus@example.com',
      to: 'you@example.com',
      content: emailSurface + '<p>Thanks, the annual plan works for us. Can we start the pilot next week?</p>',
    },
  },
  {
    subject: __('Demo follow-up'),
    author: { fullname: 'Priya Raman' },
    time: __('Yesterday'),
    data: {
      sender: 'priya@example.com',
      to: 'marcus@example.com',
      content: emailSurface + '<p>Sharing the recording and the rollout plan we discussed.</p>',
    },
  },
]
</script>

<style scoped>
.email-preview {
  mask-image: linear-gradient(to bottom, black 68%, transparent 98%);
}

.email-preview :deep(.preview-window) {
  left: 48px !important;
  top: 88px !important;
  transform: scale(1.08);
  transform-origin: top left;
}
</style>
