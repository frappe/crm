<template>
  <component
    :is="item.icon"
    v-if="item.icon"
    class="size-4 shrink-0"
    :class="item.tone || 'text-ink-gray-6'"
    aria-hidden="true"
  />
</template>

<script setup>
defineProps({
  item: { type: Object, required: true },
})
</script>
