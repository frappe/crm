<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showNewDialog = true">
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
      <Filter doctype="CRM Deal" />
      <SortBy doctype="CRM Deal" />
      <Button icon="more-horizontal" />
    </div>
  </div>
  <DealsListView :rows="rows" :columns="columns" />
  <Dialog
    v-model="showNewDialog"
    :options="{
      size: '3xl',
      title: 'New Deal',
      actions: [{ label: 'Save', variant: 'solid' }],
    }"
  >
    <template #body-content>
      <NewDeal :newDeal="newDeal" />
    </template>
    <template #actions="{ close }">
      <div class="flex flex-row-reverse gap-2">
        <Button variant="solid" label="Save" @click="createNewDeal(close)" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import NewDeal from '@/components/NewDeal.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import {
  dealStatuses,
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
} from '@/utils'
import {
  FeatherIcon,
  Dialog,
  Button,
  Dropdown,
  createListResource,
  createResource,
  Breadcrumbs,
} from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, computed, reactive, watch } from 'vue'

const breadcrumbs = [{ label: 'Deals', route: { name: 'Deals' } }]

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const currentView = ref({
  label: 'List',
  icon: 'list',
})

function getFilter() {
  return getArgs() || {}
}

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  fields: [
    'name',
    'organization',
    'annual_revenue',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: getFilter(),
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    deals.orderBy = getOrderBy() || 'modified desc'
    deals.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    deals.filters = getFilter()
    deals.reload()
  }, 300),
  { deep: true }
)

const columns = [
  {
    label: 'Organization',
    key: 'organization',
    width: '11rem',
  },
  {
    label: 'Amount',
    key: 'annual_revenue',
    width: '9rem',
  },
  {
    label: 'Status',
    key: 'status',
    width: '10rem',
  },
  {
    label: 'Email',
    key: 'email',
    width: '12rem',
  },
  {
    label: 'Mobile no',
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: 'Deal owner',
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

const rows = computed(() => {
  if (!deals.data) return []
  return deals.data.map((deal) => {
    return {
      name: deal.name,
      organization: {
        label: deal.organization,
        logo: getOrganization(deal.organization)?.organization_logo,
      },
      annual_revenue: formatNumberIntoCurrency(deal.annual_revenue),
      status: {
        label: deal.status,
        color: dealStatuses[deal.status]?.color,
      },
      email: deal.email,
      mobile_no: deal.mobile_no,
      deal_owner: {
        label: deal.deal_owner && getUser(deal.deal_owner).full_name,
        ...(deal.deal_owner && getUser(deal.deal_owner)),
      },
      modified: {
        label: dateFormat(deal.modified, dateTooltipFormat),
        timeAgo: timeAgo(deal.modified),
      },
    }
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

const showNewDialog = ref(false)

let newDeal = reactive({
  organization: '',
  status: 'Qualification',
  email: '',
  mobile_no: '',
  deal_owner: getUser().email,
})

const createDeal = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'CRM Deal',
        ...values,
      },
    }
  },
})

const router = useRouter()

function createNewDeal(close) {
  createDeal
    .submit(newDeal, {
      validate() {
        if (!newDeal.first_name) {
          return 'First name is required'
        }
      },
      onSuccess(data) {
        router.push({
          name: 'Deal',
          params: {
            dealId: data.name,
          },
        })
      },
    })
    .then(close)
}
</script>
