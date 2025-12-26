<template>
  <div class="flex flex-col h-full w-full text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between p-8 text-ink-gray-8">
      <div class="flex flex-col gap-1">
        <slot name="title">
          <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
            {{ title }}
          </h2>
        </slot>
        <slot
          name="description"
          v-if="Boolean($slots['description']) || Boolean(description)"
        >
          <p class="text-p-base text-ink-gray-6">
            {{ description }}
          </p>
        </slot>
      </div>
      <slot name="header-actions" v-if="Boolean($slots['header-actions'])" />
    </div>
    <div class="p-8 pt-0" v-if="Boolean($slots['header-bottom'])">
      <slot name="header-bottom" />
    </div>
    <div class="h-full overflow-y-auto p-8 pt-0">
      <slot name="content" />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
  },
  description: {
    type: String,
  },
})
</script>
