<template>
  <div class="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-lg dark:bg-gray-800">
    <!-- Success icon -->
    <div
      class="mb-6 flex h-16 w-16 items-center justify-center rounded-full mx-auto"
      style="background-color: color-mix(in srgb, var(--brand-primary, #bc1823) 15%, transparent)"
    >
      <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ color: 'var(--brand-primary, #bc1823)' }">
        <path d="M20 6L9 17l-5-5"/>
      </svg>
    </div>

    <h2 class="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
      Thank you<span v-if="signatoryName">, {{ firstName }}</span>.
    </h2>

    <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
      Your signature has been recorded.
    </p>

    <!-- Contract reference -->
    <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 text-left dark:border-gray-700 dark:bg-gray-800/50">
      <dl class="space-y-2">
        <div>
          <dt class="text-xs text-gray-400 dark:text-gray-500">Contract Reference</dt>
          <dd class="text-sm font-semibold text-gray-900 dark:text-white">{{ contract }}</dd>
        </div>
        <div v-if="contractDate">
          <dt class="text-xs text-gray-400 dark:text-gray-500">Contract Date</dt>
          <dd class="text-sm font-semibold text-gray-900 dark:text-white">{{ formattedDate }}</dd>
        </div>
      </dl>
    </div>

    <p class="mt-6 text-xs text-gray-400 dark:text-gray-500">
      You may close this window. A copy of the executed contract will be sent to you once all parties have signed.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  signatoryName: { type: String, default: '' },
  contract: { type: String, required: true },
  contractDate: { type: String, default: '' },
})

const firstName = computed(() => {
  if (!props.signatoryName) return ''
  return props.signatoryName.split(' ')[0]
})

const formattedDate = computed(() => {
  if (!props.contractDate) return ''
  try {
    return new Date(props.contractDate).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  } catch {
    return props.contractDate
  }
})
</script>
