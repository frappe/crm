<!--
  The seam on the sidebar's right edge: click it, or the round button that shows on hover, to
  collapse or expand. Placed right after the `peer/sidebar` Sidebar, inside a wrapper as wide as it.
-->
<template>
  <div
    class="peer/edge absolute inset-y-0 left-full z-10 w-2 -translate-x-1/2"
    :class="collapsed ? 'cursor-e-resize' : 'cursor-w-resize'"
    aria-hidden="true"
    @click="emit('toggle')"
  />

  <button
    type="button"
    class="absolute bottom-1/3 left-full z-20 flex size-6 -translate-x-1/2 translate-y-1/2 items-center justify-center rounded-full border border-outline-gray-2 bg-surface-base text-ink-gray-5 opacity-0 shadow-sm transition-opacity hover:bg-surface-gray-2 focus-visible:opacity-100 focus-visible:focus-ring hover:opacity-100 peer-hover/edge:opacity-100 peer-hover/sidebar:opacity-100"
    :aria-label="collapsed ? __('Expand sidebar') : __('Collapse sidebar')"
    :aria-expanded="!collapsed"
    @click="emit('toggle')"
  >
    <span
      class="lucide-chevron-left size-4 transition-transform"
      :class="{ 'rotate-180': collapsed }"
      aria-hidden="true"
    />
  </button>
</template>

<script setup>
defineProps({
  collapsed: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle'])
</script>
