<template>
  <div class="fc-partner-commission space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Partner &amp; Commission</h2>
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

    <RebateVouchers v-if="activeTab === 'rebates'" />
    <SalesCommissions v-else-if="activeTab === 'commissions'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RebateVouchers from './partner/RebateVouchers.vue'
import SalesCommissions from './partner/SalesCommissions.vue'

const TABS = [
  { key: 'rebates', label: 'Rebate Vouchers' },
  { key: 'commissions', label: 'Sales Commissions' },
]

const activeTab = ref('rebates')
</script>
