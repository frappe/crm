<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        label="Create"
        @click="showOrganizationModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex items-center justify-between px-5 pb-4 pt-3">
    <div class="flex items-center gap-2">
      <Dropdown :options="viewsDropdownOptions">
        <template #default="{ open }">
          <Button :label="currentView.label">
            <template #prefix>
              <FeatherIcon :name="currentView.icon" class="h-4" />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>
    <div class="flex items-center gap-2">
      <Filter doctype="CRM Organization" />
      <SortBy doctype="CRM Organization" />
      <ViewSettings doctype="CRM Organization" v-model="organizations" />
    </div>
  </div>
  <OrganizationsListView
    v-if="organizations.data"
    :rows="rows"
    :columns="organizations.data.columns"
  />
  <OrganizationModal v-model="showOrganizationModal" :organization="{}" />
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import ViewSettings from '@/components/ViewSettings.vue'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import { FeatherIcon, Breadcrumbs, Dropdown, createResource } from 'frappe-ui'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
} from '@/utils'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const showOrganizationModal = ref(false)

const currentOrganization = computed(() => {
  return organizations.data?.data?.find(
    (organization) => organization.name === route.params.organizationId
  )
})

const breadcrumbs = computed(() => {
  let items = [{ label: 'Organizations', route: { name: 'Organizations' } }]
  if (!currentOrganization.value) return items
  items.push({
    label: currentOrganization.value.name,
    route: {
      name: 'Organization',
      params: { organizationId: currentOrganization.value.name },
    },
  })
  return items
})

const currentView = ref({
  label: 'List',
  icon: 'list',
})

function getParams() {
  const filters = getArgs() || {}
  const order_by = getOrderBy() || 'modified desc'

  return {
    doctype: 'CRM Organization',
    filters: filters,
    order_by: order_by,
  }
}

const organizations = createResource({
  url: 'crm.api.doc.get_list_data',
  params: getParams(),
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    organizations.params = getParams()
    organizations.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    organizations.params = getParams()
    organizations.reload()
  }, 300),
  { deep: true }
)

const rows = computed(() => {
  if (!organizations.data?.data) return []
  return organizations.data.data.map((organization) => {
    let _rows = {}
    organizations.data.rows.forEach((row) => {
      _rows[row] = organization[row]

      if (row === 'organization_name') {
        _rows[row] = {
          label: organization.organization_name,
          logo: organization.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(organization.website)
      } else if (row === 'annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(organization.annual_revenue)
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(organization[row], dateTooltipFormat),
          timeAgo: timeAgo(organization[row]),
        }
      }
    })
    return _rows
  })
})

const viewsDropdownOptions = [
  {
    label: 'List',
    icon: 'list',
    onClick() {
      currentView.value = {
        label: 'List',
        icon: 'list',
      }
    },
  },
  {
    label: 'Table',
    icon: 'grid',
    onClick() {
      currentView.value = {
        label: 'Table',
        icon: 'grid',
      }
    },
  },
  {
    label: 'Calender',
    icon: 'calendar',
    onClick() {
      currentView.value = {
        label: 'Calender',
        icon: 'calendar',
      }
    },
  },
  {
    label: 'Board',
    icon: 'columns',
    onClick() {
      currentView.value = {
        label: 'Board',
        icon: 'columns',
      }
    },
  },
]

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}
</script>
