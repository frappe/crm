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
  <ViewControls
    v-model="leads"
    v-model:loadMore="loadMore"
    doctype="CRM Lead"
    :filters="{ converted: 0 }"
  />
  <LeadsListView
    v-if="leads.data && rows.length"
    v-model="leads.data.page_length_count"
    :rows="rows"
    :columns="leads.data.columns"
    :options="{
      rowCount: leads.data.row_count,
      totalCount: leads.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div v-else-if="leads.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <LeadsIcon class="h-10 w-10" />
      <span>No Leads Found</span>
      <Button label="Create" @click="showNewDialog = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
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
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import NewLead from '@/components/NewLead.vue'
import ViewControls from '@/components/ViewControls.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { dateFormat, dateTooltipFormat, timeAgo, formatTime } from '@/utils'
import { createResource, Breadcrumbs } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, computed, reactive } from 'vue'

const breadcrumbs = [{ label: 'Leads', route: { name: 'Leads' } }]

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getLeadStatus } = statusesStore()

const router = useRouter()

// leads data is loaded in the ViewControls component
const leads = ref({})
const loadMore = ref(1)

// Rows
const rows = computed(() => {
  if (!leads.value?.data?.data) return []
  return leads.value?.data.data.map((lead) => {
    let _rows = {}
    leads.value?.data.rows.forEach((row) => {
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
      } else if (row == 'sla_status') {
        let value = lead.sla_status
        let tooltipText = value
        let color =
          lead.sla_status == 'Failed'
            ? 'red'
            : lead.sla_status == 'Fulfilled'
            ? 'green'
            : 'orange'
        if (value == 'First Response Due') {
          value = timeAgo(lead.response_by)
          tooltipText = dateFormat(lead.response_by, dateTooltipFormat)
          if (new Date(lead.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'lead_owner') {
        _rows[row] = {
          label: lead.lead_owner && getUser(lead.lead_owner).full_name,
          ...(lead.lead_owner && getUser(lead.lead_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(lead._assign) || []
        if (!assignees.length && lead.lead_owner) {
          assignees = [lead.lead_owner]
        }
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(lead[row], dateTooltipFormat),
          timeAgo: timeAgo(lead[row]),
        }
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: lead[field] ? dateFormat(lead[field], dateTooltipFormat) : '',
          timeAgo: lead[row]
            ? row == 'first_response_time'
              ? formatTime(lead[row])
              : timeAgo(lead[row])
            : '',
        }
      }
    })
    return _rows
  })
})

// New Lead
const showNewDialog = ref(false)

let newLead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  lead_name: '',
  organization: '',
  status: '',
  email: '',
  mobile_no: '',
  lead_owner: '',
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
