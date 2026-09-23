<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-7">{{ title }}</div>
      </template>
      <template #right-header>
        <Button
          :label="__('Print')"
          :iconLeft="LucidePrinter"
          variant="outline"
          @click="showPrintModal = true"
        />
        <Button
          :label="__('Export')"
          :iconLeft="LucideDownload"
          variant="outline"
          @click="showExportModal = true"
        />
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          :loading="reportData.loading"
          @click="reportData.reload"
        />
      </template>
    </LayoutHeader>

    <!-- Filters Row -->
    <div v-if="hasFilters" class="flex flex-wrap items-center gap-4 p-5 pb-2">
      <!-- Date Range Picker for paired from_date / to_date fields -->
      <DateRangePicker
        v-if="hasDateRangeFilter"
        class="!w-48"
        :value="dateRangePeriod"
        variant="outline"
        :placeholder="__('Date Range')"
        :formatter="formatRange"
        @change="handleDateRangeChange"
      >
        <template #prefix>
          <LucideCalendar class="mr-2 size-4 text-ink-gray-5" />
        </template>
      </DateRangePicker>

      <!-- Other Report Filters -->
      <template v-for="filter in visibleFilters" :key="filter.fieldname">
        <!-- Link Field Filter -->
        <Link
          v-if="filter.fieldtype === 'Link'"
          class="form-control w-48"
          variant="outline"
          :value="filterValues[filter.fieldname]"
          :doctype="filter.options"
          :placeholder="__(filter.label)"
          @change="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <!-- Select Field Filter -->
        <FormControl
          v-else-if="filter.fieldtype === 'Select'"
          :modelValue="filterValues[filter.fieldname]"
          type="select"
          class="w-48"
          :options="getSelectOptions(filter)"
          :placeholder="__(filter.label)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <!-- Single Date Filter — uses a plain date input, not a range picker -->
        <FormControl
          v-else-if="filter.fieldtype === 'Date'"
          type="date"
          class="w-48"
          :modelValue="filterValues[filter.fieldname]"
          :placeholder="__(filter.label)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <!-- Check (Boolean) Filter -->
        <label
          v-else-if="filter.fieldtype === 'Check'"
          class="flex items-center gap-2 cursor-pointer select-none text-sm text-ink-gray-7"
        >
          <input
            type="checkbox"
            :checked="!!filterValues[filter.fieldname]"
            @change="
              (e) =>
                handleFilterChange(
                  filter.fieldname,
                  (e.target as HTMLInputElement).checked ? 1 : 0,
                )
            "
          />
          <span>{{ __(filter.label) }}</span>
        </label>

        <!-- Data / Int / Float / Currency / Small Text — plain text input -->
        <FormControl
          v-else-if="
            ['Data', 'Int', 'Float', 'Currency', 'Small Text'].includes(
              filter.fieldtype,
            )
          "
          type="text"
          class="w-48"
          :modelValue="filterValues[filter.fieldname]"
          :placeholder="__(filter.label)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />
      </template>
    </div>

    <!-- Data Table Container -->
    <div class="flex-1 overflow-auto px-5 pb-5">
      <div
        v-if="
          (reportMeta.loading && !reportMeta.data) ||
          (reportData.loading && !reportData.data)
        "
        class="p-10 text-center text-sm text-ink-gray-5"
      >
        {{ __('Loading...') }}
      </div>

      <div
        v-else-if="reportMeta.error || reportData.error"
        class="p-10 text-center text-sm text-red-500"
      >
        {{ errorMessage }}
      </div>

      <div
        v-else-if="!displayedRows.length"
        class="p-10 text-center text-sm text-ink-gray-5"
      >
        {{ __('No records found') }}
      </div>

      <table
        v-else-if="displayedColumns.length && displayedRows.length"
        class="w-full border-collapse text-sm"
      >
        <thead>
          <tr class="border-b border-outline-gray-2 text-left text-ink-gray-6">
            <th
              v-for="column in displayedColumns"
              :key="column.key"
              class="whitespace-nowrap px-3 py-2 font-medium"
              :style="{ width: column.width, textAlign: column.align }"
            >
              {{ __(column.label) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in displayedRows"
            :key="row.name || idx"
            class="border-b border-outline-gray-1 hover:bg-surface-gray-1"
          >
            <td
              v-for="column in displayedColumns"
              :key="column.key"
              class="whitespace-nowrap px-3 py-2 text-ink-gray-8"
              :style="{ width: column.width, textAlign: column.align }"
            >
              <!-- Link to record if a CRM route exists for this column or doctype -->
              <router-link
                v-if="getRecordRoute(row[column.key], column)"
                :to="getRecordRoute(row[column.key], column)!"
                class="text-ink-blue-3 hover:underline"
              >
                {{ row[column.key] }}
              </router-link>

              <!-- Currency formatted value -->
              <span v-else-if="column.type === 'Currency'">
                {{
                  formatCurrency(
                    row[column.key],
                    '',
                    getCurrencyForColumn(row, column),
                  )
                }}
              </span>

              <!-- Regular text -->
              <span v-else>{{ row[column.key] ?? '' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Print & Export Modals -->
    <ReportPrintModal
      v-model:open="showPrintModal"
      :reportName="reportName"
      :filters="filterValues"
      :columns="reportColumns"
      :visibleColumnKeys="displayedColumns.map((c) => c.key)"
      :rows="displayedRows"
    />

    <ReportExportModal
      v-model:open="showExportModal"
      :reportName="reportName"
      :filters="filterValues"
      :columns="displayedColumns"
    />
  </div>
</template>

<script setup lang="ts">
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucideCalendar from '~icons/lucide/calendar'
import LucidePrinter from '~icons/lucide/printer'
import LucideDownload from '~icons/lucide/download'
import ReportPrintModal from '@/components/Modals/ReportPrintModal.vue'
import ReportExportModal from '@/components/Modals/ReportExportModal.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { formatCurrency } from '@/utils/numberFormat.js'
import { getLastXDays, formatRange, parseDateRange } from '@/utils/dashboard'
import { localToday, evaluateReportFiltersScript } from '@/utils/reports'
import {
  usePageMeta,
  createResource,
  DateRangePicker,
  FormControl,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { ref, reactive, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const showPrintModal = ref(false)
const showExportModal = ref(false)

interface ReportColumn {
  key: string
  label: string
  type: string
  options?: string
  width: string
  align: 'left' | 'right'
  hidden?: number
}

const route = useRoute()
const reportName = computed(() => String(route.params.reportName || ''))
const title = computed(() => reportName.value)

const filterValues = reactive<Record<string, any>>({})
const dateRangePeriod = ref<string | null>(null)

// Fetch report metadata (ref_doctype, script, filters)
const reportMeta = createResource({
  url: 'crm.api.report.get_report_meta',
  makeParams() {
    return { report_name: reportName.value }
  },
  auto: true,
  onSuccess(data) {
    initializeFilters(data)
  },
})

// Parsed filters list from report meta / script
const reportFilters = ref<any[]>([])

function initializeFilters(meta: any) {
  if (!meta) return
  let filters: any[] = []

  if (meta.filters && Array.isArray(meta.filters) && meta.filters.length) {
    filters = meta.filters
  } else if (meta.script) {
    const session = sessionStore()
    const sessionUser: string =
      session.user ||
      (window as any).frappe?.session?.user ||
      (window as any).frappe?.boot?.user_info?.name ||
      ''
    filters = evaluateReportFiltersScript(
      meta.script,
      meta.name || meta.report_name,
      {
        sessionUser,
        filterValues,
      },
    )
  }

  reportFilters.value = filters

  // Setup default filter values (supporting static values, 'Today', and functions)
  for (const f of filters) {
    if (f.default !== undefined) {
      if (typeof f.default === 'function') {
        try {
          filterValues[f.fieldname] = f.default()
        } catch {
          filterValues[f.fieldname] = null
        }
      } else if (f.default === 'Today' || f.default === 'today') {
        filterValues[f.fieldname] = localToday()
      } else {
        filterValues[f.fieldname] = f.default
      }
    } else {
      filterValues[f.fieldname] = null
    }
  }

  // Handle paired from_date & to_date as DateRangePicker
  const hasFromDate = filters.some((f) => f.fieldname === 'from_date')
  const hasToDate = filters.some((f) => f.fieldname === 'to_date')

  if (hasFromDate && hasToDate) {
    const fromVal =
      filterValues.from_date || parseDateRange(getLastXDays(365))[0]
    const toVal = filterValues.to_date || parseDateRange(getLastXDays(365))[1]
    filterValues.from_date = fromVal
    filterValues.to_date = toVal
    dateRangePeriod.value = `${fromVal},${toVal}`
  }

  reportData.reload()
}

const hasDateRangeFilter = computed(() => {
  return (
    reportFilters.value.some((f) => f.fieldname === 'from_date') &&
    reportFilters.value.some((f) => f.fieldname === 'to_date')
  )
})

const visibleFilters = computed(() => {
  if (hasDateRangeFilter.value) {
    return reportFilters.value.filter(
      (f) => f.fieldname !== 'from_date' && f.fieldname !== 'to_date',
    )
  }
  return reportFilters.value
})

const hasFilters = computed(() => {
  return hasDateRangeFilter.value || visibleFilters.value.length > 0
})

function handleDateRangeChange(range: any) {
  dateRangePeriod.value = range
  const [from, to] = parseDateRange(range)
  filterValues.from_date = from || null
  filterValues.to_date = to || null
  reportData.reload()
}

function handleFilterChange(key: string, value: any) {
  filterValues[key] = value
  reportData.reload()
}

function getSelectOptions(filter: any) {
  if (Array.isArray(filter.options)) {
    return filter.options.map((opt: any) =>
      typeof opt === 'string' ? { label: opt, value: opt } : opt,
    )
  }
  if (typeof filter.options === 'string') {
    return filter.options
      .split('\n')
      .filter(Boolean)
      .map((opt: string) => ({ label: opt, value: opt }))
  }
  return []
}

// Columns returned from the report runner
const reportColumns = ref<ReportColumn[]>([])

// Fetch report columns and rows
const reportData = createResource({
  url: 'crm.api.report.get_report_data',
  makeParams() {
    return {
      report_name: reportName.value,
      filters: { ...filterValues },
    }
  },
  auto: false,
  onSuccess(data) {
    reportColumns.value = data?.columns?.length
      ? data.columns.map((c: ReportColumn) => ({ ...c }))
      : []
  },
})

// Error message computed from report metadata or report data query
const errorMessage = computed(() => {
  const err = (reportMeta.error || reportData.error) as any
  if (!err) return ''
  return (
    err?.messages?.join(' ') ||
    err?.message ||
    __('An error occurred while loading the report.')
  )
})

// Columns displayed in the table exclude hidden columns
const displayedColumns = computed<ReportColumn[]>(() =>
  reportColumns.value.filter((col: any) => !col.hidden),
)

const displayedRows = computed(() => {
  return reportData.data?.rows || []
})

// Currency resolution from column options field, row currency, or system default
function getCurrencyForColumn(row: any, column: ReportColumn): string {
  if (column.options && row[column.options]) {
    return row[column.options]
  }
  if (
    column.options &&
    typeof column.options === 'string' &&
    column.options.length === 3 &&
    !row[column.options]
  ) {
    return column.options
  }
  return row.currency || (window as any).sysdefaults?.currency || 'USD'
}

// Link routing for Link columns and report primary record name
const DOCTYPE_ROUTE_MAP: Record<
  string,
  { routeName: string; paramKey: string }
> = {
  'CRM Deal': { routeName: 'Deal', paramKey: 'dealId' },
  Opportunity: { routeName: 'Deal', paramKey: 'dealId' },
  'CRM Lead': { routeName: 'Lead', paramKey: 'leadId' },
  Lead: { routeName: 'Lead', paramKey: 'leadId' },
  Contact: { routeName: 'Contact', paramKey: 'contactId' },
  'CRM Organization': { routeName: 'Organization', paramKey: 'organizationId' },
  Customer: { routeName: 'Organization', paramKey: 'organizationId' },
}

function getRecordRoute(value: any, column: ReportColumn) {
  if (!value || typeof value !== 'string') return null

  let targetDoctype = ''
  if (column.type === 'Link' && column.options) {
    targetDoctype = column.options
  } else if (column.key === 'name') {
    targetDoctype = reportMeta.data?.ref_doctype || ''
  }

  const mapping = DOCTYPE_ROUTE_MAP[targetDoctype]
  if (!mapping) return null

  return {
    name: mapping.routeName,
    params: { [mapping.paramKey]: value },
  }
}

// Reload when route param changes (switching between pinned reports)
watch(reportName, () => {
  reportColumns.value = []
  reportFilters.value = []
  if (reportData.data) reportData.data = null
  if (reportData.error) reportData.error = null
  if (reportMeta.data) reportMeta.data = null
  if (reportMeta.error) reportMeta.error = null
  Object.keys(filterValues).forEach((k) => delete filterValues[k])
  reportMeta.reload()
})

usePageMeta(() => {
  return { title: title.value }
})
</script>
