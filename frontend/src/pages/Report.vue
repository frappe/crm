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
          @click="runReport"
        />
      </template>
    </LayoutHeader>

    <div
      v-if="filterScriptError"
      class="mx-5 mt-4 rounded bg-surface-amber-3 px-3 py-2 text-sm text-ink-amber-7"
    >
      {{
        __(
          "Some filters of this report couldn't be loaded here, so they are not shown.",
        )
      }}
    </div>

    <!-- Filters Row -->
    <div v-if="hasFilters" class="flex flex-wrap items-center gap-4 p-5 pb-2">
      <!-- Date Range Picker for paired from_date / to_date fields -->
      <DateRangePicker
        v-if="hasDateRangePair"
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
        <Link
          v-if="filter.fieldtype === 'Link'"
          class="form-control w-48"
          variant="outline"
          :value="filterValues[filter.fieldname]"
          :doctype="filter.options"
          :filters="getLinkQueryFilters(filter) || []"
          :placeholder="filterPlaceholder(filter)"
          @change="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <!-- Dynamic Link: its doctype comes from another filter -->
        <Link
          v-else-if="
            filter.fieldtype === 'Dynamic Link' && filterValues[filter.options]
          "
          class="form-control w-48"
          variant="outline"
          :value="filterValues[filter.fieldname]"
          :doctype="filterValues[filter.options]"
          :placeholder="filterPlaceholder(filter)"
          @change="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <MultiLinkSelect
          v-else-if="
            filter.fieldtype === 'MultiSelectList' &&
            typeof filter.options === 'string' &&
            !filter.options.includes('\n')
          "
          class="w-60"
          :modelValue="filterValues[filter.fieldname] || []"
          :doctype="filter.options"
          :filters="getLinkQueryFilters(filter)"
          :placeholder="filterPlaceholder(filter)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <MultiSelect
          v-else-if="filter.fieldtype === 'MultiSelectList'"
          class="w-60"
          variant="outline"
          :modelValue="filterValues[filter.fieldname] || []"
          :options="getSelectOptions(filter)"
          :placeholder="filterPlaceholder(filter)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <FormControl
          v-else-if="['Select', 'Autocomplete'].includes(filter.fieldtype)"
          :modelValue="filterValues[filter.fieldname]"
          type="select"
          class="w-48"
          :options="getSelectOptions(filter)"
          :placeholder="filterPlaceholder(filter)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <FormControl
          v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
          :type="filter.fieldtype === 'Date' ? 'date' : 'datetime'"
          class="w-48"
          :modelValue="filterValues[filter.fieldname]"
          :placeholder="filterPlaceholder(filter)"
          @update:modelValue="(v) => handleFilterChange(filter.fieldname, v)"
        />

        <DateRangePicker
          v-else-if="filter.fieldtype === 'DateRange'"
          class="!w-48"
          variant="outline"
          :value="(filterValues[filter.fieldname] || []).join(',') || null"
          :placeholder="filterPlaceholder(filter)"
          :formatter="formatRange"
          @change="(range) => handleDateRangeFilter(filter.fieldname, range)"
        />

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
          <span>{{ filterPlaceholder(filter) }}</span>
        </label>

        <!-- Data / numbers / Small Text: one request once typing pauses -->
        <FormControl
          v-else-if="filter.fieldtype !== 'Dynamic Link'"
          type="text"
          class="w-48"
          :debounce="500"
          :modelValue="filterValues[filter.fieldname]"
          :placeholder="filterPlaceholder(filter)"
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
        v-else-if="missingRequiredFilters.length"
        class="p-10 text-center text-sm text-ink-gray-5"
      >
        {{
          __('Set the required filters to run this report: {0}', [
            missingRequiredFilters.join(', '),
          ])
        }}
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
          <!-- report rows have no reliable unique key (grouped reports repeat names) -->
          <tr
            v-for="(row, idx) in displayedRows"
            :key="idx"
            class="border-b border-outline-gray-1 hover:bg-surface-gray-1"
          >
            <td
              v-for="column in displayedColumns"
              :key="column.key"
              class="whitespace-nowrap px-3 py-2 text-ink-gray-8"
              :style="{ width: column.width, textAlign: column.align }"
            >
              <router-link
                v-if="recordRoute(row[column.key], column)"
                :to="recordRoute(row[column.key], column)!"
                class="text-ink-blue-3 hover:underline"
              >
                {{ row[column.key] }}
              </router-link>
              <span v-else>{{ cellValue(row, column) }}</span>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="totalRow">
          <tr class="border-t-2 border-outline-gray-3 bg-surface-gray-1">
            <td
              v-for="column in displayedColumns"
              :key="column.key"
              class="whitespace-nowrap px-3 py-2 font-semibold text-ink-gray-9"
              :style="{ width: column.width, textAlign: column.align }"
            >
              {{ cellValue(totalRow, column) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Print & Export Modals -->
    <ReportPrintModal
      v-model:open="showPrintModal"
      :reportName="reportName"
      :title="title"
      :appliedFilters="appliedFilters"
      :columns="reportColumns"
      :visibleColumnKeys="displayedColumns.map((c) => c.key)"
      :rows="displayedRows"
      :totalRow="totalRow"
      :formatValue="cellValue"
    />

    <ReportExportModal
      v-model:open="showExportModal"
      :reportName="reportName"
      :filters="filterParams"
      :appliedFilters="appliedFilters"
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
import MultiLinkSelect from '@/components/Controls/MultiLinkSelect.vue'
import { formatDate } from '@/utils'
import { formatRange, parseDateRange } from '@/utils/dashboard'
import {
  evaluateReportFiltersScript,
  resolveFilterDefault,
  isFilterVisible,
  getReportFilterParams,
  getMissingRequiredFilters,
  getAppliedFilters,
  getLinkQueryFilters,
  getRecordRoute,
  formatReportValue,
} from '@/utils/reports'
import {
  usePageMeta,
  createResource,
  DateRangePicker,
  FormControl,
  MultiSelect,
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
const title = computed(() => reportMeta.data?.report_name || reportName.value)

const filterValues = reactive<Record<string, any>>({})
const dateRangePeriod = ref<string | null>(null)
const filterScriptError = ref(false)

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
  filterScriptError.value = false

  if (meta.filters && Array.isArray(meta.filters) && meta.filters.length) {
    // Query Report filters from the Report doc call "required" `mandatory`
    filters = meta.filters.map((f: any) => ({
      ...f,
      reqd: f.reqd ?? f.mandatory,
    }))
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
        onError: () => (filterScriptError.value = true),
      },
    )
  }

  reportFilters.value = filters
  for (const f of filters) {
    filterValues[f.fieldname] = resolveFilterDefault(f)
  }

  // from_date / to_date share one range picker; without defaults it starts empty
  dateRangePeriod.value =
    filterValues.from_date && filterValues.to_date
      ? `${filterValues.from_date},${filterValues.to_date}`
      : null

  runReport()
}

