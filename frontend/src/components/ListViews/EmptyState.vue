<template>
  <div class="flex h-full mb-28 items-center justify-center">
    <div class="flex flex-col items-center gap-3 w-96">
      <component :is="icon" class="size-7.5 text-ink-gray-5" />
      <div class="flex flex-col items-center gap-1">
        <span class="text-lg font-medium text-ink-gray-8">
          {{ computedTitle }}
        </span>
        <span class="text-center text-p-base text-ink-gray-6">
          {{ computedDescription }}
        </span>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  icon: {
    type: Object,
    default: () => import('@/components/Icons/LeadsIcon.vue'),
  },
})

const computedTitle = computed(() => {
  return props.title ? props.title : __('No {0} found', [__(props.name)])
})

const computedDescription = computed(() => {
  return props.description
    ? props.description
    : __(
        'It appears that there are currently no {0} available. you can create more {0} by using the Create button.',
        [__(props.name)],
      )
})
</script>
