<template>
  <div class="fc-kpi-strip">
    <!-- Period selector + refresh — top right -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Overview</h2>
      <div class="flex items-center gap-2">
        <PeriodSelector :model-value="period" @update:modelValue="onPeriodChange" />
        <button
          class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors"
          title="Refresh"
          :disabled="kpisResource.loading"
          @click="refresh"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M8 16H3v5"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="kpisResource.loading" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="n in 8" :key="n" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 h-28 animate-pulse" />
    </div>

    <!-- Error state -->
    <div v-else-if="kpisResource.error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3 text-sm text-red-600 dark:text-red-400 flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
      Failed to load KPIs.
      <button class="underline font-medium ml-1" @click="refresh">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!visibleTiles.length" class="text-sm text-gray-400 py-8 text-center">
      No KPI data available for this role.
    </div>

    <!-- Tiles -->
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <KpiTile
        v-for="tile in visibleTiles"
        :key="tile.key"
        :label="tile.label"
        :value="tile.data.value"
        :currency="tile.data.currency"
        :delta-pct="tile.data.delta_pct"
        :delta-direction="tile.data.delta_direction"
        :icon-svg="tile.iconSvg"
        :tone="tile.tone"
        @click="$emit('navigate', tile.section)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import KpiTile from './KpiTile.vue'
import PeriodSelector from './PeriodSelector.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const props = defineProps({
  userRoles: { type: Array, default: () => [] },
})
const emit = defineEmits(['navigate', 'update:period'])

const { company } = useCompanyContext()
const LS_PERIOD_KEY = 'fc_period'
const period = ref(localStorage.getItem(LS_PERIOD_KEY) || 'month')

const kpisResource = createResource({
  url: 'crm.finance.api.get_finance_kpis',
  makeParams() {
    return { company: company.value, period: period.value }
  },
  auto: true,
})

function onPeriodChange(val) {
  period.value = val
  localStorage.setItem(LS_PERIOD_KEY, val)
  kpisResource.fetch()
  emit('update:period', val)
}

function refresh() {
  kpisResource.fetch({ force: 1 })
}

// Re-fetch when company changes
watch(company, () => { kpisResource.fetch() })

const ICON_SVGS = {
  ar: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/></svg>',
  ap: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
  payment: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V8"/><path d="m5 12-3-3 3-3"/><path d="m19 12 3-3-3-3"/></svg>',
  rebate: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
}

// tone maps each KPI to a finance meaning (see KpiTile TONES): outstanding
// balances = neutral, cash-in = positive, overdue = attention, in-flight/obligations
// = pending. (No `info`/blue tone — this fork rebrands blue to Tiberbu red.)
const ALL_TILES = [
  { key: 'ar_outstanding',     label: 'AR Outstanding',      section: 'receivables',        tone: 'neutral',   roles: ['Finance Manager', 'AR Accountant'],              iconSvg: ICON_SVGS.ar },
  { key: 'ar_overdue',         label: 'AR Overdue',          section: 'receivables',        tone: 'attention', roles: ['Finance Manager', 'AR Accountant'],              iconSvg: ICON_SVGS.ar },
  { key: 'invoiced_mtd',       label: 'Invoiced MTD',        section: 'receivables',        tone: 'pending',   roles: ['Finance Manager', 'AR Accountant'],              iconSvg: ICON_SVGS.payment },
  { key: 'collected_mtd',      label: 'Collected MTD',       section: 'receivables',        tone: 'positive',  roles: ['Finance Manager', 'AR Accountant'],              iconSvg: ICON_SVGS.payment },
  { key: 'ap_outstanding',     label: 'AP Outstanding',      section: 'payables',           tone: 'pending',   roles: ['Finance Manager', 'AP Accountant'],              iconSvg: ICON_SVGS.ap },
  { key: 'ap_overdue',         label: 'AP Overdue',          section: 'payables',           tone: 'attention', roles: ['Finance Manager', 'AP Accountant'],              iconSvg: ICON_SVGS.ap },
  { key: 'pending_rebates',    label: 'Pending Rebates',     section: 'partner_commission', tone: 'pending',   roles: ['Finance Manager', 'AR Accountant', 'Partner RM'], iconSvg: ICON_SVGS.rebate },
  { key: 'unpaid_commissions', label: 'Unpaid Commissions',  section: 'partner_commission', tone: 'pending',   roles: ['Finance Manager', 'Sales Manager'],              iconSvg: ICON_SVGS.rebate },
]

const visibleTiles = computed(() => {
  const data = kpisResource.data || {}
  // Drive visibility from API response: the server already role-scopes the payload.
  // A tile is shown iff its key is present in the response (absent = no access for this role).
  // The frontend roles list is used only as a secondary label hint, not for gating.
  return ALL_TILES
    .filter(t => t.key in data)
    .map(t => ({ ...t, data: data[t.key] }))
})
</script>
