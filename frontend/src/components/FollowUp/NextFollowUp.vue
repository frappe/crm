<template>
  <div
    v-if="task"
    class="flex items-center gap-1.5 border-b px-5 py-2 text-base text-ink-gray-8"
  >
    <button
      type="button"
      class="flex min-w-0 flex-1 items-center gap-1.5 text-left"
      @click="emit('open', task)"
    >
      <span class="shrink-0 text-ink-gray-5">{{ __('Next:') }}</span>
      <Tooltip :text="formatTaskDue(task, 'long')">
        <span
          class="shrink-0"
          :class="isTaskOverdue(task) ? 'text-ink-red-7' : ''"
        >
          {{ formatTaskDue(task) }}
        </span>
      </Tooltip>
      <span class="shrink-0 text-ink-gray-4">&middot;</span>
      <span class="truncate">{{ task.title }}</span>
    </button>
    <FollowUpActions :task="task" @change="emit('change')" />
  </div>
</template>
<script setup>
import FollowUpActions from '@/components/FollowUp/FollowUpActions.vue'
import { formatTaskDue, isTaskOverdue, nextFollowUp } from '@/utils/task'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
})

const emit = defineEmits(['open', 'change'])

const task = computed(() => nextFollowUp(props.tasks))
</script>
