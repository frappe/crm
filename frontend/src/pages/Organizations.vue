<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Organizations" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-4">
        <SmartFilterField
          v-if="!isMobileView"
          ref="desktopSmartFilter"
          doctype="CRM Organization"
          @update:filters="handleSmartFilter"
        />
        <CustomActions
          v-if="organizationsListView?.customListActions"
          :actions="organizationsListView.customListActions"
        />
        <Button
          variant="solid"
          :label="__('Create')"
          @click="showOrganizationModal = true"
        >
          <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
        </Button>
      </div>
    </template>
  </LayoutHeader>
  <div v-if="isMobileView" class="px-3 py-2 border-b">
    <SmartFilterField
      ref="mobileSmartFilter"
      doctype="CRM Organization"
      @update:filters="handleSmartFilter"
    />
  </div>
  <ViewControls
    ref="viewControls"
    v-model="organizations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Organization"
  />
  <OrganizationsListView
    ref="organizationsListView"
    v-if="organizations.data && rows.length"
    v-model="organizations.data.page_length_count"
    v-model:list="organizations"
    :rows="rows"
    :columns="organizations.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: organizations.data.row_count,
      totalCount: organizations.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="organizations.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <OrganizationsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Organizations')]) }}</span>
      <Button :label="__('Create')" @click="showOrganizationModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <OrganizationModal
    v-model="showOrganizationModal"
    v-model:quickEntry="showQuickEntryModal"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="CRM Organization"
  />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { formatDate, timeAgo, website, formatNumberIntoCurrency } from '@/utils'
import { ref, computed, watch } from 'vue'
import SmartFilterField from '@/components/SmartFilterField.vue'
import { isMobileView } from '@/composables/settings'

const organizationsListView = ref(null)
const showOrganizationModal = ref(false)
const showQuickEntryModal = ref(false)

// organizations data is loaded in the ViewControls component
const organizations = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !organizations.value?.data?.data ||
    !['list', 'group_by'].includes(organizations.value.data.view_type)
  )
    return []
  return organizations.value?.data.data.map((organization) => {
    let _rows = {}
    organizations.value?.data.rows.forEach((row) => {
      _rows[row] = organization[row]

      let fieldType = organizations.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          organization[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (row === 'organization_name') {
        _rows[row] = {
          label: organization.organization_name,
          logo: organization.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = {
          label: website(organization.website),
          value: organization.website // Store raw URL for filtering
        }
      } else if (row === 'industry') {
        _rows[row] = {
          label: organization.industry,
          value: organization.industry // Store raw value for filtering
        }
      } else if (row === 'annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(
          organization.annual_revenue,
          organization.currency,
        )
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(organization[row]),
          timeAgo: __(timeAgo(organization[row])),
        }
      }
    })
    return _rows
  })
})

const desktopSmartFilter = ref(null)
const mobileSmartFilter = ref(null)
const isResettingFilters = ref(false)

watch(() => organizations.value?.params?.filters, (newFilters) => {
  if (isResettingFilters.value) return;
  
  if (!newFilters || Object.keys(newFilters).length === 0) {
    isResettingFilters.value = true;
    desktopSmartFilter.value?.clearSearch();
    mobileSmartFilter.value?.clearSearch();
    isResettingFilters.value = false;
  }
}, { deep: true })

function handleSmartFilter(filters) {
  if (!viewControls.value || !filters) return;
  if (isResettingFilters.value) return;
  if (!organizations.value || !organizations.value.params) return;

  const currentFilters = organizations.value.params.filters || {};
  const standardFilters = {};
  Object.entries(currentFilters).forEach(([key, value]) => {
    if (!['website', 'industry'].includes(key)) {
      standardFilters[key] = value;
    }
  });

  organizations.value.params.filters = {
    ...standardFilters,
    ...filters
  };
  
  organizations.value.reload();
}
</script>
