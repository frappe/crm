<template>
  <ListRow :class="homeRowClass">
    <ListCell>
      <Tooltip :text="prefixTooltip">
        <span class="relative flex text-ink-gray-6">
          <TaskStatusIcon v-if="!reference" :status="task.status" />
          <component :is="doctypeIcon" v-else class="size-4" />
        </span>
      </Tooltip>
    </ListCell>
    <ListCell class="gap-1.5">
      <RouterLink
        v-if="reference"
        :to="recordRoute(reference)"
        :class="stretchedClass"
        :aria-label="task.title"
      />
      <button
        v-else
        type="button"
        :class="stretchedClass"
        :aria-label="task.title"
        @click="emit('open', task)"
      />
      <template v-if="reference">
        <span class="max-w-[70%] shrink-0 truncate text-ink-gray-8">
          {{ task.reference_title || task.reference_docname }}
        </span>
        <span class="truncate text-ink-gray-5">{{ task.title }}</span>
      </template>
      <span v-else class="truncate text-ink-gray-8">{{ task.title }}</span>
    </ListCell>
    <ListCell class="justify-end">
      <Tooltip v-if="task.due_date" :text="formatTaskDue(task, 'long')">
        <span
          class="relative whitespace-nowrap"
          :class="isTaskOverdue(task) ? 'text-ink-red-4' : 'text-ink-gray-5'"
        >
          {{ relativeTaskDue(task) }}
        </span>
      </Tooltip>
    </ListCell>
    <slot />
  </ListRow>
</template>
<script setup>
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import { homeRowClass, recordRoute } from '@/utils/home'
import { formatTaskDue, isTaskOverdue, relativeTaskDue } from '@/utils/task'
import { Tooltip } from 'frappe-ui'
import { ListCell, ListRow } from 'frappe-ui/list'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['open'])

const stretchedClass = 'absolute inset-0 rounded-[10px]'

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
