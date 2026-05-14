<template>
  <div
    class="grid h-full place-items-center px-4 py-20 text-center text-lg text-ink-gray-5"
  >
    <div class="flex flex-col justify-between items-center gap-3">
      <span class="lucide-octagon-x size-12 text-ink-red-3" aria-hidden="true" />
      <div class="text-2xl font-semibold">{{ errorTitle }}</div>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div v-html="sanitizeHTML(errorMessage)" />
    </div>
  </div>
</template>

<script setup>
import { sanitizeHTML } from '@/utils'
defineProps({
  errorTitle: { type: String, required: true },
  errorMessage: { type: String, required: true },
})
</script>
