<template>
  <SettingsPage
    doctype="CRM Exotel Settings"
    :title="__('Exotel Settings')"
    :successMessage="__('Exotel Settings Updated')"
    class="p-8"
    :back="() => emit('updateStep', 'telephony-settings')"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
const emit = defineEmits(['updateStep'])
</script>
