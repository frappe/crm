<template>
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs v-model="viewControls" routeName="Properties" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="propertiesListView?.customListActions"
          :actions="propertiesListView.customListActions"
        />
        <Button
          variant="solid"
          :label="__('Create')"
          @click="showPropertyModal = true"
        >
          <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
        </Button>
      </template>
    </LayoutHeader>

   <ViewControls
      ref="viewControls"
      v-model="properties"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="Item"
    />
    <PropertiesListView
      ref="propertiesListView"
      v-if="properties.data && rows.length"
      v-model="properties.data.page_length_count"
      v-model:list="properties"
      :rows="rows"
      :columns="properties.data.columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: properties.data.row_count,
        totalCount: properties.data.total_count,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
    />
    <div
      v-else-if="properties.data"
      class="flex h-full items-center justify-center"
    >
      <div
        class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
      >
        <OrganizationsIcon class="h-10 w-10" />
        <span>{{ __('No {0} Found', [__('Properties')]) }}</span>
        <Button :label="__('Create')" @click="showPropertyModal = true">
          <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
        </Button>
      </div>
    </div>
    <PropertyModal
      v-model="showPropertyModal"
      v-model:showQuickEntryModal="showQuickEntryModal"
      @openAddressModal="(_address) => openAddressModal(_address)"
    />
    <QuickEntryModal
      v-if="showQuickEntryModal"
      v-model="showQuickEntryModal"
      doctype="Item"
    />
    <AddressModal v-model="showAddressModal" v-model:address="address" />
  </template>
  <script setup>
  import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
  import CustomActions from '@/components/CustomActions.vue'
  import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
  import LayoutHeader from '@/components/LayoutHeader.vue'
  import PropertyModal from '@/components/Modals/PropertyModal.vue'
  import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
  import AddressModal from '@/components/Modals/AddressModal.vue'
  import PropertiesListView from '@/components/ListViews/PropertiesListView.vue'
  import ViewControls from '@/components/ViewControls.vue'
  import { getMeta } from '@/stores/meta'
  import { formatDate, timeAgo, website } from '@/utils'
  import { call } from 'frappe-ui'
  import { ref, computed } from 'vue'

  const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
    getMeta('Item')

  const propertiesListView = ref(null)
  const showPropertyModal = ref(false)
  const showQuickEntryModal = ref(false)
  const showAddressModal = ref(false)

  // properties data is loaded in the ViewControls component
  const properties = ref({})
  const address = ref({})
  const loadMore = ref(1)
  const triggerResize = ref(1)
  const updatedPageCount = ref(20)
  const viewControls = ref(null)

  const rows = computed(() => {
    if (
      !properties.value?.data?.data ||
      !['list', 'group_by'].includes(properties.value.data.view_type)
    )
      return []
    return properties.value?.data.data.map((property) => {
      let _rows = {}
      properties.value?.data.rows.forEach((row) => {
        _rows[row] = property[row]

        let fieldType = properties.value?.data.columns?.find(
          (col) => (col.key || col.value) == row,
        )?.type

        if (
          fieldType &&
          ['Date', 'Datetime'].includes(fieldType) &&
          !['modified', 'creation'].includes(row)
        ) {
          _rows[row] = formatDate(
            property[row],
            '',
            true,
            fieldType == 'Datetime',
          )
        }

        if (fieldType && fieldType == 'Currency') {
          _rows[row] = getFormattedCurrency(row, property)
        }

        if (fieldType && fieldType == 'Float') {
          _rows[row] = getFormattedFloat(row, property)
        }

        if (fieldType && fieldType == 'Percent') {
          _rows[row] = getFormattedPercent(row, property)
        }

        if (row === 'property_name') {
          _rows[row] = {
            label: property.property_name,
            logo: property.property_logo,
          }
        } else if (row === 'website') {
          _rows[row] = website(property.website)
        } else if (['modified', 'creation'].includes(row)) {
          _rows[row] = {
            label: formatDate(property[row]),
            timeAgo: __(timeAgo(property[row])),
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

