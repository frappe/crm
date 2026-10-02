<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: false,
      showTooltip: false,
      resizeColumn: false,
      onRowClick: (row) => openRow(row),
    }"
    row-key="name"
  >
    <ListHeader class="sm:mx-5 mx-3">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      />
    </ListHeader>
    <ListRows v-slot="{ column, item }" :rows="rows" :doctype="doctype">
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <div class="truncate text-base">{{ item }}</div>
      </ListRowItem>
    </ListRows>
  </ListView>
  <div v-if="rows.length < totalCount" class="flex justify-center py-3">
    <Button
      :label="__('Load More')"
      :loading="loading"
      @click="emit('loadMore')"
    />
  </div>
</template>

<script setup>
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
} from 'frappe-ui/experimental'
import { useRouter } from 'vue-router'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  totalCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  doctype: { type: String, default: '' },
})

const emit = defineEmits(['loadMore'])

const router = useRouter()

// The server only passes same-origin paths in `url`
function openRow(row) {
  if (!row.url) return
  if (row.url === '/crm' || row.url.startsWith('/crm/')) {
    router.push(row.url.slice('/crm'.length) || '/')
  } else {
    window.open(row.url, '_blank')
  }
}
</script>
