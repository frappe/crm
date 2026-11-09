<template>
  <!-- ListView sizes to its content by default; Home cards truncate instead. Without the
       inner overflow, the header sticks to ListView's own scroll box when rows overflow. -->
  <ListView
    class="!w-full !overflow-visible"
    :columns="columns"
    :rows="rows"
    :rowKey="rowKey"
    :options="{
      getRowRoute: rowRoute,
      onRowClick,
      selectable: false,
      showTooltip: true,
      resizeColumn: false,
    }"
  >
    <ListHeader class="sticky top-0 z-10">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      >
        <Tooltip v-if="sort" :text="column.tooltip" :disabled="!column.tooltip">
          <button
            type="button"
            class="flex min-w-0 items-center gap-0.5 hover:text-ink-gray-8"
            :class="{ 'text-ink-gray-8': sort.key === column.key }"
            @click="sort = nextSort(sort, column)"
          >
            <span class="truncate">{{ column.label }}</span>
            <span
              v-if="sort.key === column.key"
              aria-hidden="true"
              class="size-3 shrink-0"
              :class="sort.descending ? 'lucide-arrow-down' : 'lucide-arrow-up'"
            />
          </button>
        </Tooltip>
        <Tooltip v-else-if="column.tooltip" :text="column.tooltip">
          <div class="truncate">{{ column.label }}</div>
        </Tooltip>
      </ListHeaderItem>
    </ListHeader>
    <div class="*:mx-0 *:sm:mx-0">
      <ListRows v-slot="{ column, item, row }" :rows="rows">
        <slot :name="column.key" v-bind="{ column, item, row }">
          <HomeCell :column="column" :item="item" :row="row" />
        </slot>
      </ListRows>
    </div>
  </ListView>
</template>
<script setup>
import HomeCell from '@/components/Home/HomeCell.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { nextSort } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { ListHeader, ListHeaderItem, ListView } from 'frappe-ui/experimental'

defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  rowKey: { type: String, default: 'name' },
  rowRoute: { type: Function, default: null },
  onRowClick: { type: Function, default: null },
})

const sort = defineModel('sort', { type: Object, default: null })
</script>
