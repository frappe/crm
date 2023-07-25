<template>
  <ListView :title="title" :columns="columns" :rows="rows" />
</template>

<script setup>
import ListView from '../components/ListView.vue'
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'

const title = 'Leads'

const leads = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  fields: [
    'name',
    'first_name',
    'last_name',
    'organization_name',
    'status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  orderBy: 'modified asc',
  cache: 'Leads',
  pageLength: 999,
  auto: true,
})
leads.fetch()

const columns = [
  {
    label: 'Full name',
    key: 'full_name',
    size: 'w-44',
  },
  {
    label: 'Organization',
    key: 'organization_name',
    size: 'w-44',
  },
  {
    label: 'Status',
    key: 'status',
    size: 'w-44',
  },
  {
    label: 'Email',
    key: 'email',
    size: 'w-44',
  },
  {
    label: 'Mobile no',
    key: 'mobile_no',
    size: 'w-44',
  },
  {
    label: 'Lead owner',
    key: 'lead_owner',
    size: 'w-44',
  },
]

const rows = computed(() => {
  return leads.data?.map((lead) => {
    return {
      full_name: lead.first_name + ' ' + lead.last_name,
      organization_name: lead.organization_name,
      status: lead.status,
      email: lead.email,
      mobile_no: lead.mobile_no,
      lead_owner: lead.lead_owner,
    }
  })
})
</script>
