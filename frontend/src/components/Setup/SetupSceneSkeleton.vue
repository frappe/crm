<template>
  <span
    class="sk block shrink-0 rounded-full"
    :class="{ outline }"
    :style="
      circle
        ? { width: `${size}px`, height: `${size}px` }
        : { width: w, height: `${h}px` }
    "
  />
</template>

<script setup>
defineProps({
  w: { type: String, default: '60%' },
  h: { type: Number, default: 8 },
  circle: Boolean,
  size: { type: Number, default: 20 },
  outline: Boolean,
})
</script>

<style scoped>
.sk {
  background: var(--st-skel, var(--surface-gray-3));
}
.sk.outline {
  background: none;
  border: 1px solid var(--st-hair-strong, var(--outline-gray-3));
}
</style>
