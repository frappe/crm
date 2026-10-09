<template>
  <div class="grid place-items-center" :class="$attrs.class">
    <svg
      class="size-3 shrink-0"
      viewBox="0 0 10 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="0" y="8" width="2.5" height="4" rx="0.5" :class="barClass(2)" />
      <rect x="4" y="4" width="2.5" height="8" rx="0.5" :class="barClass(1)" />
      <rect x="8" y="0" width="2.5" height="12" rx="0.5" :class="barClass(0)" />
    </svg>
  </div>
</template>
<script setup>
defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  priority: { type: String, required: true },
})

// Tallest bars faded per level: High is fully solid, Low only shows one bar
const FADED_BARS = { High: 0, Medium: 1, Low: 2 }

function barClass(barIndexFromTop) {
  const faded = FADED_BARS[props.priority] ?? 0
  return barIndexFromTop < faded ? 'fill-ink-gray-3' : 'fill-ink-gray-6'
}
</script>
