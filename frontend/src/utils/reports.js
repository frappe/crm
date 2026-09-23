/**
 * Utilities for CRM Report navigation, routing, and configuration.
 */

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

/**
 * Evaluates a Report's frontend JS script in a safe sandbox to extract filter definitions.
 * Stubs common Frappe globals (datetime, session, boot, query_report, utils, db).
 */
export function evaluateReportFiltersScript(script, reportName, options = {}) {
  if (!script) return []
  try {
    const today = localToday()
    const sessionUser = options.sessionUser || ''
    const filterValues = options.filterValues || {}

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

    const fakeFrappe = new Proxy(
      {
        query_reports: {},
        datetime: datetimeSandbox,
        session: { user: sessionUser },
        boot: { user_info: { name: sessionUser } },
        defaults: {
          get_user_default: (k) => (k === 'user' ? sessionUser : ''),
          get_default: (k) => (k === 'user' ? sessionUser : ''),
          get_global_default: () => '',
        },
        utils: {
          get_fiscal_year: () => null,
          formatDate: (d) => d,
          nowdate: () => today,
        },
        query_report: {
          get_filter_value: (fieldname) => filterValues[fieldname],
          set_filter_value: (fieldname, val) => {
            filterValues[fieldname] = val
          },
        },
        db: {
          get_value: () => null,
          get_list: () => [],
          count: () => 0,
        },
      },
      {
        get(target, prop) {
          if (prop in target) return target[prop]
          return undefined
        },
      },
    )

    const fn = new Function('frappe', '__', script)
    fn(fakeFrappe, (s) => s)

    const reportConf =
      fakeFrappe.query_reports[reportName] ||
      fakeFrappe.query_reports[reportName?.replace(/ /g, '_')] ||
      Object.values(fakeFrappe.query_reports)[0] ||
      {}
    return reportConf.filters || []
  } catch (e) {
    console.warn('Failed to evaluate report filters script for', reportName, e)
    return []
  }
}

export function getReportRoute(report) {
  const name =
    typeof report === 'string' ? report : report?.report || report?.name || ''

  return { name: 'Report', params: { reportName: name } }
}

export function getReportKey(report) {
  const name =
    typeof report === 'string' ? report : report?.report || report?.name || ''

  return 'report-' + name
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
  return pinnedReports.some(
    (p) => p.report === reportName || p.name === reportName,
  )
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

export function generateReportPrintHTML({
  title = 'Report',
  filters = {},
  includeFilters = true,
  columns = [],
  rows = [],
  orientation = 'Landscape',
  printDate = '',
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
                `<span class="filter-pill"><span class="filter-key">${escapeHTML(k)}:</span> ${escapeHTML(v)}</span>`,
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

  const rowsHtml = rows
    .map((row) => {
      const cells = columns
        .map((col) => {
          const val = row[col.key] ?? ''
          return `<td style="text-align: ${col.align || 'left'};">${escapeHTML(val)}</td>`
        })
        .join('')
      return `<tr>${cells}</tr>`
    })
    .join('')

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
