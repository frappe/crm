<template>
  <aside
    class="relative flex-col justify-center gap-8 overflow-hidden bg-surface-gray-2 p-10"
    aria-hidden="true"
  >
    <ul class="flex flex-col items-center gap-3">
      <li
        v-for="highlight in highlights"
        :key="highlight.label"
        class="flex items-center gap-2 rounded-lg bg-surface-white px-3 py-2 text-base text-ink-gray-7 shadow-sm"
      >
        <component :is="highlight.icon" class="size-4 text-ink-gray-5" />
        {{ highlight.label }}
      </li>
    </ul>
    <div class="rounded-xl bg-surface-white p-4 shadow-sm">
      <div class="mb-4 h-3 w-24 rounded-full bg-surface-gray-3" />
      <div
        v-for="row in 6"
        :key="row"
        class="flex items-center gap-3 border-t border-outline-gray-1 py-3"
      >
        <div class="size-5 rounded-full bg-surface-gray-3" />
        <div
          class="h-2.5 rounded-full bg-surface-gray-3"
          :style="{ width: `${30 + ((row * 17) % 40)}%` }"
        />
        <div class="ml-auto h-2.5 w-12 rounded-full bg-surface-gray-2" />
      </div>
    </div>
  </aside>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import LucideSend from '~icons/lucide/send'
import LucideUserPlus from '~icons/lucide/user-plus'
import LucideTable from '~icons/lucide/table'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideUsers from '~icons/lucide/users'
import LucideAtSign from '~icons/lucide/at-sign'
import LucideHeart from '~icons/lucide/heart'
import { computed } from 'vue'

const props = defineProps({
  step: { type: String, required: true },
})

const highlightsByStep = {
  connect_email: [
    { icon: LucideMail, label: __('Emails logged on leads and deals') },
    { icon: LucideSend, label: __('Send and reply from the CRM') },
    { icon: LucideUserPlus, label: __('Leads created from incoming email') },
  ],
  bring_leads: [
    { icon: LucideTable, label: __('Import leads from a CSV file') },
    { icon: LucideSparkles, label: __('Or explore with sample data') },
  ],
  invite_team: [
    { icon: LucideUsers, label: __('Assign leads to teammates') },
    { icon: LucideAtSign, label: __('Mention and comment together') },
  ],
  feedback: [{ icon: LucideHeart, label: __('Thanks for setting up') }],
}

const highlights = computed(() => highlightsByStep[props.step] || [])
</script>
