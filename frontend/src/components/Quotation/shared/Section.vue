<template>
  <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-6">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-base font-semibold text-ink-gray-9">{{ title }}</h3>
      <slot name="actions" />
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({ title: { type: String, required: true } })
</script>