<template>
  <div class="absolute inset-0">
    <SetupPreviewWindow :sidebar="false" :top="40">
      <div class="flex items-center justify-between border-b border-outline-gray-1 px-5 py-3">
        <div class="flex items-center gap-2 text-sm text-ink-gray-5">
          <LeadsIcon class="size-3.5" />
          {{ __('Leads') }}
          <span class="text-ink-gray-3">/</span>
          <span class="text-ink-gray-8">Marcus Lee</span>
        </div>
        <div class="flex items-center gap-1.5 text-xs text-ink-gray-6">
          <img v-if="provider" :src="provider.icon" class="size-3.5" alt="" />
          <LucideMail v-else class="size-3.5" />
          {{ provider?.name || __('Email') }}
        </div>
      </div>

      <div class="px-5 pb-4 pt-6">
        <div class="flex items-center gap-3">
          <Avatar label="Marcus Lee" size="lg" />
          <div>
            <div class="text-xl font-semibold tracking-tight text-ink-gray-9">Marcus Lee</div>
            <div class="mt-1 text-sm text-ink-gray-5">{{ __('Globex · Sales Director') }}</div>
          </div>
          <span class="ml-auto rounded-full border border-outline-gray-2 px-2 py-1 text-xs text-ink-gray-6">
            {{ __('Contacted') }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-5 border-b border-outline-gray-1 px-5 text-sm">
        <span class="flex items-center gap-1.5 border-b border-ink-gray-9 pb-3 font-medium text-ink-gray-9">
          <LucideMail class="size-3.5" />
          {{ __('Emails') }}
          <span class="rounded bg-surface-gray-2 px-1.5 text-xs text-ink-gray-5">3</span>
        </span>
        <span class="pb-3 text-ink-gray-5">{{ __('Activity') }}</span>
        <span class="pb-3 text-ink-gray-5">{{ __('Notes') }}</span>
      </div>

      <div class="flex min-h-0 flex-1 flex-col px-5 py-4">
        <div class="flex items-center justify-between text-xs text-ink-gray-5">
          <span>{{ __('Conversation') }}</span>
          <span>{{ __('3 messages') }}</span>
        </div>
        <div class="mt-3 rounded-6 border border-outline-gray-2 bg-surface-gray-1">
          <div class="flex items-center gap-2.5 border-b border-outline-gray-1 px-4 py-3">
            <Avatar label="Marcus Lee" size="sm" />
            <div class="flex-1 text-sm font-medium text-ink-gray-8">Marcus Lee</div>
            <span class="text-xs text-ink-gray-5">{{ __('Today, 9:42 AM') }}</span>
          </div>
          <div class="px-4 py-4">
            <h3 class="text-base font-medium text-ink-gray-9">{{ __('Re: Pricing for 40 seats') }}</h3>
            <p class="mt-3 text-sm leading-6 text-ink-gray-6">
              {{ __('Thanks, the annual plan works for us. Can we start the pilot next week?') }}
            </p>
            <p class="mt-3 text-sm leading-6 text-ink-gray-6">{{ __('Looking forward to getting the team onboard.') }}</p>
            <div class="mt-4 flex items-center gap-1.5 text-xs text-ink-gray-5">
              <LucideCornerDownRight class="size-3" />
              {{ __('2 earlier messages') }}
            </div>
          </div>
        </div>
        <div class="mt-4 rounded-6 border border-outline-gray-2 p-3">
          <div class="flex items-center gap-2 text-xs text-ink-gray-5">
            <LucideReply class="size-3.5" />
            {{ __('Reply to Marcus') }}
          </div>
          <div class="pb-7 pt-3 text-sm text-ink-gray-4">{{ __('Write a reply…') }}</div>
          <div class="flex items-center justify-between border-t border-outline-gray-1 pt-3">
            <LucidePaperclip class="size-3.5 text-ink-gray-5" />
            <span class="flex items-center gap-1.5 rounded-4 bg-surface-gray-7 px-2.5 py-1.5 text-xs font-medium text-ink-white">
              {{ __('Send') }} <LucideArrowUp class="size-3" />
            </span>
          </div>
        </div>
        <div class="mt-auto flex items-center justify-center gap-1.5 pt-4 text-xs text-ink-gray-5">
          <LucideCheck class="size-3" />
          {{ __('Every conversation, linked to your lead') }}
        </div>
      </div>
    </SetupPreviewWindow>
  </div>
</template>

<script setup>
import SetupPreviewWindow from '@/components/Setup/SetupPreviewWindow.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import { Avatar } from 'frappe-ui'
import LucideMail from '~icons/lucide/mail'
import LucideReply from '~icons/lucide/reply'
import LucidePaperclip from '~icons/lucide/paperclip'
import LucideArrowUp from '~icons/lucide/arrow-up'
import LucideCheck from '~icons/lucide/check'
import LucideCornerDownRight from '~icons/lucide/corner-down-right'

defineProps({ provider: { type: Object, default: null } })
</script>
