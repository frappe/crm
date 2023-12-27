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
      <ViewSettings doctype="CRM Deal" v-model="deals" />
    </div>
  </div>
  <DealsListView
    v-if="deals.data && rows.length"
    :rows="rows"
    :columns="deals.data.columns"
  />
  <div v-else-if="deals.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <DealsIcon class="h-10 w-10" />
      <span>No Deals Found</span>
      <Button label="Create" @click="showNewDialog = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
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
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import NewDeal from '@/components/NewDeal.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import ViewSettings from '@/components/ViewSettings.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  formatTime,
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
const { getDealStatus } = statusesStore()
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

      let org = getOrganization(deal.organization)

      if (row == 'organization') {
        _rows[row] = {
          label: deal.organization,
          logo: org?.organization_logo,
        }
      } else if (row == 'annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(org?.annual_revenue)
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: getDealStatus(deal.status)?.iconColorClass,
        }
      } else if (row == 'sla_status') {
        let value = deal.sla_status
        let tooltipText = value
        let color =
          deal.sla_status == 'Failed'
            ? 'red'
            : deal.sla_status == 'Fulfilled'
            ? 'green'
            : 'orange'
        if (value == 'First Response Due') {
          value = timeAgo(deal.response_by)
          tooltipText = dateFormat(deal.response_by, dateTooltipFormat)
          if (new Date(deal.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(deal._assign) || []
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(deal[row], dateTooltipFormat),
          timeAgo: timeAgo(deal[row]),
        }
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: deal[field] ? dateFormat(deal[field], dateTooltipFormat) : '',
          timeAgo: deal[row]
            ? row == 'first_response_time'
              ? formatTime(deal[row])
              : timeAgo(deal[row])
            : '',
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
  status: '',
  email: '',
  mobile_no: '',
  deal_owner: '',
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
