<template>
  <div class="flex min-h-0 flex-1 flex-col p-8 max-sm:p-0">
    <div
      v-if="step === 'email-add'"
      class="min-h-0 flex-1 overflow-y-auto max-sm:p-4"
    >
      <EmailAdd @update:step="updateStep" />
    </div>
    <div v-else-if="step === 'email-list'" class="flex min-h-0 flex-1 flex-col">
      <EmailAccountList @update:step="updateStep" />
    </div>
    <div
      v-else-if="step === 'email-edit'"
      class="min-h-0 flex-1 overflow-y-auto max-sm:p-4"
    >
      <EmailEdit :account-data="accountData" @update:step="updateStep" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import EmailAdd from './EmailAdd.vue'
import EmailAccountList from './EmailAccountList.vue'
import EmailEdit from './EmailEdit.vue'

const step = ref('email-list')
const accountData = ref(null)
function updateStep(newStep, data) {
  step.value = newStep
  accountData.value = data
}
</script>
