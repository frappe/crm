<template>
  <slot name="prefix"></slot>
  <slot v-if="$slots.default" />
  <div v-else class="text-base text-gray-900 truncate">
    {{ value }}
  </div>
</template>
<script setup>
const props = defineProps({
  value: {
    type: String,
    default: null,
  },
})
</script>
