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
    <template #left-subheader>
      <Dropdown :options="viewsDropdownOptions">
        <template #default="{ open }">
          <Button :label="currentView.label">
            <template #prefix
              ><FeatherIcon :name="currentView.icon" class="h-4"
            /></template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
    </template>
    <template #right-subheader>
      <Filter doctype="CRM Lead" />
      <SortBy doctype="CRM Lead" />
      <Button icon="more-horizontal" />
    </template>
  </LayoutHeader>
  <ListView :list="list" :columns="columns" :rows="rows" row-key="name" />
  <Dialog
    v-model="showNewDialog"
    :options="{
      size: '3xl',
      title: 'New Lead',
      actions: [{ label: 'Save', variant: 'solid' }],
    }"
  >
    <template #body-content>
      <NewLead :newLead="newLead" />
    </template>
    <template #actions="{ close }">
      <div class="flex flex-row-reverse gap-2">
        <Button variant="solid" label="Save" @click="createNewLead(close)" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ListView from '@/components/ListView.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import NewLead from '@/components/NewLead.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import { usersStore } from '@/stores/users'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
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
  title: 'Leads',
  plural_label: 'Leads',
  singular_label: 'Lead',
}
const { getUser } = usersStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const currentView = ref({
  label: 'List',
  icon: 'list',
})

const leads = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  fields: [
    'name',
    'first_name',
    'lead_name',
    'image',
    'organization_name',
    'organization_logo',
    'status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  filters: getArgs() || {},
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
    leads.filters = getArgs() || {}
    leads.reload()
  }, 300),
  { deep: true }
)

const columns = [
  {
    label: 'Name',
    key: 'lead_name',
    type: 'avatar',
    size: 'w-44',
  },
  {
    label: 'Organization',
    key: 'organization_name',
    type: 'logo',
    size: 'w-44',
  },
  {
    label: 'Status',
    key: 'status',
    type: 'indicator',
    size: 'w-44',
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
    size: 'w-44',
  },
  {
    label: 'Lead owner',
    key: 'lead_owner',
    type: 'avatar',
    size: 'w-44',
  },
]

const rows = computed(() => {
  return leads.data?.map((lead) => {
    return {
      name: lead.name,
      lead_name: {
        label: lead.lead_name,
        image: lead.image,
        image_label: lead.first_name,
      },
      organization_name: {
        label: lead.organization_name,
        logo: lead.organization_logo,
      },
      status: {
        label: lead.status,
        color: indicatorColor[lead.status],
      },
      email: lead.email,
      mobile_no: lead.mobile_no,
      lead_owner: lead.lead_owner && getUser(lead.lead_owner),
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

const indicatorColor = {
  New: 'text-gray-600',
  'Contact made': 'text-orange-500',
  'Proposal made': 'text-blue-600',
  Negotiation: 'text-red-600',
  Converted: 'text-green-600',
}

const showNewDialog = ref(false)

let newLead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  lead_name: '',
  organization_name: '',
  status: 'New',
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

function createNewLead(close) {
  createLead
    .submit(newLead, {
      validate() {
        if (!newLead.first_name) {
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
