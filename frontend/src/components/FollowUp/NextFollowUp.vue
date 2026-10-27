<template>
  <div v-if="task" class="flex flex-col gap-1 border-b px-5 py-3">
    <div class="flex items-center justify-between gap-2">
      <span class="text-sm-medium text-ink-gray-5">{{ __('Next step') }}</span>
      <FollowUpActions :task="task" @change="emit('change')" />
    </div>
    <button
      type="button"
      class="flex flex-col gap-1 text-left"
      @click="emit('open', task)"
    >
      <span class="line-clamp-2 text-base text-ink-gray-8">
        {{ task.title }}
      </span>
      <Tooltip :text="formatTaskDue(task, 'long')">
        <span
          class="text-sm"
          :class="isTaskOverdue(task) ? 'text-ink-red-7' : 'text-ink-gray-5'"
        >
          {{ formatTaskDue(task) }}
        </span>
      </Tooltip>
    </button>
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