const hasDateRangePair = computed(() => {
  const names = reportFilters.value.map((f) => f.fieldname)
  return names.includes('from_date') && names.includes('to_date')
})

const visibleFilters = computed(() =>
  reportFilters.value.filter(
    (f) =>
      isFilterVisible(f, filterValues) &&
      !(
        hasDateRangePair.value && ['from_date', 'to_date'].includes(f.fieldname)
      ),
  ),
)

const hasFilters = computed(
  () => hasDateRangePair.value || visibleFilters.value.length > 0,
)

const filterParams = computed(() =>
  getReportFilterParams(reportFilters.value, filterValues),
)
const appliedFilters = computed(() =>
  getAppliedFilters(reportFilters.value, filterValues),
)
const missingRequiredFilters = computed(() =>
  getMissingRequiredFilters(reportFilters.value, filterValues),
)

function filterPlaceholder(filter: any) {
  const label = __(filter.label || filter.fieldname)
  return filter.reqd ? `${label} *` : label
}

function handleDateRangeChange(range: any) {
  dateRangePeriod.value = range
  const [from, to] = range ? parseDateRange(range) : []
  filterValues.from_date = from || null
  filterValues.to_date = to || null
  runReport()
}

// DateRange filters hold [from, to], as desk sends them
function handleDateRangeFilter(key: string, range: any) {
  const [from, to] = parseDateRange(range)
  handleFilterChange(key, from && to ? [from, to] : null)
}

function handleFilterChange(key: string, value: any) {
  filterValues[key] = value
  runReport()
}

// Runs the report with the current filters. An in-flight run is cancelled first,
// so a slow older response can't replace newer results.
function runReport() {
  reportData.abort()
  if (missingRequiredFilters.value.length) {
    reportData.data = null
    reportData.error = null
    return
  }
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
      filters: filterParams.value,
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

const displayedRows = computed(() => reportData.data?.rows || [])
const totalRow = computed(() => reportData.data?.total_row || null)

function cellValue(row: any, column: ReportColumn) {
  return formatReportValue(row[column.key], column, row, {
    defaultCurrency: reportData.data?.default_currency,
    // site date format; Datetime adds the site time format
    formatDate: (value: string, type: string) =>
      formatDate(value, '', true, type === 'Datetime'),
  })
}

function recordRoute(value: any, column: ReportColumn) {
  return getRecordRoute(value, column, reportMeta.data?.ref_doctype)
}

// Reload when route param changes (switching between pinned reports)
watch(reportName, () => {
  reportData.abort()
  reportColumns.value = []
  reportFilters.value = []
  filterScriptError.value = false
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
