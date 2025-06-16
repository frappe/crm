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
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="visits"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    :filters="defaultFilter"
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
      <QuotationIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('CRM Site Visits')]) }}</span>
      <Button :label="__('Create')" @click="showQuotationModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>

  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="CRM Site Visit"
  />
  <AddressModal v-model="showAddressModal" v-model:address="address" />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { computed, ref } from 'vue'
import QuotationIcon from '@/components/Icons/QuotationIcon.vue'
import VisitListView from '../components/ListViews/VisitListView.vue'
import { filter } from 'lodash'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Site Visit')

const defaultFilter = {docstatus: ["!=", 2]};
const visitsListView = ref(null)
const showQuotationModal = ref(false)
const showQuickEntryModal = ref(false)
const showAddressModal = ref(false)

// Quotations data is loaded in the ViewControls component
const visits = ref({})
const address = ref({})
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
        (col) => (col.key || col.value) === row,
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
          fieldType === 'Datetime',
        )
      }

      if (fieldType && fieldType === 'Currency') {
        _rows[row] = getFormattedCurrency(row, visit)
      }

      if (fieldType && fieldType === 'Float') {
        _rows[row] = getFormattedFloat(row, visit)
      }

      if (fieldType && fieldType === 'Percent') {
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
