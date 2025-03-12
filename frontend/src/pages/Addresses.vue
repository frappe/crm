<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Addresses" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="addressesListView?.customListActions"
        :actions="addressesListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showAddressModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="addresses"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Address"
  />
  <AddressesListView
    ref="addressesListView"
    v-if="addresses.data && rows.length"
    v-model="addresses.data.page_length_count"
    v-model:list="addresses"
    :rows="rows"
    :columns="addresses.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: addresses.data.row_count,
      totalCount: addresses.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="addresses.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <AddressIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Addresses')]) }}</span>
      <Button :label="__('Create')" @click="showAddressModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <AddressModal
    v-model="showAddressModal"
    v-model:quickEntry="showQuickEntryModal"
    :address="{}"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Address"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import AddressIcon from '@/components/Icons/AddressIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AddressesListView from '@/components/ListViews/AddressesListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { customersStore } from '@/stores/customers.js'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { ref, computed } from 'vue'

const { getCustomer } = customersStore()

const showAddressModal = ref(false)
const showQuickEntryModal = ref(false)

const addressesListView = ref(null)

// addresses data is loaded in the ViewControls component
const addresses = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !addresses.value?.data?.data ||
    !['list', 'group_by'].includes(addresses.value.data.view_type)
  )
    return []
  return addresses.value?.data.data.map((address) => {
    let _rows = {}
    addresses.value?.data.rows.forEach((row) => {
      _rows[row] = address[row]

      if (row == 'full_name') {
        _rows[row] = {
          label: address.full_name,
          image_label: address.full_name,
          image: address.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: address.company_name,
          logo: getCustomer(address.company_name)?.image,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(address[row], dateTooltipFormat),
          timeAgo: __(timeAgo(address[row])),
        }
      }
    })
    return _rows
  })
})
</script>
