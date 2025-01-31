<template>
  <div class="timeline-group">
    <div class="text-sm text-gray-600 mb-2">{{ formatDate(date) }}</div>
    <div class="space-y-3">
      <TimelineItem
        v-for="activity in group"
        :key="activity.reference.name"
        :activity="activity"
      />
    </div>
  </div>
</template>

<script setup>
import { formatDate } from '@/utils'
import TimelineItem from './TimelineItem.vue'

defineProps({
  date: {
    type: String,
    required: true
  },
  group: {
    type: Array,
    required: true
  }
})
</script>
