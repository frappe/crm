<template>
  <div class="grid place-items-center">
    <div
      class="h-3 w-3 rounded-full"
      :class="{
        'bg-red-500': priority === 'High',
        'bg-yellow-500': priority === 'Medium',
        'bg-surface-gray-4': priority === 'Low',
      }, $attrs.class"
    ></div>
  </div>
</template>
<script setup>
defineOptions({
  inheritAttrs: false
})
const props = defineProps({
  priority: {
    type: String,
    required: true,
  },
})
</script>
