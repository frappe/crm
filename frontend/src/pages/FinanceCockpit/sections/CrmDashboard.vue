<template>
  <div class="crm-dashboard space-y-5">

    <!-- ── Period selector ── -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-semibold text-ink-gray-9">Overview</h2>
        <p class="text-xs text-ink-gray-5 mt-0.5">{{ periodLabel }} · {{ company }}</p>
      </div>
      <div class="flex items-center gap-1 p-1 rounded-lg bg-surface-gray-2">
        <button
          v-for="p in PERIODS"
          :key="p.value"
          class="px-3 py-1 text-xs font-medium rounded-md transition-all duration-150"
          :class="period === p.value
            ? 'bg-surface-white text-ink-gray-9 shadow-sm'
            : 'text-ink-gray-5 hover:text-ink-gray-8'"
          @click="setPeriod(p.value)"
        >{{ p.label }}</button>
      </div>
    </div>

    <!-- ── KPI tiles ── -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div
        v-for="tile in kpiTiles"
        :key="tile.key"
        class="fc-glass-card group cursor-pointer"
        @click="$emit('navigate', tile.section)"
      >
        <div class="flex items-start justify-between mb-3">
          <span class="text-xs font-medium text-ink-gray-5 leading-tight">{{ tile.label }}</span>
          <span
            class="w-8 h-8 -mt-0.5 flex-shrink-0 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105"
            :class="tile.tone.chip"
          >
            <span :class="[tile.iconClass, 'size-4']" aria-hidden="true" />
          </span>
        </div>
        <div v-if="loading" class="h-8 w-24 rounded-md bg-surface-gray-2 animate-pulse" />
        <div v-else class="text-2xl font-bold text-ink-gray-9 tabular-nums">{{ tile.formatted }}</div>
        <div class="mt-2 flex items-center gap-1 text-xs">
          <template v-if="!loading && tile.delta !== 0">
            <span :class="['size-3', tile.delta > 0 ? 'lucide-trending-up text-ink-green-6' : 'lucide-trending-down text-ink-red-6']" />
            <span :class="tile.delta > 0 ? 'text-ink-green-6' : 'text-ink-red-6'">{{ Math.abs(tile.delta) }}%</span>
            <span class="text-ink-gray-4">vs last period</span>
          </template>
          <span v-else class="text-ink-gray-4">—</span>
        </div>
      </div>
    </div>

    <!-- ── Pipeline bar ── -->
    <div class="fc-glass-card !p-0 overflow-hidden">
      <div class="px-5 pt-4 pb-3 border-b border-outline-gray-1/60">
        <h3 class="text-sm font-semibold text-ink-gray-8">Sales Pipeline</h3>
      </div>
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-4 divide-x divide-outline-gray-1/40">
        <div v-for="n in 4" :key="n" class="px-5 py-4 space-y-2">
          <div class="h-3 w-16 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-6 w-10 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-3 w-20 bg-surface-gray-2 rounded animate-pulse" />
        </div>
      </div>
      <div v-else class="grid grid-cols-2 sm:grid-cols-4 divide-x divide-outline-gray-1/40">
        <div
          v-for="stage in pipelineStages"
          :key="stage.key"
          class="px-5 py-4 cursor-pointer hover:bg-surface-gray-1/60 transition-colors group"
          @click="$emit('navigate', stage.section)"
        >
          <div class="flex items-center gap-1.5 mb-1.5">
            <span :class="[stage.dot, 'w-2 h-2 rounded-full flex-shrink-0']" />
            <span class="text-xs font-medium text-ink-gray-5 group-hover:text-ink-gray-7 transition-colors">{{ stage.label }}</span>
          </div>
          <p class="text-2xl font-bold text-ink-gray-9 tabular-nums">{{ stage.count }}</p>
          <p class="text-xs text-ink-gray-5 tabular-nums mt-0.5">{{ stage.amount }}</p>
        </div>
      </div>
    </div>

    <!-- ── Recent invoices ── -->
    <div class="fc-glass-card !p-0 overflow-hidden">
      <div class="px-5 pt-4 pb-3 border-b border-outline-gray-1/60 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-ink-gray-8">Recent Invoices</h3>
        <button
          class="text-xs font-medium text-ink-red-6 hover:text-ink-red-8 transition-colors"
          @click="$emit('navigate', 'invoices')"
        >View all →</button>
      </div>
      <div v-if="recentLoading" class="divide-y divide-outline-gray-1/40">
        <div v-for="n in 5" :key="n" class="flex items-center gap-4 px-5 py-3">
          <div class="h-3 w-28 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-3 flex-1 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-3 w-16 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-3 w-20 bg-surface-gray-2 rounded animate-pulse" />
          <div class="h-5 w-16 bg-surface-gray-2 rounded-full animate-pulse" />
        </div>
      </div>
      <div v-else-if="!recentInvoices.length" class="py-12 text-center text-sm text-ink-gray-4">
        No invoices yet.
      </div>
      <div v-else class="divide-y divide-outline-gray-1/40">
        <div
          v-for="inv in recentInvoices"
          :key="inv.name"
          class="flex items-center gap-4 px-5 py-3 hover:bg-surface-gray-1/60 cursor-pointer transition-colors"
          @click="$emit('navigate', 'invoices')"
        >
          <span class="w-32 font-mono text-xs font-semibold text-ink-gray-7 truncate flex-shrink-0">{{ inv.name }}</span>
          <span class="flex-1 text-sm text-ink-gray-6 truncate">{{ inv.customer }}</span>
          <span class="text-xs text-ink-gray-4 flex-shrink-0 w-24 text-right">{{ fmtDate(inv.posting_date) }}</span>
          <span class="text-sm font-semibold text-ink-gray-8 tabular-nums flex-shrink-0 w-28 text-right">{{ fmtCurrency(inv.outstanding_amount, inv.currency) }}</span>
          <span :class="[statusClass(inv.status), 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 w-24 justify-center']">
            {{ inv.status }}
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useCompanyContext } from '../composables/useCompanyContext.js'
import { useCurrency } from '../composables/useCurrency.js'

