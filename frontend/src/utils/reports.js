/**
 * Utilities for CRM Report navigation, routing, and configuration.
 */

import { formatCurrency, formatNumber, cint } from '@/utils/numberFormat.js'
import { evaluateDependsOnValue } from '@/utils/expressions.js'

// ---------------------------------------------------------------------------
// Date helpers — local-timezone-aware
// ---------------------------------------------------------------------------

/**
 * Returns today's date in YYYY-MM-DD using the browser's LOCAL timezone.
 */
export function localToday() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * Adds `days` (may be negative) to a YYYY-MM-DD date string and returns
 * the result as YYYY-MM-DD in LOCAL timezone.
 * Parses the base date as local midnight to avoid DST and UTC-offset issues.
 */
export function localDateOffset(base, days) {
  const dt = new Date(`${base}T00:00:00`) // local midnight
  dt.setDate(dt.getDate() + days)
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const d = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * Adds `months` (may be negative) to a YYYY-MM-DD date string and returns
 * the result as YYYY-MM-DD in LOCAL timezone.
 * Clamps to the destination month's last day to avoid month overflow (e.g. Jan 31 -> Feb 28).
 */
export function localMonthOffset(base, months) {
  const parts = base.split('-').map(Number)
  const year = parts[0]
  const month = parts[1] - 1
  const day = parts[2]

  const targetDate = new Date(year, month + months, 1)
  const targetYear = targetDate.getFullYear()
  const targetMonth = targetDate.getMonth()
  const daysInTargetMonth = new Date(targetYear, targetMonth + 1, 0).getDate()
  const clampedDay = Math.min(day, daysInTargetMonth)

  const y = targetYear
  const m = String(targetMonth + 1).padStart(2, '0')
  const d = String(clampedDay).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// Desk namespaces report scripts call while defining filters (frappe.ui.form.on,
// frappe.model..., frappe.call...). They don't exist in CRM, so they become no-ops.
const DESK_NAMESPACES = [
  'ui',
  'model',
  'form',
  'dom',
  'views',
  'meta',
  'call',
  'xcall',
  'msgprint',
  'show_alert',
  'set_route',
  'route_options',
  'realtime',
  'format',
  'tools',
]

// A value that swallows any call, property access or `new`, so a script line like
// `erpnext.utils.get_fiscal_year(...)` runs instead of throwing.
function createNoop() {
  const noop = new Proxy(function () {}, {
    get(target, prop) {
      if (prop === 'then') return undefined // don't look like a promise
      if (prop === Symbol.toPrimitive) return () => ''
      return noop
    },
    apply: () => noop,
    construct: () => noop,
  })
  return noop
}

function withFallback(target, fallback) {
  return new Proxy(target, {
    get(obj, prop) {
      return prop in obj ? obj[prop] : fallback
    },
  })
}

/**
 * Runs a report's desk JS to read its filter definitions.
 *
 * This is NOT a security sandbox: the script runs with full page access, exactly as
 * it does in desk, and is written by whoever can edit the Report. It only stubs the
 * desk APIs report scripts use while defining filters, so they load outside desk.
 * Unknown `frappe.*` members stay undefined so scripts can still feature-detect.
 *
 * A script that still fails returns [] and reports the error through
 * `options.onError`, so the page can say so instead of silently showing no filters.
 */
export function evaluateReportFiltersScript(script, reportName, options = {}) {
  if (!script) return []
  try {
    const today = localToday()
    const sessionUser = options.sessionUser || ''
    const filterValues = options.filterValues || {}
    const noop = createNoop()

    const datetimeSandbox = {
      get_today: () => today,
      now_datetime: () => `${today} 00:00:00`,
      add_months: (d, m) => localMonthOffset(d, m),
      add_days: (d, n) => localDateOffset(d, n),
      month_start: () => `${today.slice(0, 7)}-01`,
      month_end: () => {
        const parts = today.split('-').map(Number)
        const days = new Date(parts[0], parts[1], 0).getDate()
        return `${parts[0]}-${String(parts[1]).padStart(2, '0')}-${String(days).padStart(2, '0')}`
      },
      quarter_start: () => {
        const parts = today.split('-').map(Number)
        const qMonth = Math.floor((parts[1] - 1) / 3) * 3 + 1
        return `${parts[0]}-${String(qMonth).padStart(2, '0')}-01`
      },
      quarter_end: () => {
        const parts = today.split('-').map(Number)
        const qMonth = Math.floor((parts[1] - 1) / 3) * 3 + 3
        const days = new Date(parts[0], qMonth, 0).getDate()
        return `${parts[0]}-${String(qMonth).padStart(2, '0')}-${String(days).padStart(2, '0')}`
      },
      str_to_obj: (d) => new Date(`${d}T00:00:00`),
      obj_to_str: (dt) => {
        if (!(dt instanceof Date) || isNaN(dt.getTime())) return today
        const y = dt.getFullYear()
        const mo = String(dt.getMonth() + 1).padStart(2, '0')
        const day = String(dt.getDate()).padStart(2, '0')
        return `${y}-${mo}-${day}`
      },
      user_to_str: (d) => d,
      user_to_obj: (d) => new Date(`${d}T00:00:00`),
      year_start: () => `${new Date().getFullYear()}-01-01`,
      year_end: () => `${new Date().getFullYear()}-12-31`,
      get_diff: (d1, d2) => {
        const t1 = new Date(`${d1}T00:00:00`).getTime()
        const t2 = new Date(`${d2}T00:00:00`).getTime()
        return Math.round((t1 - t2) / (1000 * 60 * 60 * 24))
      },
      validate: () => true,
      get_datetime_as_string: (dt) =>
        dt instanceof Date
          ? dt.toISOString().replace('T', ' ').slice(0, 19)
          : String(dt || ''),
    }

    const fakeFrappe = withFallback(
      {
        query_reports: {},
        datetime: withFallback(datetimeSandbox, noop),
        session: { user: sessionUser },
        boot: { user_info: { name: sessionUser } },
        defaults: withFallback(
          {
            get_user_default: (k) => (k === 'user' ? sessionUser : ''),
            get_default: (k) => (k === 'user' ? sessionUser : ''),
            get_global_default: () => '',
          },
          noop,
        ),
        utils: withFallback(
          {
            get_fiscal_year: () => null,
            formatDate: (d) => d,
            nowdate: () => today,
          },
          noop,
        ),
        query_report: withFallback(
          {
            get_filter_value: (fieldname) => filterValues[fieldname],
            set_filter_value: (fieldname, val) => {
              filterValues[fieldname] = val
            },
          },
          noop,
        ),
        db: withFallback(
          { get_value: () => null, get_list: () => [], count: () => 0 },
          noop,
        ),
        provide: () => noop,
        require: (assets, callback) => {
          if (typeof callback === 'function') callback()
          return Promise.resolve()
        },
        ...Object.fromEntries(DESK_NAMESPACES.map((name) => [name, noop])),
      },
      undefined,
    )

    const fn = new Function('frappe', '__', 'erpnext', script)
    fn(fakeFrappe, (s) => s, noop)

    const reportConf =
      fakeFrappe.query_reports[reportName] ||
      fakeFrappe.query_reports[reportName?.replace(/ /g, '_')] ||
      Object.values(fakeFrappe.query_reports)[0] ||
      {}
    return reportConf.filters || []
  } catch (e) {
    console.warn('Failed to evaluate report filters script for', reportName, e)
    options.onError?.(e)
    return []
  }
}

// ---------------------------------------------------------------------------
// Report filters
// ---------------------------------------------------------------------------

// Filter types the report page can render. Others are neither shown nor sent,
// so a value the user can't see never changes the result.
export const SUPPORTED_FILTER_TYPES = [
  'Link',
  'Dynamic Link',
  'Select',
  'Autocomplete',
  'MultiSelectList',
  'Date',
  'Datetime',
  'DateRange',
  'Check',
  'Data',
  'Small Text',
  'Int',
  'Float',
  'Currency',
  'Percent',
]

export function isFilterSupported(filter) {
  return SUPPORTED_FILTER_TYPES.includes(filter?.fieldtype || 'Data')
}

function isEmptyValue(value) {
  return (
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && !value.length)
  )
}

/** A filter's starting value: static, 'Today' or a function; null when unset. */
export function resolveFilterDefault(filter) {
  let value = filter?.default
  if (typeof value === 'function') {
    try {
      value = value()
    } catch {
      value = null
    }
  }
  if (value === 'Today' || value === 'today') value = localToday()
  // a default built from an unsupported desk call resolves to a no-op function
  if (value === undefined || typeof value === 'function') value = null
  return value
}

/** Filters whose depends_on is false are hidden and not sent, as in desk. */
export function isFilterActive(filter, values) {
  return (
    isFilterSupported(filter) &&
    Boolean(evaluateDependsOnValue(filter.depends_on, values || {}))
  )
}

export function isFilterVisible(filter, values) {
  return isFilterActive(filter, values) && !cint(filter.hidden)
}

/** Filter values to send to the server: supported, active and non-empty. */
export function getReportFilterParams(filters, values) {
  const params = {}
  for (const filter of filters || []) {
    const value = values?.[filter.fieldname]
    if (!isFilterActive(filter, values) || isEmptyValue(value)) continue
    params[filter.fieldname] = value
  }
  return params
}

/** Labels of required filters that are still empty. */
export function getMissingRequiredFilters(filters, values) {
  return (filters || [])
    .filter(
      (f) =>
        cint(f.reqd) &&
        isFilterActive(f, values) &&
        isEmptyValue(values?.[f.fieldname]),
    )
    .map((f) => __(f.label || f.fieldname))
}

/** Applied filters keyed by label with display values, as desk prints and exports them. */
export function getAppliedFilters(filters, values) {
  const applied = {}
  for (const filter of filters || []) {
    const value = values?.[filter.fieldname]
    if (!isFilterActive(filter, values) || isEmptyValue(value)) continue
    const label = __(filter.label || filter.fieldname)
    if (filter.fieldtype === 'Check') {
      applied[label] = cint(value) ? __('Yes') : __('No')
    } else if (Array.isArray(value)) {
      applied[label] = value.join(
        filter.fieldtype === 'DateRange' ? ' – ' : ', ',
      )
    } else {
      applied[label] = value
    }
  }
  return applied
}

/**
 * Static filters from a Link filter's get_query. Only a plain filters object is
 * supported; a server-side query needs desk and is ignored.
 */
export function getLinkQueryFilters(filter) {
  if (!filter?.get_query) return null
  let query
  try {
    query =
      typeof filter.get_query === 'function'
        ? filter.get_query()
        : filter.get_query
  } catch {
    return null
  }
  const filters = query?.filters
  return filters && typeof filters === 'object' ? filters : null
}

// ---------------------------------------------------------------------------
// Report values
// ---------------------------------------------------------------------------

// Only CRM doctypes: other apps' names (Opportunity, Lead, Customer) aren't CRM record ids.
export const DOCTYPE_ROUTE_MAP = {
  'CRM Deal': { routeName: 'Deal', paramKey: 'dealId' },
  'CRM Lead': { routeName: 'Lead', paramKey: 'leadId' },
  Contact: { routeName: 'Contact', paramKey: 'contactId' },
  'CRM Organization': { routeName: 'Organization', paramKey: 'organizationId' },
}

/** CRM route for a cell that names a record, or null. */
export function getRecordRoute(value, column, refDoctype) {
  if (!value || typeof value !== 'string') return null

  let doctype = ''
  if (column?.type === 'Link' && column.options) doctype = column.options
  else if (column?.key === 'name') doctype = refDoctype || ''

  const mapping = DOCTYPE_ROUTE_MAP[doctype]
  if (!mapping) return null
  return { name: mapping.routeName, params: { [mapping.paramKey]: value } }
}

/** A Currency column's currency: the row's currency field, then the site default. */
export function getCurrencyForColumn(row, column, defaultCurrency) {
  return (
    (column?.options && row?.[column.options]) ||
    row?.currency ||
    defaultCurrency ||
    window.sysdefaults?.currency ||
    'USD'
  )
}

/** Display value for a report cell, used by the table and print. */
export function formatReportValue(value, column, row, options = {}) {
  if (value === null || value === undefined || value === '') return ''
  if (Array.isArray(value)) return value.join(', ')

  switch (column?.type) {
    case 'Currency':
      return formatCurrency(
        value,
        '',
        getCurrencyForColumn(row, column, options.defaultCurrency),
      )
    case 'Float':
      return formatNumber(value)
    case 'Int':
      return formatNumber(value, '', 0)
    case 'Percent':
      return `${formatNumber(value)}%`
    case 'Check':
      return cint(value) ? __('Yes') : __('No')
    case 'Date':
    case 'Datetime':
      return options.formatDate ? options.formatDate(value, column.type) : value
    default:
      return String(value)
  }
}

// ---------------------------------------------------------------------------
// Server responses for file downloads
// ---------------------------------------------------------------------------

const FILE_CONTENT_TYPES = {
  pdf: ['application/pdf'],
  xlsx: [
    'spreadsheetml',
    'application/vnd.ms-excel',
    'application/octet-stream',
  ],
  csv: ['text/csv', 'application/csv', 'application/octet-stream'],
}

/** True when the response is the requested file, not an error page or JSON. */
export function isExpectedFileResponse(response, kind) {
  if (!response?.ok) return false
  const type = response.headers?.get('content-type') || ''
  return (FILE_CONTENT_TYPES[kind] || []).some((t) => type.includes(t))
}

function stripTags(text) {
  return String(text)
    .replace(/<[^>]*>/g, '')
    .trim()
}

/**
 * The user-facing message from a Frappe error response. Never the traceback (exc).
 */
export async function getServerErrorMessage(response, fallback) {
  let data
  try {
    data = await response.clone().json()
  } catch {
    return fallback
  }

  if (data?._server_messages) {
    try {
      const messages = JSON.parse(data._server_messages)
        .map((m) => {
          try {
            return JSON.parse(m).message
          } catch {
            return m
          }
        })
        .filter(Boolean)
        .map(stripTags)
      if (messages.length) return messages.join(' ')
    } catch {
      // fall through
    }
  }

  // "frappe.exceptions.ValidationError: No data to export" -> "No data to export"
  if (typeof data?.exception === 'string') {
    const message = data.exception.split(': ').slice(1).join(': ').trim()
    if (message) return stripTags(message)
  }
  return fallback
}

// ---------------------------------------------------------------------------
// Sidebar pins
// ---------------------------------------------------------------------------

function reportNameOf(report) {
  return typeof report === 'string' ? report : report?.report || ''
}

export function getReportRoute(report) {
  return { name: 'Report', params: { reportName: reportNameOf(report) } }
}

export function getReportKey(report) {
  return 'report-' + reportNameOf(report)
}

export function getReportIcon(report, LucideFileText) {
  return (
    (typeof report === 'object' && report?.icon) ||
    LucideFileText ||
    'lucide-file-text'
  )
}

export function isReportPinned(reportName, pinnedReports = []) {
  if (!reportName || !Array.isArray(pinnedReports)) return false
  return pinnedReports.some((p) => p.report === reportName)
}

export function escapeHTML(str) {
  if (str === null || str === undefined) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Printable HTML for a report.
 * `filters` is keyed by label with display values (see getAppliedFilters);
 * `formatValue(value, column, row)` formats cells; `totalRow` goes in <tfoot>.
 */
export function generateReportPrintHTML({
  title = 'Report',
  filters = {},
  includeFilters = true,
  columns = [],
  rows = [],
  totalRow = null,
  orientation = 'Landscape',
  printDate = '',
  formatValue = (value) => value,
}) {
  const dateStr = printDate || new Date().toLocaleString()
  const filterEntries =
    includeFilters && filters
      ? Object.entries(filters).filter(
          ([, v]) => v !== null && v !== undefined && v !== '',
        )
      : []

  const filtersHtml =
    filterEntries.length > 0
      ? `<div class="filters-container">
        <strong>Applied Filters:</strong>
        <div class="filter-pills">
          ${filterEntries
            .map(
              ([k, v]) =>
                `<span class="filter-pill"><span class="filter-key">${escapeHTML(k)}:</span> ${escapeHTML(Array.isArray(v) ? v.join(', ') : v)}</span>`,
            )
            .join(' ')}
        </div>
      </div>`
      : ''

  const headersHtml = columns
    .map(
      (col) =>
        `<th style="text-align: ${col.align || 'left'};">${escapeHTML(col.label || col.key)}</th>`,
    )
    .join('')

  const cellsHtml = (row) =>
    columns
      .map((col) => {
        const val = formatValue(row[col.key] ?? '', col, row)
        return `<td style="text-align: ${col.align || 'left'};">${escapeHTML(val)}</td>`
      })
      .join('')

  const rowsHtml = rows.map((row) => `<tr>${cellsHtml(row)}</tr>`).join('')
  const totalHtml = totalRow
    ? `<tfoot><tr class="total-row">${cellsHtml(totalRow)}</tr></tfoot>`
    : ''

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHTML(title)}</title>
  <style>
    @page {
      size: ${orientation.toLowerCase()};
      margin: 12mm;
    }
    * {
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1f2937;
      background: #ffffff;
      margin: 0;
      padding: 16px;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .report-header {
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 12px;
      margin-bottom: 16px;
    }
    .report-header-top {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      color: #111827;
    }
    .report-meta {
      font-size: 11px;
      color: #6b7280;
    }
    .filters-container {
      margin-top: 10px;
      font-size: 12px;
    }
    .filter-pills {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 4px;
    }
    .filter-pill {
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      padding: 2px 8px;
      font-size: 11px;
    }
    .filter-key {
      font-weight: 600;
      color: #4b5563;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      line-height: 1.4;
    }
    th {
      background-color: #f9fafb !important;
      color: #374151;
      font-weight: 600;
      border: 1px solid #e5e7eb;
      padding: 6px 10px;
      white-space: nowrap;
    }
    td {
      border: 1px solid #e5e7eb;
      padding: 6px 10px;
      color: #1f2937;
    }
    tr:nth-child(even) td {
      background-color: #fbfcfd;
    }
    .total-row td {
      font-weight: 600;
      border-top: 2px solid #d1d5db;
      background-color: #f9fafb;
    }
    .report-footer {
      margin-top: 16px;
      font-size: 11px;
      color: #6b7280;
      display: flex;
      justify-content: space-between;
    }
    @media print {
      body {
        padding: 0;
      }
      thead {
        display: table-header-group;
      }
      tr {
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="report-header">
    <div class="report-header-top">
      <h1>${escapeHTML(title)}</h1>
      <div class="report-meta">Printed: ${escapeHTML(dateStr)}</div>
    </div>
    ${filtersHtml}
  </div>
  <table>
    <thead>
      <tr>${headersHtml}</tr>
    </thead>
    <tbody>
      ${rowsHtml || '<tr><td colspan="' + (columns.length || 1) + '" style="text-align: center; padding: 20px;">No records found</td></tr>'}
    </tbody>
    ${totalHtml}
  </table>
  <div class="report-footer">
    <span>Total rows: ${rows.length}</span>
    <span>Frappe CRM</span>
  </div>
</body>
</html>`
}

export function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }, 100)
}

export function printHTML(html) {
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    alert('Please allow pop-ups in your browser to print the report.')
    return
  }
  printWindow.document.open()
  printWindow.document.write(html)
  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.onafterprint = () => {
      try {
        printWindow.close()
      } catch {
        // Ignore if already closed
      }
    }
    printWindow.print()
  }, 250)
}
