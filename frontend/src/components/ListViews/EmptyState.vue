<template>
  <div class="relative flex h-full w-full justify-center">
    <div
      class="absolute left-1/2 flex w-4/12 -translate-x-1/2 flex-col items-center gap-3"
      :style="{ top: top }"
    >
      <Icon :icon="icon" class="size-7.5 text-ink-gray-5" />
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
import Icon from '@/components/Icon.vue'
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  icon: {
    type: [String, Object],
    default: 'file-text',
  },
  top: { type: String, default: '35%' },
})

const computedTitle = computed(() => {
  return props.title ? props.title : __('No {0} found', [__(props.name)])
})

const computedDescription = computed(() => {
  return props.description
    ? props.description
    : __(
        'It appears that there are currently no {0} available. You can create more {0} by using the Create button.',
        [__(props.name)],
      )
})
</script>
