<template>
  <div class="fc-expenses space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Expenses</h2>
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

    <ExpenseClaims v-if="activeTab === 'claims'" />
    <EmployeeAdvances v-else-if="activeTab === 'advances'" />
    <ExpenseJournals v-else-if="activeTab === 'journals'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ExpenseClaims from './expenses/ExpenseClaims.vue'
import EmployeeAdvances from './expenses/EmployeeAdvances.vue'
import ExpenseJournals from './expenses/ExpenseJournals.vue'

const TABS = [
  { key: 'claims', label: 'Expense Claims' },
  { key: 'advances', label: 'Employee Advances' },
  { key: 'journals', label: 'Expense Journals' },
]

const activeTab = ref('claims')
</script>
