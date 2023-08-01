<template>
  <div class="p-6">
    <div v-for="activity in activities">
      <div>{{ activity.value }}</div>
    </div>
  </div>
</template>
<script setup>
const props = defineProps({
  activities: {
    type: Array,
    default: [],
  },
})
</script>
