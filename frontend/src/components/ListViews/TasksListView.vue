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
        <Tooltip
          v-if="column.key === 'due_date'"
          class="flex items-center gap-2 truncate text-base"
          :text="dateFormat(item, 'ddd, MMM D, YYYY | hh:mm a')"
        >
          <div>
            <CalendarIcon />
          </div>
          <div v-if="item" class="truncate">
            {{ dateFormat(item, 'D MMM, hh:mm a') }}
          </div>
        </Tooltip>
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
        <div class="flex gap-2">
          <Button
            theme="red"
            variant="subtle"
            label="Delete"
            @click="deleteTask(selections, unselectAll)"
          />
          <Button
            variant="subtle"
            label="Edit"
            @click="editValues(selections, unselectAll)"
          >
            <template #prefix>
              <EditIcon class="h-3 w-3" />
            </template>
          </Button>
        </div>
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
  <EditValueModal
    v-model="showEditModal"
    v-model:unselectAll="unselectAllAction"
    doctype="CRM Task"
    :selectedValues="selectedValues"
    @reload="emit('reload')"
  />
</template>
<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import EditValueModal from '@/components/Modals/EditValueModal.vue'
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
import { ref, watch } from 'vue'

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

const showEditModal = ref(false)
const selectedValues = ref([])
const unselectAllAction = ref(() => {})

function editValues(selections, unselectAll) {
  selectedValues.value = selections
  showEditModal.value = true
  unselectAllAction.value = unselectAll
}
</script>
