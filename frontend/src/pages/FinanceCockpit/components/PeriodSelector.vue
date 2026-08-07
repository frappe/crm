<template>
  <div class="flex gap-1 flex-wrap">
    <button
      v-for="opt in OPTIONS"
      :key="opt.value"
      :class="[
        'px-3 py-1 text-xs rounded-full border transition-colors',
        modelValue === opt.value
          ? 'bg-blue-600 border-blue-600 text-white'
          : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-400',
      ]"
      @click="$emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup>
const OPTIONS = [
  { value: 'month', label: 'This Month' },
  { value: 'quarter', label: 'This Quarter' },
  { value: 'year', label: 'This Year' },
  { value: 'ytd', label: 'YTD' },
]

defineProps({
  modelValue: { type: String, default: 'month' },
})
defineEmits(['update:modelValue'])
</script>
