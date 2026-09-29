<template>
  <button
    v-if="variant === 'label'"
    type="button"
    class="w-full truncate bg-transparent p-0 text-left text-base cursor-pointer hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-4 focus-visible:ring-offset-1 rounded"
    @click.stop.prevent="openWebsite(url)"
  >
    {{ label }}
  </button>
  <span
    v-else
    class="lucide-external-link h-3.5 w-3.5 shrink-0 cursor-pointer text-ink-gray-5"
    aria-hidden="true"
    @click.stop.prevent="openWebsite(url)"
  />
</template>

<script setup>
import { openWebsite } from '@/utils'

defineProps({
  url: { type: String, required: true },
  label: { type: String, default: '' },
  variant: {
    type: String,
    default: 'label',
    validator: (value) => ['label', 'icon'].includes(value),
  },
})
</script>
