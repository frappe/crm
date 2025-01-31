<template>
  <BaseListView
    :columns="columns"
    :rows="rows"
    :options="options"
    doctype="Customer"
    routeParamKey="customerId"
    nameField="customer_name"
    v-model="pageLengthCount"
    v-model:list="list"
    @loadMore="emit('loadMore')"
    @updatePageCount="emit('updatePageCount')"
    @columnWidthUpdated="emit('columnWidthUpdated')"
    @applyFilter="emit('applyFilter', $event)"
    @applyLikeFilter="emit('applyLikeFilter')"
    @likeDoc="emit('likeDoc', $event)"
  />
</template>

<script setup>
import BaseListView from './BaseListView.vue'

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
  'applyLikeFilter',
  'likeDoc',
])

const pageLengthCount = defineModel()
const list = defineModel('list')
</script> 