const emit = defineEmits(['navigate'])
const { company } = useCompanyContext()
const { formatCurrency } = useCurrency()

const PERIODS = [
  { label: 'Month',   value: 'month'   },
  { label: 'Quarter', value: 'quarter' },
  { label: 'Year',    value: 'year'    },
]
const periodLabel = computed(() => PERIODS.find(p => p.value === period.value)?.label || '')

const LS_KEY = 'fc_period'
const period = ref(localStorage.getItem(LS_KEY) || 'month')
function setPeriod(v) { period.value = v; localStorage.setItem(LS_KEY, v); kpis.fetch(); pipeline.fetch() }

const kpis = createResource({
  url: 'crm.finance.api.get_finance_kpis',
  makeParams() { return { company: company.value, period: period.value } },
  auto: true,
})
const pipeline = createResource({
  url: 'crm.finance.api.get_pipeline_summary',
  makeParams() { return { company: company.value, period: period.value } },
  auto: true,
})
const recentResource = createResource({
  url: 'crm.finance.api.get_ar_invoices',
  makeParams() { return { company: company.value, page: 0, page_size: 8, filters: JSON.stringify([]) } },
  auto: true,
})

watch(company, () => { kpis.fetch(); pipeline.fetch(); recentResource.fetch() })

const loading = computed(() => kpis.loading || pipeline.loading)
const recentLoading = computed(() => recentResource.loading)

const kd = computed(() => kpis.data || {})
function fmtKpi(key) {
  const d = kd.value[key]
  if (!d) return '—'
  const v = d.value ?? 0
  const cur = d.currency || ''
  if (v >= 1_000_000) return cur + ' ' + (v / 1_000_000).toFixed(1) + 'M'
  if (v >= 1_000) return cur + ' ' + (v / 1_000).toFixed(0) + 'K'
  return cur + ' ' + v.toLocaleString()
}
function delta(key) { return kd.value[key]?.delta_pct ?? 0 }

// Finance-semantic tones. Chip = pale surface-*-2 fill + ink-*-6 glyph.
const TONES = {
  neutral:   { chip: 'bg-surface-gray-3 text-ink-gray-7' },
  attention: { chip: 'bg-surface-red-2 text-ink-red-6' },
  pending:   { chip: 'bg-surface-amber-2 text-ink-amber-6' },
  positive:  { chip: 'bg-surface-green-2 text-ink-green-6' },
}

const kpiTiles = computed(() => [
  { key: 'ar_outstanding', label: 'AR Outstanding', section: 'invoices',  iconClass: 'lucide-receipt',     tone: TONES.neutral,   formatted: fmtKpi('ar_outstanding'), delta: delta('ar_outstanding') },
  { key: 'ar_overdue',     label: 'AR Overdue',     section: 'invoices',  iconClass: 'lucide-alert-circle', tone: TONES.attention, formatted: fmtKpi('ar_overdue'),     delta: delta('ar_overdue') },
  { key: 'invoiced_mtd',   label: 'Invoiced MTD',   section: 'invoices',  iconClass: 'lucide-file-text',    tone: TONES.pending,   formatted: fmtKpi('invoiced_mtd'),   delta: delta('invoiced_mtd') },
  { key: 'collected_mtd',  label: 'Collected MTD',  section: 'payments',  iconClass: 'lucide-banknote',     tone: TONES.positive,  formatted: fmtKpi('collected_mtd'),  delta: delta('collected_mtd') },
])

const pd = computed(() => pipeline.data || {})
const pipelineStages = computed(() => [
  { key: 'quotes',   label: 'Open Quotes',     section: 'quotes',   dot: 'bg-surface-gray-6',   count: pd.value.open_quotes     ?? '—', amount: fmtCurrency(pd.value.quotes_value    ?? 0, pd.value.currency) },
  { key: 'orders',   label: 'Active Orders',   section: 'orders',   dot: 'bg-surface-amber-6',  count: pd.value.active_orders   ?? '—', amount: fmtCurrency(pd.value.orders_value    ?? 0, pd.value.currency) },
  { key: 'invoices', label: 'Unpaid Invoices', section: 'invoices', dot: 'bg-surface-red-6',    count: pd.value.unpaid_invoices ?? '—', amount: fmtCurrency(pd.value.invoices_value  ?? 0, pd.value.currency) },
  { key: 'payments', label: 'Received MTD',    section: 'payments', dot: 'bg-surface-green-6',  count: pd.value.payments_mtd    ?? '—', amount: fmtCurrency(pd.value.payments_value  ?? 0, pd.value.currency) },
])

const recentInvoices = computed(() => recentResource.data || [])

function fmtCurrency(v, cur) {
  if (v == null || v === '') return '—'
  return formatCurrency(Number(v), cur || '')
}
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function statusClass(s) {
  return {
    'Unpaid':      'bg-surface-red-2 text-ink-red-6',
    'Partly Paid': 'bg-surface-amber-2 text-ink-amber-6',
    'Paid':        'bg-surface-green-2 text-ink-green-6',
    'Overdue':     'bg-surface-red-2 text-ink-red-6',
  }[s] || 'bg-surface-gray-2 text-ink-gray-6'
}
</script>
