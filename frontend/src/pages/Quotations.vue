<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Quotations" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="quotationsListView?.customListActions"
        :actions="quotationsListView.customListActions"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="quotations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Quotation"
  />
  <QuotationsListView
    ref="quotationsListView"
    v-if="quotations.data && rows.length"
    v-model="quotations.data.page_length_count"
    v-model:list="quotations"
    :rows="rows"
    :columns="quotations.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: quotations.data.row_count,
      totalCount: quotations.data.total_count,
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
    v-else-if="quotations.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <QuotationIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Quotations')]) }}</span>
      <Button :label="__('Create')" @click="showQuotationModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>

  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Quotation"
  />
  <AddressModal v-model="showAddressModal" v-model:address="address" />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { call } from 'frappe-ui'
import { computed, ref } from 'vue'
import QuotationsListView from '@/components/ListViews/QuotationsListView.vue'
import QuotationIcon from '@/components/Icons/QuotationIcon.vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Quotation')

const quotationsListView = ref(null)
const showQuotationModal = ref(false)
const showQuickEntryModal = ref(false)
const showAddressModal = ref(false)

// Quotations data is loaded in the ViewControls component
const quotations = ref({})
const address = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !quotations.value?.data?.data ||
    !['list', 'group_by'].includes(quotations.value.data.view_type)
  )
    return []
  return quotations.value?.data.data.map((quotation) => {
    let _rows = {}
    quotations.value?.data.rows.forEach((row) => {
      _rows[row] = quotation[row]

      let fieldType = quotations.value?.data.columns?.find(
        (col) => (col.key || col.value) === row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          quotation[row],
          '',
          true,
          fieldType === 'Datetime',
        )
      }

      if (fieldType && fieldType === 'Currency') {
        _rows[row] = getFormattedCurrency(row, quotation)
      }

      if (fieldType && fieldType === 'Float') {
        _rows[row] = getFormattedFloat(row, quotation)
      }

      if (fieldType && fieldType === 'Percent') {
        _rows[row] = getFormattedPercent(row, quotation)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(quotation[row]),
          timeAgo: __(timeAgo(quotation[row])),
        }
      }
    })
    return _rows
  })
})

</script>
