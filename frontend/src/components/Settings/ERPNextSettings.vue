<template>
  <SettingsPage
    doctype="ERPNext CRM Settings"
    :title="__('ERPNext settings')"
    :successMessage="__('ERPNext settings updated')"
    class="p-8"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
</script>