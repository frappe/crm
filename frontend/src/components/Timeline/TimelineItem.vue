<template>
  <div class="activity-item flex gap-3 p-3 bg-white rounded-lg border">
    <div class="activity-icon">
      <component :is="getActivityIcon(activity.type)" class="h-5 w-5 text-gray-600" />
    </div>
    <div class="flex-1">
      <div class="flex justify-between items-start">
        <div class="font-medium">{{ activity.title }}</div>
        <div class="text-sm text-gray-500">{{ getUser(activity.owner).full_name }}</div>
      </div>
      <ActivityContent :activity="activity" />
    </div>
  </div>
</template>

<script setup>
import { usersStore } from '@/stores/users'
import ActivityContent from './ActivityContent.vue'
import EmailIcon from '../Icons/EmailIcon.vue'
import NoteIcon from '../Icons/NoteIcon.vue'

const { getUser } = usersStore()

const props = defineProps({
  activity: {
    type: Object,
    required: true
  }
})

function getActivityIcon(type) {
  const icons = {
    'email': EmailIcon,
    'note': NoteIcon,
    'comment': NoteIcon
  }
  return icons[type] || NoteIcon
}
</script> 