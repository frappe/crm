<template>
  <div class="grid grid-cols-[10rem_1fr] gap-3 text-sm">
    <div class="text-ink-gray-5">{{ label }}</div>
    <div
      class="min-w-0 break-words text-ink-gray-8"
      :class="{ 'font-mono text-xs': mono }"
    >
      {{ value || '-' }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  mono: { type: Boolean, default: false },
})
</script>
