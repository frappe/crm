<template>
  <button
    :class="[
      active ? 'bg-gray-100' : 'text-gray-800',
      'group flex h-7 w-full items-center justify-between gap-3 rounded px-2 text-base',
    ]"
    @click="onClick"
  >
    <span class="whitespace-nowrap">
      {{ value }}
    </span>
    <FeatherIcon
      v-if="selected"
      name="check"
      class="text-primary-500 h-4 w-4"
      size="sm"
    />
  </button>
</template>
<script setup>
const props = defineProps({
  value: {
    type: String,
    default: '',
  },
  onClick: {
    type: Function,
    default: () => {},
  },
  active: {
    type: Boolean,
    default: false,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})
</script>
