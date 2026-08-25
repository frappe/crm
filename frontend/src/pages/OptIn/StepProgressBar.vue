<template>
  <div class="flex items-center justify-center gap-0 overflow-x-auto pb-1">
    <template v-for="(label, idx) in steps" :key="label">
      <div class="flex flex-col items-center">
        <div
          :class="[
            'flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all duration-300',
            isComplete(idx)
              ? 'border-green-500 bg-green-500 text-white dark:border-green-400 dark:bg-green-400'
              : isActive(idx)
                ? 'text-white'
                : 'border-gray-200 bg-white text-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500',
          ]"
          :style="isActive(idx)
            ? 'border-color: var(--brand-primary); background-color: var(--brand-primary); box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand-primary) 16%, transparent)'
            : ''"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            :stroke-width="isComplete(idx) ? 3 : 2"
            stroke-linecap="round"
            stroke-linejoin="round"
            v-html="isComplete(idx) ? CHECK : icons[idx]"
          />
        </div>
        <span
          :class="[
            'mt-1.5 hidden text-center text-xs sm:block',
            isActive(idx) ? 'font-semibold text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500',
          ]"
        >
          {{ label }}
        </span>
      </div>
      <div
        v-if="idx < steps.length - 1"
        :class="[
          'h-0.5 w-6 flex-shrink-0 transition-colors duration-300 sm:w-10',
          isComplete(idx) ? 'bg-green-500 dark:bg-green-400' : 'bg-gray-200 dark:bg-gray-700',
        ]"
      />
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  activeStep: { type: Number, default: 1 },
})

const steps = ['Details', 'Verify', 'Facilities', 'Pricing', 'Review', 'Confirm']

// Premium per-step glyphs (Lucide-style). Rendered into the <svg> via v-html so each
// step reads at a glance instead of a bare number; completed steps show a checkmark.
const CHECK = '<polyline points="20 6 9 17 4 12" />'
const icons = [
  '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
  '<path d="M3 21h18"/><path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17"/><path d="M9.5 8h5M9.5 12h5"/>',
  '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.2"/><path d="M6 12h.01M18 12h.01"/>',
  '<path d="M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2"/><path d="M9 2h6a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/><path d="m9 14 2 2 4-4"/>',
  '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
]

function isComplete(idx) {
  return props.activeStep > idx + 1
}

function isActive(idx) {
  return props.activeStep === idx + 1
}
</script>
