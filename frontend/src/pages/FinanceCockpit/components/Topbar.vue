<template>
  <div class="fc-topbar flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
    <div class="flex items-center gap-3">
      <button
        v-if="isMobile"
        class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
        aria-label="Toggle sidebar"
        @click="$emit('toggle-sidebar')"
      >
        <!-- Menu icon via inline svg (lucide menu) -->
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
      </button>
      <span class="font-semibold text-base text-gray-900 dark:text-gray-100">Finance Cockpit</span>
    </div>
    <div class="flex items-center gap-2">
      <select
        v-if="companiesResource && companiesResource.data && companiesResource.data.length > 0"
        :value="company"
        class="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        @change="setCompany($event.target.value)"
      >
        <option v-for="c in companiesResource.data" :key="c.name" :value="c.name">
          {{ c.abbr || c.name }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { useCompanyContext } from '../composables/useCompanyContext.js'
import { useBreakpoint } from '../composables/useBreakpoint.js'

const { company, setCompany, companiesResource } = useCompanyContext()
const { isMobile } = useBreakpoint()

defineEmits(['toggle-sidebar'])
</script>
