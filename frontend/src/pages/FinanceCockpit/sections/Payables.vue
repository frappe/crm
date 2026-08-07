<template>
  <div class="fc-payables space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">Payables</h2>
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
    <ApInvoices v-if="activeTab === 'invoices'" />
    <PurchaseOrders v-else-if="activeTab === 'orders'" />
    <SupplierPayments v-else-if="activeTab === 'payments'" />
    <Suppliers v-else-if="activeTab === 'suppliers'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ApInvoices from './payables/ApInvoices.vue'
import PurchaseOrders from './payables/PurchaseOrders.vue'
import SupplierPayments from './payables/SupplierPayments.vue'
import Suppliers from './payables/Suppliers.vue'

const TABS = [
  { key: 'invoices', label: 'AP Invoices' },
  { key: 'orders', label: 'Purchase Orders' },
  { key: 'payments', label: 'Payments' },
  { key: 'suppliers', label: 'Suppliers' },
]

const activeTab = ref('invoices')
</script>
