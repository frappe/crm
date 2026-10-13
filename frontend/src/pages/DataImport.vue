<template>
  <DataImportWizardPage />
</template>

<script setup>
import DataImportWizardPage from '@/components/DataImport/DataImportWizardPage.vue'
import { usePageMeta } from 'frappe-ui'
import { getSettings } from '@/stores/settings'

const { brand } = getSettings()

usePageMeta(() => {
  return {
    title: __('Data Import'),
    icon: brand.favicon,
  }
})
</script>
