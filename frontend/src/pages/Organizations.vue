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
      <Button icon="more-horizontal" />
    </div>
  </div>
  <OrganizationsListView :rows="rows" :columns="columns" />
  <OrganizationModal
    v-model="showOrganizationModal"
    :organization="{}"
  />
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import { FeatherIcon, Breadcrumbs, Dropdown } from 'frappe-ui'
import { organizationsStore } from '@/stores/organizations.js'
import { dateFormat, dateTooltipFormat, timeAgo, formatNumberIntoCurrency } from '@/utils'
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const { organizations } = organizationsStore()
const route = useRoute()

const showOrganizationModal = ref(false)

const currentOrganization = computed(() => {
  return organizations.data.find(
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

const rows = computed(() => {
  return organizations.data.map((organization) => {
    return {
      name: organization.name,
      organization: {
        label: organization.organization_name,
        logo: organization.organization_logo,
      },
      website: website(organization.website),
      industry: organization.industry,
      annual_revenue: formatNumberIntoCurrency(organization.annual_revenue),
      modified: {
        label: dateFormat(organization.modified, dateTooltipFormat),
        timeAgo: timeAgo(organization.modified),
      },
    }
  })
})

const columns = [
  {
    label: 'Organization',
    key: 'organization',
    width: '16rem',
  },
  {
    label: 'Website',
    key: 'website',
    width: '14rem',
  },
  {
    label: 'Industry',
    key: 'industry',
    width: '14rem',
  },
  {
    label: 'Annual Revenue',
    key: 'annual_revenue',
    width: '14rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}
</script>
