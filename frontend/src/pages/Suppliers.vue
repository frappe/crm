<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Suppliers" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="suppliersListView?.customListActions"
        :actions="suppliersListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showSupplierModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="suppliers"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Supplier"
  />
  <SuppliersListView
    ref="suppliersListView"
    v-if="suppliers.data && rows.length"
    v-model="suppliers.data.page_length_count"
    v-model:list="suppliers"
    :rows="rows"
    :columns="suppliers.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: suppliers.data.row_count,
      totalCount: suppliers.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="suppliers.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <OrganizationsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Suppliers')]) }}</span>
      <Button :label="__('Create')" @click="showSupplierModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Supplier"
  />
  <AddressModal v-model="showAddressModal" v-model:address="address" />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import SuppliersListView from '@/components/ListViews/SuppliersListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo, website } from '@/utils'
import { call } from 'frappe-ui'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Supplier')

const suppliersListView = ref(null)
const showSupplierModal = ref(false)
const showQuickEntryModal = ref(false)
const showAddressModal = ref(false)

// suppliers data is loaded in the ViewControls component
const suppliers = ref({})
const address = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !suppliers.value?.data?.data ||
    !['list', 'group_by'].includes(suppliers.value.data.view_type)
  )
    return []
  return suppliers.value?.data.data.map((supplier) => {
    let _rows = {}
    suppliers.value?.data.rows.forEach((row) => {
      _rows[row] = supplier[row]

      let fieldType = suppliers.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          supplier[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, supplier)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, supplier)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, supplier)
      }

      if (row === 'supplier_name') {
        _rows[row] = {
          label: supplier.supplier_name,
          image: supplier.image,
        }
      } else if (row === 'website') {
        _rows[row] = website(supplier.website)
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(supplier[row]),
          timeAgo: __(timeAgo(supplier[row])),
        }
      }
    })
    return _rows
  })
})

async function openAddressModal(_address) {
  if (_address) {
    _address = await call('frappe.client.get', {
      doctype: 'Address',
      name: _address,
    })
  }
  showAddressModal.value = true
  address.value = _address || {}
}
</script> 