<template>
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="8" cy="8" :r="radius" fill="currentColor" />
  </svg>
</template>
<script setup>
const props = defineProps({
  radius: {
    type: Number,
    default: 3.5,
  },
})
</script>
