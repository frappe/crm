<template>
  <SettingsPage
    doctype="CRM Twilio Settings"
    :title="__('Twilio Settings')"
    :successMessage="__('Twilio Settings Updated')"
    class="p-8"
    :back="() => emit('updateStep', 'telephony-settings')"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
const emit = defineEmits(['updateStep'])
</script>
