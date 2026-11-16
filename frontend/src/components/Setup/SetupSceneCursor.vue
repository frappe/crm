<template>
  <MousePointer
    class="cursor pointer-events-none absolute size-5 text-ink-gray-7"
  />
</template>

<script setup>
import MousePointer from '~icons/lucide/mouse-pointer-2'
</script>

<style scoped>
.cursor {
  fill: var(--surface-base);
  filter: drop-shadow(0 2px 3px rgb(0 0 0 / 0.18));
}
</style>
