<template>
  <div
    class="flex w-full min-w-0 items-center rounded p-2 text-base font-medium text-gray-800"
    :class="{ 'bg-gray-200': active }"
  >
    <Icon
      v-if="command.icon"
      :icon="command.icon"
      class="mr-3 h-4 w-4 text-gray-700"
    />
    <span class="overflow-hidden text-ellipsis whitespace-nowrap">
      {{ command.translate === false ? command.title : __(command.title) }}&nbsp;
    </span>
    <span
      v-if="command.subtitle"
      class="ml-auto whitespace-nowrap pl-2 text-gray-600"
    >
      {{ command.subtitle }}
    </span>
    <span
      v-if="command.children"
      class="lucide-chevron-right ml-auto h-4 w-4 text-gray-600"
    />
    <span
      v-if="command.checked"
      class="lucide-check ml-auto h-4 w-4 text-gray-600"
    />
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'

defineProps({
  command: { type: Object, required: true },
  active: { type: Boolean, required: true },
})
</script>
