<template>
  <svg
    v-if="!fill"
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="8"
      cy="8"
      r="3.5"
      fill="currentColor"
      stroke="currentColor"
      stroke-width="1"
    />
  </svg>
  <svg
    v-else
    width="12"
    height="12"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="8"
      cy="8"
      r="4.5"
      fill="currentColor"
      stroke="currentColor"
      stroke-width="3"
    />
  </svg>
</template>

<script setup>
defineProps({
  fill: {
    type: Boolean,
    default: false,
  },
})
</script>
