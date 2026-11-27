<template>
  <div class="mb-5 flex items-center gap-3">
    <span
      class="grid size-8 shrink-0 place-items-center rounded-5 bg-surface-gray-2"
    >
      <Icon :icon="icon" class="size-4 text-ink-gray-7" />
    </span>
    <div class="min-w-0">
      <p class="truncate text-base-semibold text-ink-gray-8">{{ title }}</p>
      <p class="text-sm text-ink-gray-5">{{ origin }}</p>
    </div>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'

defineProps({
  icon: { type: [String, Object, Function], required: true },
  title: { type: String, required: true },
  origin: { type: String, required: true },
})
</script>
