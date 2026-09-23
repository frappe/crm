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
      expect(getReportRoute({ name: 'Lead Summary' })).toEqual({
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
      const pinned = [
        { report: 'Lost Deals', name: 'hash1' },
        { report: 'Lead Summary', name: 'hash2' },
      ]
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
})
