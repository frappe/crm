<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Organizations" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="organizationsListView?.customListActions"
        :actions="organizationsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="lucide-plus"
        @click="showOrganizationModal = true"
      />
    </template>
  </LayoutHeader>

  <!-- Organizations Status Tabs -->
  <div class="border-b border-outline-gray-2 bg-surface-base px-3 sm:px-5">
    <div class="flex items-center gap-6 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="flex items-center gap-2 border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap focus:outline-none"
        :class="[
          activeTab === tab.value
            ? 'border-surface-gray-9 text-ink-gray-9 font-semibold dark:border-ink-white dark:text-ink-white'
            : 'border-transparent text-ink-gray-5 hover:text-ink-gray-8 dark:text-ink-gray-4 dark:hover:text-ink-white',
        ]"
        @click="setTab(tab.value)"
      >
        <span>{{ tab.label }}</span>
        <Badge
          variant="solid"
          size="sm"
          :class="[
            activeTab === tab.value
              ? 'bg-surface-gray-9 text-surface-white dark:bg-surface-gray-7 dark:text-ink-white'
              : 'bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3',
          ]"
        >
          {{ tab.count }}
        </Badge>
      </button>
    </div>
  </div>

  <ViewControls
    ref="viewControls"
    v-model="organizations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    :filters="activeTabFilters"
    doctype="CRM Organization"
  />
  <OrganizationsListView
    v-if="organizations.data && rows.length"
    ref="organizationsListView"
    v-model="organizations.data.page_length_count"
    v-model:list="organizations"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: organizations.data.row_count,
      totalCount: organizations.data.total_count,
    }"
    @reload="fetchTabCounts"
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
  <EmptyState
    v-else-if="organizations.data && !rows.length"
    name="Organizations"
    :icon="OrganizationsIcon"
    :title="__('No organizations yet')"
    :description="
      __('Organizations are the companies your contacts and deals belong to.')
    "
    :filtered="!!Object.keys(organizations.params?.filters || {}).length || activeTab !== 'all'"
    docsLink="https://docs.frappe.io/crm/organization"
    importDoctype="CRM Organization"
    @create="showOrganizationModal = true"
  />
  <OrganizationModal
    v-if="showOrganizationModal"
    v-model="showOrganizationModal"
  />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, website } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { Badge, createResource } from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '../components/ListViews/EmptyState.vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Organization')

const route = useRoute()
const router = useRouter()

const organizationsListView = ref(null)
const showOrganizationModal = ref(false)

// organizations data is loaded in the ViewControls component
const organizations = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// 1. Active Tab (default: all)
const activeTab = ref(
  ['all', 'active', 'inactive'].includes(route.query.tab)
    ? route.query.tab
    : 'all',
)

// 2. Dynamic Counts for the tabs
const tabCounts = ref({
  all: 0,
  active: 0,
  inactive: 0,
})

const tabCountsResource = createResource({
  url: 'crm.api.organization.get_organization_tab_counts',
  auto: true,
  onSuccess: (data) => {
    if (data) {
      tabCounts.value = {
        all: data.all ?? 0,
        active: data.active ?? 0,
        inactive: data.inactive ?? 0,
      }
    }
  },
})

function fetchTabCounts() {
  tabCountsResource.reload()
}

onMounted(() => {
  fetchTabCounts()
})

watch(
  () => organizations.value?.data,
  () => {
    fetchTabCounts()
  },
)

watch(showOrganizationModal, (val) => {
  if (!val) {
    fetchTabCounts()
  }
})

const tabs = computed(() => [
  {
    label: __('All'),
    value: 'all',
    count: tabCounts.value.all,
  },
  {
    label: __('Active'),
    value: 'active',
    count: tabCounts.value.active,
  },
  {
    label: __('Inactive'),
    value: 'inactive',
    count: tabCounts.value.inactive,
  },
])

function setTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  router.replace({
    query: {
      ...route.query,
      tab: tab === 'all' ? undefined : tab,
    },
  })
  fetchTabCounts()
  nextTick(() => {
    viewControls.value?.reload?.()
  })
}

// 3. Mutually exclusive active tab filters
const activeTabFilters = computed(() => {
  if (activeTab.value === 'active') {
    return {
      status: 'Active',
    }
  } else if (activeTab.value === 'inactive') {
    return {
      status: 'Inactive',
    }
  }
  return {}
})

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

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, organization)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, organization)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, organization)
      }

      if (row === 'organization_name') {
        _rows[row] = {
          label: organization.organization_name,
          logo: organization.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(organization.website)
      } else if (row === 'status') {
        _rows[row] = organization.status || 'Active'
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(organization[row])
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = organizations.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})
</script>
