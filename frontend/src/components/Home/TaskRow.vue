<template>
  <ItemListRow
    class="relative hover:bg-surface-gray-2 has-[:focus-visible]:bg-surface-gray-3"
  >
    <template #prefix>
      <Tooltip :text="prefixTooltip">
        <span class="relative flex text-ink-gray-6">
          <TaskStatusIcon v-if="!reference" :status="task.status" />
          <component :is="doctypeIcon" v-else class="size-4" />
        </span>
      </Tooltip>
    </template>
    <RouterLink
      v-if="reference"
      :to="recordRoute(reference)"
      :class="labelClass"
    >
      <span class="truncate text-ink-gray-8">
        {{ task.reference_title || task.reference_docname }}
      </span>
      <span class="truncate text-ink-gray-5">{{ task.title }}</span>
    </RouterLink>
    <button
      v-else
      type="button"
      :class="labelClass"
      @click="emit('open', task)"
    >
      <span class="truncate text-ink-gray-8">{{ task.title }}</span>
    </button>
    <template #suffix>
      <div class="relative flex items-center gap-2">
        <Tooltip v-if="task.due_date" :text="formatTaskDue(task, 'long')">
          <span
            class="whitespace-nowrap"
            :class="isTaskOverdue(task) ? 'text-ink-red-4' : 'text-ink-gray-5'"
          >
            {{ relativeTaskDue(task) }}
          </span>
        </Tooltip>
        <slot />
      </div>
    </template>
  </ItemListRow>
</template>
<script setup>
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import { recordRoute } from '@/utils/home'
import { formatTaskDue, isTaskOverdue, relativeTaskDue } from '@/utils/task'
import { ItemListRow, Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['open'])

const labelClass =
  'flex w-full min-w-0 items-baseline gap-1.5 text-left outline-none after:absolute after:inset-0'

const reference = computed(() =>
  props.task.reference_docname
    ? {
        doctype: props.task.reference_doctype,
        name: props.task.reference_docname,
      }
    : null,
)

const doctypeIcon = computed(() =>
  reference.value?.doctype === 'CRM Deal' ? DealsIcon : LeadsIcon,
)

const prefixTooltip = computed(() => {
  if (!reference.value) return __(props.task.status)
  return reference.value.doctype === 'CRM Deal' ? __('Deal') : __('Lead')
})
</script>
