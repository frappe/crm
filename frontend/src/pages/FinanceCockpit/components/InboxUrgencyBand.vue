<template>
  <div v-if="items.length" class="mb-4">
    <div
      :class="[
        'flex items-center gap-2 px-3 py-1.5 rounded-t text-xs font-semibold uppercase tracking-wider',
        bandClass,
      ]"
    >
      <span v-html="bandIcon" class="w-4 h-4 flex-shrink-0" />
      <span>{{ label }}</span>
      <span class="ml-auto bg-white/20 rounded-full px-1.5 py-0.5 text-xs">{{ items.length }}</span>
    </div>
    <div class="border border-t-0 rounded-b border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700">
      <slot />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  urgency: { type: String, required: true },
  items: { type: Array, default: () => [] },
})

const BAND_CONFIG = {
  critical: {
    label: 'Critical',
    bandClass: 'bg-red-500 text-white',
    bandIcon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
  },
  warning: {
    label: 'Warning',
    bandClass: 'bg-amber-500 text-white',
    bandIcon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>',
  },
  normal: {
    label: 'Normal',
    bandClass: 'bg-gray-400 text-white',
    bandIcon: '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
  },
}

const config = BAND_CONFIG[props.urgency] || BAND_CONFIG.normal
const { label, bandClass, bandIcon } = config
</script>
