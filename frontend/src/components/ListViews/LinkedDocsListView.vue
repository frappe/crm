<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: true,
      showTooltip: true,
      resizeColumn: true,
    }"
    row-key="reference_docname"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
    ref="listViewRef"
  >
    <ListHeader @columnWidthUpdated="emit('columnWidthUpdated')">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
      </ListHeaderItem>
    </ListHeader>
    <div class="*:mx-0 *:sm:mx-0">
      <ListRows :rows="rows" v-slot="{ idx, column, item, row }">
        <ListRowItem
          :item="item"
          @click="listViewRef.toggleRow(row['reference_docname'])"
        >
          <template #default="{ label }">
            <div
              v-if="column.key === 'title'"
              class="truncate text-base flex gap-2"
            >
              <span>
                {{ label }}
              </span>
              <FeatherIcon
                name="external-link"
                class="h-4 w-4 cursor-pointer"
                @click.stop="viewLinkedDoc(row)"
              />
            </div>
            <span
              v-if="column.key === 'reference_doctype'"
              class="truncate text-base flex gap-2"
            >
              {{ getDoctypeName(row.reference_doctype) }}
            </span>
          </template>
        </ListRowItem>
      </ListRows>
    </div>
  </ListView>
</template>

<script setup>
import ListRows from '@/components/ListViews/ListRows.vue'
import { ListView, ListHeader, ListHeaderItem, ListRowItem } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  linkedDocsResource: {
    type: Object,
    required: true,
  },
  unlinkLinkedDoc: {
    type: Function,
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
  'selectionsChanged',
])

const listViewRef = ref(null)

const viewLinkedDoc = (doc) => {
  let page = ''
  let id = ''
  switch (doc.reference_doctype) {
    case 'CRM Lead':
      page = 'leads'
      id = doc.reference_docname
      break
    case 'CRM Call Log':
      page = 'call-logs'
      id = `view?open=${doc.reference_docname}`
      break
    case 'CRM Task':
      page = 'tasks'
      id = `view?open=${doc.reference_docname}`
      break
    case 'Contact':
      page = 'contacts'
      id = doc.reference_docname
      break
    case 'CRM Organization':
      page = 'organizations'
      id = doc.reference_docname
      break
    case 'FCRM Note':
      page = 'notes'
      id = `view?open=${doc.reference_docname}`
      break
    default:
      break
  }
  window.open(`/crm/${page}/${id}`)
}

const getDoctypeName = (doctype) => {
  return doctype.replace(/^(CRM|FCRM)\s*/, '')
}
</script>
