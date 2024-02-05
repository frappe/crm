<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('showTask', row.name),
      selectable: options.selectable,
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" />
    <ListRows id="list-rows">
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <div
          v-if="column.key === 'due_date'"
          class="flex items-center gap-2 text-base"
        >
          <CalendarIcon />
          <div v-if="item">
            <Tooltip :text="dateFormat(item, 'ddd, MMM D, YYYY')">
              {{ dateFormat(item, 'D MMM') }}
            </Tooltip>
          </div>
        </div>
        <ListRowItem v-else :item="item">
          <template #prefix>
            <div v-if="column.key === 'status'">
              <TaskStatusIcon :status="item" />
            </div>
            <div v-else-if="column.key === 'priority'">
              <TaskPriorityIcon :priority="item" />
            </div>
            <div v-else-if="column.key === 'assigned_to'">
              <Avatar
                v-if="item.full_name"
                class="flex items-center"
                :image="item.user_image"
                :label="item.full_name"
                size="sm"
              />
            </div>
          </template>
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
          >
            {{ item.timeAgo }}
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-gray-900"
            />
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Button
          theme="red"
          variant="subtle"
          label="Delete"
          @click="deleteTask(selections, unselectAll)"
        />
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    class="border-t px-5 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
</template>
<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import { dateFormat } from '@/utils'
import { globalStore } from '@/stores/global'
import {
  Avatar,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  call,
  Tooltip,
} from 'frappe-ui'
import { defineModel, watch } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits(['loadMore', 'updatePageCount', 'showTask', 'reload'])

const pageLengthCount = defineModel()

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const { $dialog } = globalStore()

function deleteTask(selections, unselectAll) {
  let title = 'Delete task'
  let message = 'Are you sure you want to delete this task?'

  if (selections.size > 1) {
    title = 'Delete tasks'
    message = 'Are you sure you want to delete these tasks?'
  }

  $dialog({
    title: title,
    message: message,
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          for (const selection of selections) {
            await call('frappe.client.delete', {
              doctype: 'CRM Task',
              name: selection,
            })
          }
          close()
          unselectAll()
          emit('reload')
        },
      },
    ],
  })
}
</script>
