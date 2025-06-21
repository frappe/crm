<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Visits" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="visitsListView?.customListActions"
        :actions="visitsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showVisitModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="visits"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    :filters="default_filters"
    doctype="CRM Site Visit"
  />
  <VisitListView
    ref="visitsListView"
    v-if="visits.data && rows.length"
    v-model="visits.data.page_length_count"
    v-model:list="visits"
    :rows="rows"
    :columns="visits.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: visits.data.row_count,
      totalCount: visits.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <div
    v-else-if="visits.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <VisitsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Visits')]) }}</span>
      <Button :label="__('Create')" @click="showVisitModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <VisitModal
    v-if="showVisitModal"
    v-model="showVisitModal"
    v-model:quickEntry="showQuickEntryModal"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="CRM Site Visit"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import VisitsIcon from '@/components/Icons/VisitsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import VisitModal from '@/components/Modals/VisitModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import VisitListView from '@/components/ListViews/VisitListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Site Visit')

const visitsListView = ref(null)
const showVisitModal = ref(false)
const showQuickEntryModal = ref(false)
const default_filters = {docstatus: ["!=", 2]}

// visits data is loaded in the ViewControls component
const visits = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !visits.value?.data?.data ||
    !['list', 'group_by'].includes(visits.value.data.view_type)
  )
    return []
  return visits.value?.data.data.map((visit) => {
    let _rows = {}
    visits.value?.data.rows.forEach((row) => {
      _rows[row] = visit[row]

      let fieldType = visits.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          visit[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, visit)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, visit)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, visit)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(visit[row]),
          timeAgo: __(timeAgo(visit[row])),
        }
      }
    })
    return _rows
  })
})
</script>
