<template>
  <Tooltip v-if="column.type === 'timeAgo'" :text="timestamp.label">
    <div class="truncate text-base">{{ timestamp.timeAgo }}</div>
  </Tooltip>
  <Tooltip
    v-else-if="column.type === 'dueDate'"
    :text="formatTaskDue(row, 'long')"
  >
    <div
      v-if="item"
      class="flex items-center gap-2 truncate text-base"
      :class="{ 'text-ink-red-7': column.overdue && isTaskOverdue(row) }"
    >
      <div class="shrink-0"><CalendarIcon /></div>
      <div class="truncate">{{ formatTaskDue(row) }}</div>
    </div>
  </Tooltip>
  <ListRowItem
    v-else
    :column="column"
    :row="row"
    :item="label"
    :align="column.align"
    class="overflow-hidden"
  >
    <template #prefix>
      <div v-if="column.type === 'status'" class="shrink-0">
        <IndicatorIcon :class="statusColor" />
      </div>
      <div v-else-if="column.type === 'taskStatus'" class="shrink-0">
        <TaskStatusIcon :status="item" />
      </div>
      <div v-else-if="column.type === 'priority'" class="shrink-0">
        <TaskPriorityIcon :priority="item" />
      </div>
      <div
        v-else-if="column.type === 'channel' && channels[item]"
        class="shrink-0"
      >
        <component :is="channels[item].icon" class="size-4" />
      </div>
      <div v-else-if="column.type === 'user' && item" class="shrink-0">
        <UserAvatar class="flex items-center" :user="item" size="sm" />
      </div>
    </template>
  </ListRowItem>
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { formatTaskDue, isTaskOverdue } from '@/utils/task'
import { Tooltip } from 'frappe-ui'
import { ListRowItem } from 'frappe-ui/experimental'
import { computed } from 'vue'

const props = defineProps({
  column: { type: Object, required: true },
  row: { type: Object, required: true },
  item: { type: [String, Number, Object], default: null },
})

const channels = {
  email: { label: __('Email'), icon: EmailIcon },
  whatsapp: { label: __('WhatsApp'), icon: WhatsAppIcon },
}

const { getLeadStatus, getDealStatus } = statusesStore()
const { getUser } = usersStore()

const timestamp = computed(() => timestampCell(props.item))

const statusColor = computed(() => {
  const getStatus =
    props.row.doctype === 'CRM Deal' ? getDealStatus : getLeadStatus
  return getStatus(props.item)?.color
})

const label = computed(() => {
  if (props.column.type === 'user')
    return props.item && getUser(props.item).full_name
  if (props.column.type === 'channel') return channels[props.item]?.label
  if (['taskStatus', 'priority'].includes(props.column.type))
    return __(props.item)
  return props.item
})
</script>
