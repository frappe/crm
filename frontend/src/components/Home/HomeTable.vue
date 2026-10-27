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
    <ListHeader v-if="showHeader" class="sticky top-0 z-10">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      />
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
import { ListHeader, ListHeaderItem, ListView } from 'frappe-ui/experimental'

defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  rowKey: { type: String, default: 'name' },
  showHeader: { type: Boolean, default: false },
  rowRoute: { type: Function, default: null },
  onRowClick: { type: Function, default: null },
})
</script>
