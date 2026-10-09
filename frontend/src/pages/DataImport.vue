<template>
  <DataImport
    :doctype="route.params.doctype"
    :importName="route.params.importName"
    :doctypeMap="doctypeMap"
  />
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import { DataImport } from 'frappe-ui/frappe'
import { useRoute } from 'vue-router'
import { getSettings } from '@/stores/settings'

const route = useRoute()
const { brand } = getSettings()

const doctypeMap = {
  'CRM Lead': {
    title: 'Leads',
    listRoute: '/crm/leads',
    pageRoute: `/crm/leads/docname`,
  },
  'CRM Deal': {
    title: 'Deals',
    listRoute: '/crm/deals',
    pageRoute: `/crm/deals/docname`,
  },
  Contact: {
    title: 'Contacts',
    listRoute: '/crm/contacts',
    pageRoute: `/crm/contacts/docname`,
  },
  'CRM Task': {
    title: 'Tasks',
    listRoute: '/crm/tasks',
  },
  'CRM Organization': {
    title: 'Organizations',
    listRoute: '/crm/organizations',
    pageRoute: `/crm/organizations/docname`,
  },
  'CRM Call Log': {
    title: 'Call Log',
    listRoute: '/crm/call-logs',
  },
}

usePageMeta(() => {
  return {
    title: __('Data Import'),
    icon: brand.favicon,
  }
})
</script>
