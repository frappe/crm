<template>
  <div
    class="email-container border-l-4 border-blue-400 pl-3 cursor-pointer"
    @click="openInDesk(activity)"
  >
    <div class="flex items-center gap-2">
      <span class="text-gray-500">{{ __('From') }}:</span>
      <span class="text-gray-700">{{ activity.details.sender_name || activity.details.sender }}</span>
    </div>
    <div class="flex items-center gap-2" v-if="activity.details.recipients">
      <span class="text-gray-500">{{ __('To') }}:</span>
      <span class="text-gray-700">{{ activity.details.recipients }}</span>
    </div>
    <div 
      class="mt-2 prose max-w-none email-content"
      v-html="displayedContent"
    ></div>
    <div v-if="activity.description.length > 500" class="mt-2">
      <button
        class="text-gray-600 hover:text-gray-900 text-sm"
        @click.stop="toggleExpanded"
      >
        {{ isExpanded ? __('Show Less') : __('Show More') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  activity: {
    type: Object,
    required: true
  }
})

const isExpanded = ref(false)
const originalContent = ref(props.activity.description)

const displayedContent = computed(() => {
  if (isExpanded.value || props.activity.description.length <= 500) {
    return originalContent.value
  }
  return props.activity.description.slice(0, 500) + '...'
})

function toggleExpanded(event) {
  event.preventDefault()
  isExpanded.value = !isExpanded.value
}

function openInDesk(activity) {
  if (activity.type === 'email' && activity.reference?.name) {
    const url = `/app/communication/${activity.reference.name}`
    window.open(url, '_blank')
  }
}
</script>

<style scoped>
.email-content {
  @apply text-sm text-gray-700 whitespace-pre-wrap break-words;
  word-break: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.email-content :deep(*) {
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  hyphens: auto;
}

.email-content :deep(a) {
  @apply text-blue-600 hover:text-blue-800 underline;
  word-break: break-all;
}

.email-content :deep(p) {
  @apply mb-3;
  max-width: 100%;
}

.email-content :deep(ul), 
.email-content :deep(ol) {
  @apply ml-4 mb-3 list-disc;
}

.email-content :deep(ol) {
  @apply list-decimal;
}

.email-content :deep(li) {
  @apply mb-1;
}

.email-content :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-3 my-2 text-gray-600;
}

.email-content :deep(pre) {
  @apply bg-gray-100 p-2 rounded my-2;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-width: 100%;
}
</style>
