<template>
  <SettingsPage
    doctype="ERPNext CRM Settings"
    :title="__('ERPNext Settings')"
    :successMessage="__('ERPNext Settings Updated')"
    class="p-8"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
</script>
