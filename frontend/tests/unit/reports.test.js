import { describe, expect, it, vi, afterEach } from 'vitest'
import {
  getReportRoute,
  getReportKey,
  getReportIcon,
  isReportPinned,
  escapeHTML,
  generateReportPrintHTML,
  localToday,
  localDateOffset,
  localMonthOffset,
  evaluateReportFiltersScript,
  resolveFilterDefault,
  isFilterVisible,
  getReportFilterParams,
  getMissingRequiredFilters,
  getAppliedFilters,
  getLinkQueryFilters,
  getRecordRoute,
  getCurrencyForColumn,
  formatReportValue,
  isExpectedFileResponse,
  getServerErrorMessage,
} from '@/utils/reports'

describe('reports utility', () => {
  describe('getReportRoute', () => {
    it('returns Report route for a report string', () => {
      expect(getReportRoute('Lead Summary')).toEqual({
        name: 'Report',
        params: { reportName: 'Lead Summary' },
      })
    })

    it('returns Report route for a report object', () => {
      expect(getReportRoute({ report: 'Lead Summary' })).toEqual({
        name: 'Report',
        params: { reportName: 'Lead Summary' },
      })
    })
  })

  describe('getReportKey', () => {
    it('prefixes report name with "report-"', () => {
      expect(getReportKey('Lead Summary')).toBe('report-Lead Summary')
      expect(getReportKey({ report: 'Lead Summary' })).toBe(
        'report-Lead Summary',
      )
    })
  })

  describe('getReportIcon', () => {
    it('returns custom icon if provided on report object', () => {
      expect(getReportIcon({ report: 'My Report', icon: 'custom-icon' })).toBe(
        'custom-icon',
      )
    })

    it('falls back to default file-text icon', () => {
      const FileTextIcon = { name: 'FileText' }
      expect(getReportIcon('My Report', FileTextIcon)).toBe(FileTextIcon)
    })
  })

  describe('isReportPinned', () => {
    it('correctly checks whether report is in pinned reports array', () => {
      const pinned = [{ report: 'Lost Deals' }, { report: 'Lead Summary' }]
      expect(isReportPinned('Lost Deals', pinned)).toBe(true)
      expect(isReportPinned('Lead Summary', pinned)).toBe(true)
      expect(isReportPinned('Non-existent', pinned)).toBe(false)
      expect(isReportPinned(null, pinned)).toBe(false)
      expect(isReportPinned('Lost Deals', null)).toBe(false)
    })
  })

  describe('escapeHTML', () => {
    it('escapes special HTML characters', () => {
      expect(escapeHTML('<script>alert("xss")&</script>')).toBe(
        '&lt;script&gt;alert(&quot;xss&quot;)&amp;&lt;/script&gt;',
      )
    })

    it('handles empty or null values', () => {
      expect(escapeHTML('')).toBe('')
      expect(escapeHTML(null)).toBe('')
      expect(escapeHTML(undefined)).toBe('')
    })
  })

  describe('generateReportPrintHTML', () => {
    const columns = [
      { key: 'name', label: 'Deal', align: 'left' },
      { key: 'deal_value', label: 'Value', align: 'right' },
    ]
    const rows = [{ name: 'Big Deal', deal_value: '$50,000' }]

    it('generates valid print HTML document with report title and rows', () => {
      const html = generateReportPrintHTML({
        title: 'Lead Summary',
        filters: { status: 'Open' },
        includeFilters: true,
        columns,
        rows,
        orientation: 'Landscape',
        printDate: '2026-09-22',
      })
      expect(html).toContain('<!DOCTYPE html>')
      expect(html).toContain('<h1>Lead Summary</h1>')
      expect(html).toContain('size: landscape')
      expect(html).toContain('Applied Filters:')
      expect(html).toContain('status:')
      expect(html).toContain('Big Deal')
      expect(html).toContain('$50,000')
      expect(html).toContain('Total rows: 1')
    })
  })

  describe('date helpers (local timezone awareness)', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    describe('localToday', () => {
      it('returns a string matching YYYY-MM-DD format', () => {
        const result = localToday()
        expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      })

      it('uses local date calendar components', () => {
        const localNoon = new Date(2026, 8, 23, 12, 0, 0)
        vi.setSystemTime(localNoon)
        expect(localToday()).toBe('2026-09-23')
      })
    })

    describe('localDateOffset', () => {
      it('adds positive days correctly', () => {
        expect(localDateOffset('2026-01-28', 5)).toBe('2026-02-02')
      })

      it('subtracts days correctly', () => {
        expect(localDateOffset('2026-03-02', -2)).toBe('2026-02-28')
      })

      it('crosses month boundary into a new month', () => {
        expect(localDateOffset('2026-01-31', 1)).toBe('2026-02-01')
      })

      it('crosses year boundary', () => {
        expect(localDateOffset('2025-12-31', 1)).toBe('2026-01-01')
      })

      it('handles zero offset', () => {
        expect(localDateOffset('2026-06-15', 0)).toBe('2026-06-15')
      })
    })

    describe('localMonthOffset', () => {
      it('adds months correctly', () => {
        expect(localMonthOffset('2026-01-15', 3)).toBe('2026-04-15')
      })

      it('subtracts months correctly', () => {
        expect(localMonthOffset('2026-04-15', -3)).toBe('2026-01-15')
      })

      it('rolls over into the next year', () => {
        expect(localMonthOffset('2025-11-01', 3)).toBe('2026-02-01')
      })

      it('rolls back into the previous year', () => {
        expect(localMonthOffset('2026-02-01', -3)).toBe('2025-11-01')
      })

      it('handles zero offset', () => {
        expect(localMonthOffset('2026-06-15', 0)).toBe('2026-06-15')
      })

      it('clamps to destination month last day when overflowing (Jan 31 + 1 month -> Feb 28)', () => {
        expect(localMonthOffset('2026-01-31', 1)).toBe('2026-02-28')
      })

      it('clamps to leap year destination month (Jan 31 2024 + 1 month -> Feb 29 2024)', () => {
        expect(localMonthOffset('2024-01-31', 1)).toBe('2024-02-29')
      })

      it('clamps to 30-day month (May 31 - 1 month -> Apr 30)', () => {
        expect(localMonthOffset('2026-05-31', -1)).toBe('2026-04-30')
      })
    })
  })

  describe('evaluateReportFiltersScript (filter logic and sandboxing)', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    it('returns empty array if script is empty or invalid', () => {
      expect(evaluateReportFiltersScript('', 'Lead Summary')).toEqual([])
      expect(evaluateReportFiltersScript(null, 'Lead Summary')).toEqual([])
      expect(evaluateReportFiltersScript('invalid syntax :::', 'Test')).toEqual(
        [],
      )
    })

    it('extracts static filter definitions from query_reports object', () => {
      const script = `
        frappe.query_reports["Lead Summary"] = {
          filters: [
            { fieldname: "status", label: __("Status"), fieldtype: "Select", options: "Open\\nClosed" },
            { fieldname: "lead_owner", label: __("Owner"), fieldtype: "Link", options: "User" }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Lead Summary')
      expect(filters).toHaveLength(2)
      expect(filters[0].fieldname).toBe('status')
      expect(filters[1].fieldname).toBe('lead_owner')
    })

    it('supports dynamic default values using frappe.datetime.get_today()', () => {
      const fixedDate = new Date(2026, 8, 23, 12, 0, 0)
      vi.setSystemTime(fixedDate)

      const script = `
        frappe.query_reports["Sales Analytics"] = {
          filters: [
            {
              fieldname: "from_date",
              label: "From Date",
              fieldtype: "Date",
              default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
            },
            {
              fieldname: "to_date",
              label: "To Date",
              fieldtype: "Date",
              default: frappe.datetime.get_today()
            }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Sales Analytics')
      expect(filters).toHaveLength(2)
      expect(filters[1].default).toBe('2026-09-23')
      expect(filters[0].default).toBe('2026-08-23')
    })

    it('supports add_days for rolling period filters', () => {
      const fixedDate = new Date(2026, 8, 23, 12, 0, 0)
      vi.setSystemTime(fixedDate)

      const script = `
        frappe.query_reports["Recent Activity"] = {
          filters: [
            {
              fieldname: "start_date",
              default: frappe.datetime.add_days(frappe.datetime.get_today(), -7)
            }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Recent Activity')
      expect(filters[0].default).toBe('2026-09-16')
    })

    it('supports month_start and month_end in datetime sandbox', () => {
      const fixedDate = new Date(2026, 8, 23, 12, 0, 0)
      vi.setSystemTime(fixedDate)

      const script = `
        frappe.query_reports["Monthly Report"] = {
          filters: [
            { fieldname: "from_date", default: frappe.datetime.month_start() },
            { fieldname: "to_date", default: frappe.datetime.month_end() }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Monthly Report')
      expect(filters[0].default).toBe('2026-09-01')
      expect(filters[1].default).toBe('2026-09-30')
    })

    it('pre-populates user filter using sessionUser option', () => {
      const script = `
        frappe.query_reports["My Assigned Deals"] = {
          filters: [
            {
              fieldname: "user",
              label: "Assigned User",
              fieldtype: "Link",
              options: "User",
              default: frappe.session.user
            }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'My Assigned Deals', {
        sessionUser: 'sales_rep@example.com',
      })
      expect(filters[0].default).toBe('sales_rep@example.com')
    })

    it('handles query_report.get_filter_value for interdependent filters', () => {
      const script = `
        frappe.query_reports["Dependent Report"] = {
          filters: [
            {
              fieldname: "company",
              default: "Acme Corp"
            },
            {
              fieldname: "sub_filter",
              default: function() {
                return frappe.query_report.get_filter_value("company") + " - Default";
              }
            }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Dependent Report', {
        filterValues: { company: 'Acme Corp' },
      })
      expect(filters).toHaveLength(2)
      expect(typeof filters[1].default).toBe('function')
      expect(filters[1].default()).toBe('Acme Corp - Default')
    })

    it('does not crash when accessing un-stubbed frappe properties via Proxy', () => {
      const script = `
        frappe.query_reports["Tolerant Report"] = {
          filters: [
            {
              fieldname: "custom_status",
              default: frappe.non_existent_module ? "Custom" : "Standard"
            }
          ]
        };
      `
      const filters = evaluateReportFiltersScript(script, 'Tolerant Report')
      expect(filters).toHaveLength(1)
      expect(filters[0].default).toBe('Standard')
    })
  })

  describe('evaluateReportFiltersScript with desk-only APIs', () => {
    it('still loads filters when the script calls frappe.provide, frappe.ui and erpnext', () => {
      const script = `
        frappe.provide("erpnext.utils");
        frappe.ui.form.on("Deal", { refresh() {} });
        frappe.query_reports["Desk Report"] = {
          filters: [
            { fieldname: "company", fieldtype: "Link", options: "Company",
              default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()) },
            { fieldname: "status", fieldtype: "Select", options: "Open\\nWon", default: "Open" }
          ]
        };
      `
      const onError = vi.fn()
      const filters = evaluateReportFiltersScript(script, 'Desk Report', {
        onError,
      })
      expect(onError).not.toHaveBeenCalled()
      expect(filters.map((f) => f.fieldname)).toEqual(['company', 'status'])
      // a default built from a stubbed call resolves to empty, not a proxy
      expect(resolveFilterDefault(filters[0])).toBeNull()
      expect(resolveFilterDefault(filters[1])).toBe('Open')
    })

    it('runs frappe.require callbacks so filters defined inside them load', () => {
      const script = `
        frappe.require("assets/x.js", () => {
          frappe.query_reports["Lazy"] = { filters: [{ fieldname: "a" }] };
        });
      `
      expect(evaluateReportFiltersScript(script, 'Lazy')).toHaveLength(1)
    })

    it('reports a script that still fails instead of failing silently', () => {
      const onError = vi.fn()
      const filters = evaluateReportFiltersScript(
        'throw new Error("boom")',
        'Broken',
        { onError },
      )
      expect(filters).toEqual([])
      expect(onError).toHaveBeenCalledOnce()
    })
  })

  describe('report filters', () => {
    const filters = [
      { fieldname: 'company', label: 'Company', fieldtype: 'Link', reqd: 1 },
      {
        fieldname: 'territory',
        label: 'Territory',
        fieldtype: 'Link',
        depends_on: 'eval:doc.company',
      },
      { fieldname: 'secret', label: 'Secret', fieldtype: 'Data', hidden: 1 },
      { fieldname: 'range', label: 'Range', fieldtype: 'DateRange' },
      { fieldname: 'open', label: 'Open Only', fieldtype: 'Check' },
      { fieldname: 'tags', label: 'Tags', fieldtype: 'MultiSelectList' },
      { fieldname: 'weird', label: 'Weird', fieldtype: 'Geolocation' },
    ]

    it('has no invented default: an unset filter stays empty', () => {
      expect(resolveFilterDefault({ fieldname: 'from_date' })).toBeNull()
      expect(resolveFilterDefault({ default: 'Today' })).toBe(localToday())
      expect(resolveFilterDefault({ default: () => 'x' })).toBe('x')
    })

    it('hides filters by hidden and depends_on', () => {
      expect(isFilterVisible(filters[1], {})).toBe(false)
      expect(isFilterVisible(filters[1], { company: 'Acme' })).toBe(true)
      expect(isFilterVisible(filters[2], {})).toBe(false)
    })

    it('sends only supported, active, non-empty values', () => {
      const values = {
        company: '',
        territory: 'North',
        secret: 's',
        tags: [],
        weird: 'value the user cannot see',
      }
      // territory is inactive (no company); hidden filters are still sent, as in desk
      expect(getReportFilterParams(filters, values)).toEqual({ secret: 's' })
    })

    it('lists required filters that are empty', () => {
      expect(getMissingRequiredFilters(filters, {})).toEqual(['Company'])
      expect(getMissingRequiredFilters(filters, { company: 'Acme' })).toEqual(
        [],
      )
    })

    it('shows applied filters by label with display values', () => {
      expect(
        getAppliedFilters(filters, {
          company: 'Acme',
          open: 1,
          tags: ['a', 'b'],
          range: ['2026-01-01', '2026-01-31'],
        }),
      ).toEqual({
        Company: 'Acme',
        'Open Only': 'Yes',
        Tags: 'a, b',
        Range: '2026-01-01 – 2026-01-31',
      })
    })

    it('uses get_query only when it gives plain filters', () => {
      expect(
        getLinkQueryFilters({ get_query: () => ({ filters: { a: 1 } }) }),
      ).toEqual({ a: 1 })
      expect(
        getLinkQueryFilters({ get_query: () => ({ query: 'x.y' }) }),
      ).toBeNull()
      expect(getLinkQueryFilters({})).toBeNull()
    })
  })

  describe('report values', () => {
    it('links only CRM doctypes', () => {
      const link = (options) => ({ type: 'Link', options, key: 'x' })
      expect(getRecordRoute('CRM-DEAL-1', link('CRM Deal'))).toEqual({
        name: 'Deal',
        params: { dealId: 'CRM-DEAL-1' },
      })
      expect(getRecordRoute('OPP-1', link('Opportunity'))).toBeNull()
      expect(getRecordRoute('LEAD-1', link('Lead'))).toBeNull()
      expect(getRecordRoute('Cust', link('Customer'))).toBeNull()
      expect(getRecordRoute('CRM-LEAD-1', { key: 'name' }, 'CRM Lead')).toEqual(
        { name: 'Lead', params: { leadId: 'CRM-LEAD-1' } },
      )
    })

    it('resolves currency from the row, then the site default', () => {
      const column = { type: 'Currency', options: 'currency' }
      expect(getCurrencyForColumn({ currency: 'EUR' }, column, 'INR')).toBe(
        'EUR',
      )
      expect(getCurrencyForColumn({}, column, 'INR')).toBe('INR')
      // a short fieldname is not mistaken for a currency code
      expect(
        getCurrencyForColumn({}, { type: 'Currency', options: 'cur' }, 'INR'),
      ).toBe('INR')
    })

    it('formats cell values by column type', () => {
      expect(formatReportValue(1, { type: 'Check' })).toBe('Yes')
      expect(formatReportValue(0, { type: 'Check' })).toBe('No')
      expect(formatReportValue(['a', 'b'], { type: 'Data' })).toBe('a, b')
      expect(formatReportValue(null, { type: 'Currency' })).toBe('')
      expect(
        formatReportValue(
          '2026-01-02',
          { type: 'Date' },
          {},
          {
            formatDate: () => 'formatted',
          },
        ),
      ).toBe('formatted')
      expect(
        formatReportValue(
          1500,
          { type: 'Currency' },
          {},
          {
            defaultCurrency: 'USD',
          },
        ),
      ).toContain('1,500')
    })
  })

  describe('print output', () => {
    it('formats cells and puts the total row in the footer', () => {
      const html = generateReportPrintHTML({
        title: 'Deals',
        filters: { Status: 'Open', Tags: ['a', 'b'] },
        columns: [{ key: 'deal', label: 'Deal' }],
        rows: [{ deal: 'CRM-DEAL-1' }, { deal: 'CRM-DEAL-2' }],
        totalRow: { deal: 'Total' },
        formatValue: (value) => `<${value}>`,
      })
      expect(html).toContain('Status:')
      expect(html).toContain('a, b')
      expect(html).toContain('&lt;CRM-DEAL-1&gt;')
      expect(html).toContain('<tfoot><tr class="total-row">')
      expect(html).toContain('Total rows: 2')
    })
  })

  describe('file downloads', () => {
    const response = (body, contentType, status = 200) =>
      new Response(body, { status, headers: { 'content-type': contentType } })

    it('accepts only the requested file type', () => {
      expect(
        isExpectedFileResponse(response('%PDF', 'application/pdf'), 'pdf'),
      ).toBe(true)
      expect(
        isExpectedFileResponse(
          response('{"exc": "x"}', 'application/json'),
          'pdf',
        ),
      ).toBe(false)
      expect(
        isExpectedFileResponse(
          response('<html>No data</html>', 'text/html'),
          'xlsx',
        ),
      ).toBe(false)
      expect(
        isExpectedFileResponse(
          response('a,b', 'text/csv; charset=utf-8'),
          'csv',
        ),
      ).toBe(true)
      expect(
        isExpectedFileResponse(response('x', 'application/pdf', 500), 'pdf'),
      ).toBe(false)
    })

    it('shows the server message, never the traceback', async () => {
      const serverMessages = JSON.stringify([
        JSON.stringify({ message: '<b>No data to export</b>' }),
      ])
      expect(
        await getServerErrorMessage(
          response(
            JSON.stringify({
              exc: 'Traceback ...',
              _server_messages: serverMessages,
            }),
            'application/json',
            417,
          ),
          'fallback',
        ),
      ).toBe('No data to export')
      expect(
        await getServerErrorMessage(
          response(
            JSON.stringify({
              exception: 'frappe.exceptions.PermissionError: Not allowed',
              exc: 'Traceback',
            }),
            'application/json',
            403,
          ),
          'fallback',
        ),
      ).toBe('Not allowed')
      expect(
        await getServerErrorMessage(
          response('<html></html>', 'text/html', 500),
          'fallback',
        ),
      ).toBe('fallback')
    })
  })
})
