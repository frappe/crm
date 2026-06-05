<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Quotations" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" iconLeft="plus" @click="$router.push({ name: 'NewQuotation' })" />
    </template>
  </LayoutHeader>

  <ViewControls ref="viewControls" v-model="quotations" v-model:loadMore="loadMore" v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount" doctype="CRM Quotation" :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }" />

  <KanbanView v-if="route.params.viewType == 'kanban'" v-model="quotations" :options="{
    getRoute: (row) => ({
      name: 'Quotation',
      params: { quotationId: row.name },
      query: { view: route.query.view, viewType: route.params.viewType },
    }),
  }" @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)" />

  <QuotationsListView v-else-if="quotations.data && rows.length" v-model="quotations.data.page_length_count"
    v-model:list="quotations" :rows="rows" :columns="columns" :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: quotations.data.row_count,
      totalCount: quotations.data.total_count,
    }" @loadMore="() => loadMore++" @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)" @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)" @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="(s) => viewControls.updateSelections(s)" />

  <EmptyState v-else-if="quotations.data && !rows.length" name="Quotations" :icon="QuotationIcon" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuotationIcon from '@/components/Icons/QuotationIcon.vue'
import QuotationsListView from '@/components/ListViews/QuotationsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { Button, createResource } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'

const { getFormattedCurrency, getFormattedFloat } = getMeta('CRM Quotation')

const route = useRoute()
const router = useRouter()

const quotations = ref({})
const loadMore = ref(false) 
const triggerResize = ref(false)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// ── Create new quotation & redirect to detail ──────────────────
const createDoc = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    return {
      doc: {
        doctype: 'CRM Quotation',
        subject: 'New Quotation',
        state: 'Draft',
        date: new Date().toISOString().split('T')[0],
        currency: 'IDR',
        rate: 1,
      },
    }
  },
  onSuccess(doc) {
    router.push({ name: 'Quotation', params: { quotationId: doc.name } })
  },
  onError(err) {
    alert(err.message || 'Failed to create quotation')
  },
})

function createQuotation() {
  createDoc.submit()
}

// ── List view rows ─────────────────────────────────────────────
const rows = computed(() => {
  if (!quotations.value?.data?.data) return []
  return parseRows(quotations.value?.data.data, quotations.value.data.columns)
})

const columns = computed(() => {
  let _columns = quotations.value?.data?.columns || []
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) return { ...col, align: 'right' }
      return col
    })
  }
  return _columns
})

function parseRows(rowsData, columns = []) {
  return rowsData.map((q) => {
    let _rows = {}
    quotations.value.data.rows.forEach((row) => {
      _rows[row] = q[row]

      let fieldType = columns?.find((c) => (c.key || c.value) == row)?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(q[row], '', true, fieldType == 'Datetime')
      }
      if (fieldType === 'Currency') _rows[row] = getFormattedCurrency(row, q)
      if (fieldType === 'Float') _rows[row] = getFormattedFloat(row, q)

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(q[row]),
          timeAgo: __(timeAgo(q[row])),
        }
      }
    })
    return _rows
  })
}
</script>