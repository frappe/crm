<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('showEmailTemplate', row.name),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" @columnWidthUpdated="emit('columnWidthUpdated')" />
    <ListRows id="list-rows">
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ idx, column, item }"
        :row="row"
      >
        <ListRowItem
          :item="item"
          @click="(event) => emit('applyFilter', { event, idx, column, item })"
        >
          <!-- <template #prefix>

          </template> -->
          <Tooltip
            :text="item.label"
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
          >
            {{ item.timeAgo }}
          </Tooltip>
          <div v-else-if="column.key === 'status'" class="truncate text-base">
            <Badge
              :variant="'subtle'"
              :theme="item.color"
              size="md"
              :label="item.label"
            />
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
            @click="deleteEmailTemplate(selections, unselectAll)"
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
    doctype="Email Template"
    :selectedValues="selectedValues"
    @reload="emit('reload')"
  />
</template>
<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import EditValueModal from '@/components/Modals/EditValueModal.vue'
import { globalStore } from '@/stores/global'
import {
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
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'showEmailTemplate',
  'reload',
  'columnWidthUpdated',
  'applyFilter',
])

const pageLengthCount = defineModel()

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const { $dialog } = globalStore()

function deleteEmailTemplate(selections, unselectAll) {
  let title = 'Delete email template'
  let message = 'Are you sure you want to delete this email template?'

  if (selections.size > 1) {
    title = 'Delete email templates'
    message = 'Are you sure you want to delete these email templates?'
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
              doctype: 'Email Template',
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
