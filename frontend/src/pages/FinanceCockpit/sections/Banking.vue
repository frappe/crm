<template>
  <div class="fc-banking space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">Banking</h2>
    </div>

    <div class="flex gap-1 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        :class="[
          'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
          activeTab === tab.key
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300',
        ]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <BankAccounts v-if="activeTab === 'accounts'" />
    <BankTransactions v-else-if="activeTab === 'transactions'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BankAccounts from './banking/BankAccounts.vue'
import BankTransactions from './banking/BankTransactions.vue'

const TABS = [
  { key: 'accounts', label: 'Bank Accounts' },
  { key: 'transactions', label: 'Transactions' },
]

const activeTab = ref('accounts')
</script>
