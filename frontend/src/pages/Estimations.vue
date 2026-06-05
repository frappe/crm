<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Estimations" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" iconLeft="plus" @click="$router.push({ name: 'NewEstimation' })" />
    </template>
  </LayoutHeader>

  <ViewControls ref="viewControls" v-model="estimations" v-model:loadMore="loadMore" v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount" doctype="CRM Estimation" :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }" />

  <KanbanView v-if="route.params.viewType == 'kanban'" v-model="estimations" :options="{
    getRoute: (row) => ({
      name: 'Estimation',
      params: { estimationId: row.name },
      query: { view: route.query.view, viewType: route.params.viewType },
    }),
  }" @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)" />

  <EstimationsListView v-else-if="estimations.data && rows.length" v-model="estimations.data.page_length_count"
    v-model:list="estimations" :rows="rows" :columns="columns" :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: estimations.data.row_count,
      totalCount: estimations.data.total_count,
    }" @loadMore="() => loadMore++" @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)" @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)" @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="(s) => viewControls.updateSelections(s)" />

  <EmptyState v-else-if="estimations.data && !rows.length" name="Estimations" :icon="EstimationIcon" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import EstimationIcon from '@/components/Icons/EstimationIcon.vue'
import EstimationsListView from '@/components/ListViews/EstimationsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { Button } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, computed } from 'vue'

const { getFormattedCurrency, getFormattedFloat } = getMeta('CRM Estimation')

const route = useRoute()

const estimations = ref({})
const loadMore = ref(false)
const triggerResize = ref(false)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (!estimations.value?.data?.data) return []
  return parseRows(estimations.value?.data.data, estimations.value.data.columns)
})

const columns = computed(() => {
  let _columns = estimations.value?.data?.columns || []
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
    estimations.value.data.rows.forEach((row) => {
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
