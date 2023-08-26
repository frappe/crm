<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showNewDialog = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex justify-between items-center px-5 pb-2.5 border-b">
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
                class="h-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>
    <div class="flex items-center gap-2">
      <Filter doctype="CRM Lead" />
      <SortBy doctype="CRM Lead" />
      <Button icon="more-horizontal" />
    </div>
  </div>
  <ListView :list="list" :columns="columns" :rows="rows" row-key="name" />
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
import ListView from '@/components/ListView.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import NewDeal from '@/components/NewDeal.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import { usersStore } from '@/stores/users'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import { dealStatuses } from '@/utils'
import {
  FeatherIcon,
  Dialog,
  Button,
  Dropdown,
  createListResource,
  createResource,
} from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, computed, reactive, watch } from 'vue'

const list = {
  title: 'Deals',
  plural_label: 'Deals',
  singular_label: 'Deal',
}
const { getUser } = usersStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const currentView = ref({
  label: 'List',
  icon: 'list',
})

function getFilter() {
  return {
    ...(getArgs() || {}),
    is_deal: 1,
  }
}

const leads = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  fields: [
    'name',
    'organization_name',
    'organization_logo',
    'annual_revenue',
    'deal_status',
    'email',
    'mobile_no',
    'lead_owner',
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
    leads.orderBy = getOrderBy() || 'modified desc'
    leads.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    leads.filters = getFilter()
    leads.reload()
  }, 300),
  { deep: true }
)

const columns = [
  {
    label: 'Organization',
    key: 'organization_name',
    type: 'logo',
    size: 'w-48',
  },
  {
    label: 'Amount',
    key: 'annual_revenue',
    type: 'data',
    size: 'w-24',
  },
  {
    label: 'Status',
    key: 'deal_status',
    type: 'indicator',
    size: 'w-36',
  },
  {
    label: 'Email',
    key: 'email',
    type: 'email',
    size: 'w-44',
  },
  {
    label: 'Mobile no',
    key: 'mobile_no',
    type: 'phone',
    size: 'w-32',
  },
  {
    label: 'Lead owner',
    key: 'lead_owner',
    type: 'avatar',
    size: 'w-36',
  },
  {
    label: 'Last modified',
    key: 'modified',
    type: 'pretty_date',
    size: 'w-28',
  },
]

const rows = computed(() => {
  return leads.data?.map((lead) => {
    return {
      name: lead.name,
      organization_name: {
        label: lead.organization_name,
        logo: lead.organization_logo,
      },
      annual_revenue: lead.annual_revenue,
      deal_status: {
        label: lead.deal_status,
        color: dealStatuses[lead.deal_status]?.color,
      },
      email: lead.email,
      mobile_no: lead.mobile_no,
      lead_owner: lead.lead_owner && getUser(lead.lead_owner),
      modified: lead.modified,
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
  salutation: '',
  first_name: '',
  last_name: '',
  lead_name: '',
  organization_name: '',
  deal_status: 'Qualification',
  email: '',
  mobile_no: '',
  lead_owner: getUser().email,
})

const createLead = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'CRM Lead',
        ...values,
      },
    }
  },
})

const router = useRouter()

function createNewDeal(close) {
  createLead
    .submit(newDeal, {
      validate() {
        if (!newDeal.first_name) {
          return 'First name is required'
        }
      },
      onSuccess(data) {
        router.push({
          name: 'Lead',
          params: {
            leadId: data.name,
          },
        })
      },
    })
    .then(close)
}
</script>
