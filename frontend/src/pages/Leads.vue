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
            <template #prefix
              ><FeatherIcon :name="currentView.icon" class="h-4"
            /></template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
            /></template>
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
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({ name: 'Lead', params: { leadId: row.name } }),
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" />
    <ListRows>
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <ListRowItem :item="item">
          <template #prefix>
            <div v-if="column.key === 'status'">
              <IndicatorIcon :class="item.color" />
            </div>
            <div v-else-if="column.key === 'lead_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.image"
                :label="item.image_label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'organization_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.logo"
                :label="item.label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'lead_owner'">
              <Avatar
                v-if="item.full_name"
                class="flex items-center"
                :image="item.user_image"
                :label="item.full_name"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'mobile_no'">
              <PhoneIcon class="h-4 w-4" />
            </div>
          </template>
          <div v-if="column.key === 'modified'" class="truncate text-base">
            {{ item.timeAgo }}
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner />
  </ListView>
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
import LayoutHeader from '@/components/LayoutHeader.vue'
import NewLead from '@/components/NewLead.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { usersStore } from '@/stores/users'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import { leadStatuses, dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import {
  Avatar,
  FeatherIcon,
  Dialog,
  Button,
  Dropdown,
  createListResource,
  createResource,
  Breadcrumbs,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
} from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, computed, reactive, watch } from 'vue'

const breadcrumbs = [{ label: 'Leads', route: { name: 'Leads' } }]

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
    is_deal: 0,
  }
}

function getSortBy() {
  return getOrderBy() || 'modified desc'
}

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
  filters: getFilter(),
  orderBy: getSortBy(),
  pageLength: 20,
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    leads.orderBy = getSortBy()
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
    label: 'Name',
    key: 'lead_name',
    width: '12rem',
  },
  {
    label: 'Organization',
    key: 'organization_name',
    width: '10rem',
  },
  {
    label: 'Status',
    key: 'status',
    width: '8rem',
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
    label: 'Lead owner',
    key: 'lead_owner',
    width: '10rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
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
        color: leadStatuses[lead.status]?.color,
      },
      email: lead.email,
      mobile_no: lead.mobile_no,
      lead_owner: {
        label: lead.lead_owner && getUser(lead.lead_owner).full_name,
        ...(lead.lead_owner && getUser(lead.lead_owner)),
      },
      modified: {
        label: dateFormat(lead.modified, dateTooltipFormat),
        timeAgo: timeAgo(lead.modified),
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

let newLead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  lead_name: '',
  organization_name: '',
  status: 'Open',
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
