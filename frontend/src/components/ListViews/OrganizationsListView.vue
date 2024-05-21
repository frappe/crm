<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Organization',
        params: { organizationId: row.name },
      }),
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
        <ListRowItem :item="item">
          <template #prefix>
            <div v-if="column.key === 'organization_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.logo"
                :label="item.label"
                size="sm"
              />
            </div>
          </template>
          <template #default="{ label }">
            <div
              v-if="['modified', 'creation'].includes(column.key)"
              class="truncate text-base"
              @click="
                (event) => emit('applyFilter', { event, idx, column, item })
              "
            >
              <Tooltip :text="item.label">
                <div>{{ item.timeAgo }}</div>
              </Tooltip>
            </div>
            <div v-else-if="column.type === 'Check'">
              <FormControl
                type="checkbox"
                :modelValue="item"
                :disabled="true"
                class="text-gray-900"
              />
            </div>
            <div
              v-else
              class="truncate text-base"
              @click="
                (event) => emit('applyFilter', { event, idx, column, item })
              "
            >
              {{ label }}
            </div>
          </template>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
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
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="CRM Organization"
    :options="{
      hideAssign: true,
    }"
  />
</template>
<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
  Dropdown,
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
  'columnWidthUpdated',
  'applyFilter',
])

const pageLengthCount = defineModel()
const list = defineModel('list')

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: listBulkActionsRef.value?.customListActions,
})
</script>
