<template>
  <div class="grid place-items-center">
    <div
      class="h-3 w-3 rounded-full"
      :class="[
        priority === 'High'
          ? 'bg-red-500'
          : priority === 'Medium'
            ? 'bg-yellow-500'
            : 'bg-surface-gray-4',
        $attrs.class,
      ]"
    />
  </div>
</template>
<script setup>
defineOptions({
  inheritAttrs: false,
})

defineProps({
  priority: { type: String, required: true },
})
</script>
