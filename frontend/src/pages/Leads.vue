<template>
  <ListView :title="title" :columns="columns" :rows="rows" row-key="name" />
</template>

<script setup>
import ListView from '../components/ListView.vue'
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import { usersStore } from '../stores/users'

const title = 'Lead'
const { getUser } = usersStore()

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
  orderBy: 'modified desc',
  cache: 'Leads',
  pageLength: 999,
  auto: true,
})
leads.fetch()

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

const indicatorColor = {
  New: 'text-gray-600',
  'Contact made': 'text-orange-500',
  'Proposal made': 'text-blue-600',
  Negotiation: 'text-red-600',
  Converted: 'text-green-600',
}
</script>
