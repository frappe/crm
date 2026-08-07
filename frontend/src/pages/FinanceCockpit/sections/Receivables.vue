<template>
  <div class="fc-receivables space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Receivables</h2>
    </div>

    <!-- Sub-tab nav -->
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

    <!-- Tab panels -->
    <ArInvoices v-if="activeTab === 'invoices'" />
    <SalesOrders v-else-if="activeTab === 'orders'" />
    <CustomerPayments v-else-if="activeTab === 'payments'" />
    <Customers v-else-if="activeTab === 'customers'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ArInvoices from './receivables/ArInvoices.vue'
import SalesOrders from './receivables/SalesOrders.vue'
import CustomerPayments from './receivables/CustomerPayments.vue'
import Customers from './receivables/Customers.vue'

const TABS = [
  { key: 'invoices', label: 'AR Invoices' },
  { key: 'orders', label: 'Sales Orders' },
  { key: 'payments', label: 'Payments' },
  { key: 'customers', label: 'Customers' },
]

const activeTab = ref('invoices')
</script>
