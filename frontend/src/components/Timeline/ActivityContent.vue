<template>
  <div class="text-sm text-gray-600 mt-2">
    <template v-if="activity.type === 'email'">
      <EmailContent :activity="activity" />
    </template>
    <template v-else>
      <div v-html="activity.description"></div>
    </template>
  </div>
</template>

<script setup>
import EmailContent from './EmailContent.vue'

defineProps({
  activity: {
    type: Object,
    required: true
  }
})
</script>
