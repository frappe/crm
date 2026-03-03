<template>
  <SettingsPage
    doctype="Helpdesk CRM Settings"
    :title="__('Helpdesk Settings')"
    :successMessage="__('Helpdesk Settings Updated')"
    class="p-8"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
</script>
