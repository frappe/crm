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
      <ViewSettings doctype="CRM Deal" v-model="deals"/>
    </div>
  </div>
  <DealsListView v-if="deals.data" :rows="rows" :columns="deals.data.columns" />
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
import ViewSettings from '@/components/ViewSettings.vue'
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

function getParams() {
  const filters = getArgs() || {}
  const order_by = getOrderBy() || 'modified desc'

  return {
    doctype: 'CRM Deal',
    filters: filters,
    order_by: order_by,
  }
}

const deals = createResource({
  url: 'crm.api.doc.get_list_data',
  params: getParams(),
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    deals.params = getParams()
    deals.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    deals.params = getParams()
    deals.reload()
  }, 300),
  { deep: true }
)

const rows = computed(() => {
  if (!deals.data?.data) return []
  return deals.data.data.map((deal) => {
    let _rows = {}
    deals.data.rows.forEach((row) => {
      _rows[row] = deal[row]

      if (row == 'organization') {
        _rows[row] = {
          label: deal.organization,
          logo: getOrganization(deal.organization)?.organization_logo,
        }
      } else if (row == 'annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(deal.annual_revenue)
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: dealStatuses[deal.status]?.color,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == 'modified') {
        _rows[row] = {
          label: dateFormat(deal.modified, dateTooltipFormat),
          timeAgo: timeAgo(deal.modified),
        }
      } else if (row == 'creation') {
        _rows[row] = {
          label: dateFormat(deal.creation, dateTooltipFormat),
          timeAgo: timeAgo(deal.creation),
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
