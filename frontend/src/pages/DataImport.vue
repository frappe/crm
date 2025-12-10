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

const route = useRoute()

const doctypeMap = {
  'CRM Lead': {
    title: 'Leads',
    listRoute: '/leads',
    pageRoute: `/leads/docname`,
  },
  'CRM Deal': {
    title: 'Deals',
    listRoute: '/deals',
    pageRoute: `/deals/docname`,
  },
  Contact: {
    title: 'Contacts',
    listRoute: '/contacts',
    pageRoute: `/contacts/docname`,
  },
  'CRM Task': {
    title: 'Tasks',
    listRoute: '/tasks',
    pageRoute: `/tasks/docname`,
  },
  'CRM Organization': {
    title: 'Organizations',
    listRoute: '/organizations',
    pageRoute: `/organizations/docname`,
  },
}

usePageMeta(() => {
  return {
    title: __('Data Import'),
  }
})
</script>
