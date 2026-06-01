<template>
  <!-- Edit a single WhatsApp Account (credentials, status, etc.) -->
  <SettingsPage
    v-if="step === 'account-edit'"
    doctype="WhatsApp Account"
    :name="accountName"
    :back="goHome"
    class="p-8"
  />
  <!-- Home: global WhatsApp Settings + the account manager, scrolled together -->
  <div v-else class="flex flex-col gap-8 p-8">
    <SettingsPage doctype="WhatsApp Settings" embedded />
    <div class="h-px border-t border-outline-gray-modals" />
    <WhatsAppAccountList @edit="editAccount" />
  </div>
</template>

<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
import WhatsAppAccountList from '@/components/Settings/WhatsAppAccountList.vue'
import { ref } from 'vue'

const step = ref('home')
const accountName = ref('')

function editAccount(name) {
  accountName.value = name
  step.value = 'account-edit'
}

function goHome() {
  step.value = 'home'
  accountName.value = ''
}
</script>
