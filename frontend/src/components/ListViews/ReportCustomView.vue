<template>
  <ListView
    :class="[$attrs.class, 'deal-chip']"
    :columns="columns"
    :rows="report_data"
    :options="{
      getRowRoute: (row) => ({
        name: 'Deal',
        params: { dealId: 1 },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      >

      </ListHeaderItem>
    </ListHeader>
    <ListRows :rows="report_data" v-slot="{ idx, column, item, row }">
      <div>{{ row[column.fieldname] }}</div>
    </ListRows>
  </ListView>

</template>

<script setup>
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
} from 'frappe-ui'
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  report_data: {
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
])
const route = useRoute()

const pageLengthCount = defineModel()
const list = defineModel('list')
onMounted(() => {
  emit('loadMore')
});

</script>
