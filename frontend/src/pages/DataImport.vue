<template>
  <DataImportListPage
    v-if="route.name === 'DataImportList'"
    :key="route.fullPath"
  />
  <DataImportWizardPage v-else />
</template>

<script setup>
import DataImportListPage from '@/components/DataImport/DataImportListPage.vue'
import DataImportWizardPage from '@/components/DataImport/DataImportWizardPage.vue'
import { usePageMeta } from 'frappe-ui'
import { useRoute } from 'vue-router'

const route = useRoute()

usePageMeta(() => {
  return {
    title: __('Data Import'),
  }
})
</script>
