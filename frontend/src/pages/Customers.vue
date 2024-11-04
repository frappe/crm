<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Customers" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="customersListView?.customListActions"
        :actions="customersListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showCustomerModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="customers"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Customer"
  />
  <CustomersListView
    ref="customersListView"
    v-if="customers.data && rows.length"
    v-model="customers.data.page_length_count"
    v-model:list="customers"
    :rows="rows"
    :columns="customers.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: customers.data.row_count,
      totalCount: customers.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="customers.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <CustomersIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Customers')]) }}</span>
      <Button :label="__('Create')" @click="showCustomerModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <CustomerModal
    v-model="showCustomerModal"
    v-model:quickEntry="showQuickEntryModal"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Customer"
  />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import CustomersIcon from '@/components/Icons/CustomersIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import CustomerModal from '@/components/Modals/CustomerModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import CustomersListView from '@/components/ListViews/CustomersListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  website,
  formatNumberIntoCurrency,
} from '@/utils'
import { ref, computed } from 'vue'

const customersListView = ref(null)
const showCustomerModal = ref(false)
const showQuickEntryModal = ref(false)

// customers data is loaded in the ViewControls component
const customers = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !customers.value?.data?.data ||
    !['list', 'group_by'].includes(customers.value.data.view_type)
  )
    return []
  return customers.value?.data.data.map((customer) => {
    let _rows = {}
    customers.value?.data.rows.forEach((row) => {
      _rows[row] = customer[row]

      if (row === 'customer_name') {
        _rows[row] = {
          label: customer.customer_name,
          logo: customer.image,
        }
      } else if (row === 'website') {
        _rows[row] = website(customer.website)
      } else if (row === 'custom_annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(
          customer.custom_annual_revenue,
          customer.currency,
        )
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(customer[row], dateTooltipFormat),
          timeAgo: __(timeAgo(customer[row])),
        }
      }
    })
    return _rows
  })
})
</script>
