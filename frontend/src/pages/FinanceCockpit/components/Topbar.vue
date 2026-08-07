<template>
  <div class="fc-topbar flex items-center justify-between px-4 h-10 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex-shrink-0">
    <!-- Mobile: hamburger -->
    <button
      v-if="isMobile"
      class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 mr-2"
      aria-label="Toggle sidebar"
      @click="$emit('toggle-sidebar')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
    </button>
    <div class="flex-1" />
    <!-- Company switcher -->
    <div class="flex items-center gap-2">
      <span class="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">Company</span>
      <select
        v-if="companiesResource && companiesResource.data && companiesResource.data.length > 0"
        :value="company"
        class="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
        @change="setCompany($event.target.value)"
      >
        <option v-for="c in companiesResource.data" :key="c.name" :value="c.name">
          {{ c.name }}
        </option>
      </select>
      <span v-else class="text-xs text-gray-400 italic">Loading…</span>
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
