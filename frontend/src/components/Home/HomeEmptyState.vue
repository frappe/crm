<!-- Looks like ListViews/EmptyState, but sits in the page flow so it fits inside a card. -->
<template>
  <div class="flex flex-col items-center justify-center gap-3 text-center">
    <span
      :class="icon"
      class="size-7.5 shrink-0 text-ink-gray-5"
      aria-hidden="true"
    />
    <div class="flex max-w-72 flex-col items-center gap-1 text-balance">
      <span v-if="title" class="text-lg-medium text-ink-gray-8">
        {{ title }}
      </span>
      <span v-if="text || $slots.default" class="text-p-base text-ink-gray-6">
        <slot>{{ text }}</slot>
      </span>
    </div>
  </div>
</template>
<script setup>
defineProps({
  icon: { type: String, required: true },
  title: { type: String, default: '' },
  text: { type: String, default: '' },
})
</script>
