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
    <div
      class="flex min-w-0 flex-col gap-0.5"
      :class="compact ? 'items-start' : 'items-center'"
    >
      <span
        class="text-p-base text-ink-gray-6"
        :class="{ 'max-w-64 text-balance': !compact }"
      >
        {{ text }}
      </span>
      <slot />
    </div>
  </div>
</template>
<script setup>
defineProps({
  text: { type: String, required: true },
  icon: { type: String, required: true },
  compact: { type: Boolean, default: false },
})
</script>
