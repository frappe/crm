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
      <ViewSettings doctype="CRM Lead" v-model="leads" />
    </div>
  </div>
  <LeadsListView v-if="leads.data" :rows="rows" :columns="leads.data.columns" />
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
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import NewLead from '@/components/NewLead.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import ViewSettings from '@/components/ViewSettings.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
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

const breadcrumbs = [{ label: 'Leads', route: { name: 'Leads' } }]

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getLeadStatus } = statusesStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const currentView = ref({
  label: 'List',
  icon: 'list',
})

function getParams() {
  const filters = {
    converted: 0,
    ...(getArgs() || {}),
  }

  const order_by = getOrderBy() || 'modified desc'

  return {
    doctype: 'CRM Lead',
    filters: filters,
    order_by: order_by,
  }
}

const leads = createResource({
  url: 'crm.api.doc.get_list_data',
  params: getParams(),
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    leads.params = getParams()
    leads.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    leads.params = getParams()
    leads.reload()
  }, 300),
  { deep: true }
)

const rows = computed(() => {
  if (!leads.data?.data) return []
  return leads.data.data.map((lead) => {
    let _rows = {}
    leads.data.rows.forEach((row) => {
      _rows[row] = lead[row]

      if (row == 'lead_name') {
        _rows[row] = {
          label: lead.lead_name,
          image: lead.image,
          image_label: lead.first_name,
        }
      } else if (row == 'organization') {
        _rows[row] = {
          label: lead.organization,
          logo: getOrganization(lead.organization)?.organization_logo,
        }
      } else if (row == 'status') {
        _rows[row] = {
          label: lead.status,
          color: getLeadStatus(lead.status)?.iconColorClass,
        }
      } else if (row == 'lead_owner') {
        _rows[row] = {
          label: lead.lead_owner && getUser(lead.lead_owner).full_name,
          ...(lead.lead_owner && getUser(lead.lead_owner)),
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(lead[row], dateTooltipFormat),
          timeAgo: timeAgo(lead[row]),
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

let newLead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  lead_name: '',
  organization: '',
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
