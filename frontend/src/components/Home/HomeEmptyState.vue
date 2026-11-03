<template>
  <div
    class="flex items-center justify-center gap-3"
    :class="{ 'flex-col text-center': !compact }"
  >
    <span
      class="flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-gray-2"
    >
      <span :class="icon" class="size-4 text-ink-gray-5" />
    </span>
    <span
      class="min-w-0 text-p-base text-ink-gray-6"
      :class="{ 'max-w-64 text-balance': !compact }"
    >
      <slot>{{ text }}</slot>
    </span>
  </div>
</template>
<script setup>
defineProps({
  text: { type: String, default: '' },
  icon: { type: String, required: true },
  compact: { type: Boolean, default: false },
})
</script>
