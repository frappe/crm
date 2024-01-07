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
  <ViewControls
    v-model="organizations"
    v-model:loadMore="loadMore"
    doctype="CRM Organization"
  />
  <OrganizationsListView
    v-if="organizations.data && rows.length"
    v-model="organizations.data.page_length_count"
    :rows="rows"
    :columns="organizations.data.columns"
    :options="{
      rowCount: organizations.data.row_count,
      totalCount: organizations.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div
    v-else-if="organizations.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <OrganizationsIcon class="h-10 w-10" />
      <span>No Organizations Found</span>
      <Button label="Create" @click="showOrganizationModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <OrganizationModal v-model="showOrganizationModal" :organization="{}" />
</template>
<script setup>
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { Breadcrumbs } from 'frappe-ui'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
} from '@/utils'
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const showOrganizationModal = ref(false)

const currentOrganization = computed(() => {
  return organizations.value?.data?.data?.find(
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

// organizations data is loaded in the ViewControls component
const organizations = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!organizations.value?.data?.data) return []
  return organizations.value?.data.data.map((organization) => {
    let _rows = {}
    organizations.value?.data.rows.forEach((row) => {
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

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}
</script>
