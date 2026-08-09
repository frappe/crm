<template>
  <div class="fc-reports space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Reports</h2>
    </div>

    <div class="space-y-3">
      <div v-for="group in GROUPS" :key="group" class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- Accordion header -->
        <button
          class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
          @click="toggleGroup(group)"
        >
          <span class="font-medium text-sm text-gray-700 dark:text-gray-300">{{ GROUP_LABELS[group] }}</span>
          <div class="flex items-center gap-2">
            <span class="text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full">
              {{ visibleReportsForGroup(group).length }}
            </span>
            <!-- Chevron -->
            <svg
              :class="['transition-transform', openGroups.has(group) ? 'rotate-180' : '']"
              xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </button>

        <!-- Report list -->
        <div v-if="openGroups.has(group)" class="divide-y divide-gray-100 dark:divide-gray-700">
          <div
            v-for="report in visibleReportsForGroup(group)"
            :key="report.report"
            class="px-4 py-2.5 flex items-center justify-between gap-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <span class="text-sm text-gray-700 dark:text-gray-300 truncate">{{ report.label }}</span>
              <span
                :class="[
                  'text-xs px-1.5 py-0.5 rounded flex-shrink-0',
                  report.source === 'crm'
                    ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
                ]"
              >{{ report.source === 'crm' ? 'CRM' : 'ERPNext' }}</span>
            </div>
            <a
              :href="buildUrl(report)"
              target="_blank"
              rel="noopener"
              class="flex-shrink-0 p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title="Open report"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round"
                class="text-gray-400 dark:text-gray-500"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" x2="21" y1="14" y2="3"/>
              </svg>
            </a>
          </div>
          <div v-if="!visibleReportsForGroup(group).length" class="px-4 py-3 text-xs text-gray-400">
            No reports available for your role in this group.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { REPORTS, GROUPS, GROUP_LABELS } from '../constants/reportsConfig.js'
import { useCompanyContext } from '../composables/useCompanyContext.js'
import { useBoot } from '../composables/useBoot.js'

const { company } = useCompanyContext()
const { getRoles, isAdministrator } = useBoot()

const userRoles = getRoles()
const today = new Date().toISOString().slice(0, 10)

const openGroups = ref(new Set(GROUPS))

function toggleGroup(group) {
  if (openGroups.value.has(group)) {
    openGroups.value.delete(group)
  } else {
    openGroups.value.add(group)
  }
}

const isAdmin = userRoles.includes('System Manager') || isAdministrator()

function visibleReportsForGroup(group) {
  return REPORTS.filter(r =>
    r.group === group &&
    (isAdmin || r.roles.some(role => userRoles.includes(role)))
  )
}

function buildUrl(report) {
  const filters = {}
  for (const [k, v] of Object.entries(report.defaultFilters || {})) {
    if (v === '__COMPANY__') filters[k] = company.value || ''
    else if (v === '__TODAY__') filters[k] = today
    else filters[k] = v
  }
  const qs = new URLSearchParams(filters).toString()
  const base = '/app/query-report/' + encodeURIComponent(report.report)
  return qs ? base + '?' + qs : base
}
</script>
