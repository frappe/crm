<template>
  <button
    type="button"
    class="mx-2 mt-2 flex w-[calc(100%-1rem)] items-center gap-2.5 rounded-4 bg-surface-gray-2 px-2.5 py-2 text-start hover:bg-surface-gray-3"
    @mousedown.prevent
    @click="showAskFlow"
  >
    <component
      :is="state.icon"
      class="size-3.5 shrink-0"
      :class="[state.color, { 'animate-spin': state.spin }]"
    />
    <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
      {{ askFlow.question }}
    </span>
    <span class="shrink-0 text-xs" :class="state.color">
      {{ __(state.label) }}
    </span>
    <kbd
      v-if="showKey"
      class="shrink-0 rounded-1 bg-surface-gray-3 px-1 py-0.5 font-sans text-xs text-ink-gray-5"
    >
      Tab
    </kbd>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import LucideCircleAlert from '~icons/lucide/circle-alert'
import LucideLoaderCircle from '~icons/lucide/loader-circle'
import LucideSparkles from '~icons/lucide/sparkles'
import { askFlow, showAskFlow } from '@/components/FlowChat/askFlow'

// mousedown is prevented so the search input keeps focus: losing it would
// select the active option
defineProps({ showKey: { type: Boolean, default: false } })

const STATES = {
  working: {
    icon: LucideLoaderCircle,
    spin: true,
    color: 'text-ink-gray-5',
    label: 'Answering…',
  },
  needs_you: {
    icon: LucideCircleAlert,
    color: 'text-ink-amber-6',
    label: 'Needs approval',
  },
  error: { icon: LucideCircleAlert, color: 'text-ink-red-6', label: 'Failed' },
  answered: {
    icon: LucideSparkles,
    color: 'text-ink-gray-5',
    label: 'Answered',
  },
}

const state = computed(() => STATES[askFlow.status] || STATES.answered)
</script>
