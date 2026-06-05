<template>
  <div class="flex items-start justify-between gap-3">
    <span class="text-ink-gray-5 shrink-0">{{ label }}</span>
    <span class="text-right text-ink-gray-8 truncate" :title="value || '-'">
      {{ value || '-' }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
})
</script>