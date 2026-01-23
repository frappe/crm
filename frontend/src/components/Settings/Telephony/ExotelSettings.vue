<template>
  <SettingsPage
    doctype="CRM Exotel Settings"
    :title="__('Exotel settings')"
    :successMessage="__('Exotel settings updated')"
    class="p-8"
    :back="() => $emit('updateStep', 'telephony-settings')"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
</script>
