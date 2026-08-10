<template>
  <section class="space-y-2">
    <h3 class="text-xs-semibold uppercase tracking-wide text-ink-gray-5">
      {{ title }}
    </h3>
    <div
      class="space-y-2 rounded border border-outline-gray-2 bg-surface-elevation-1 p-3"
    >
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
})
</script>
