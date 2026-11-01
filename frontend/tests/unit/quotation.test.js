import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  CUSTOMER_METHOD,
  QUOTATION_METHOD,
  openQuotation,
  placeQuotationItems,
} from '../../../crm/fcrm/frontend/erpnext/quotation.js'

const LABELS = {
  createQuotation: 'Create Quotation',
  viewCustomer: 'View Customer',
  quotationFailed: 'Error while creating quotation in ERPNext',
}

function fakePage({
  enabled = 1,
  customerUrl = '',
  isNew = false,
  quotationUrl = 'https://erp.example/q',
} = {}) {
  return {
    isNew,
    docname: 'CRM-DEAL-45968',
    doc: { organization: 'Org 45968', erpnext_customer: null },
    header: { add: vi.fn() },
    toast: { error: vi.fn() },
    cached: vi.fn((key, fetch) => fetch()),
    call: vi.fn((method) => {
      if (method === 'frappe.client.get_single_value') return enabled
      if (method === CUSTOMER_METHOD) return customerUrl
      return Promise.resolve(quotationUrl)
    }),
  }
}

afterEach(() => vi.unstubAllGlobals())

describe('placeQuotationItems', () => {
  it("reads ERPNext CRM Settings' switch and adds Create Quotation to `⋯`", () => {
    const page = fakePage()
    placeQuotationItems(page, LABELS)
    expect(page.call).toHaveBeenCalledWith('frappe.client.get_single_value', {
      doctype: 'ERPNext CRM Settings',
      field: 'enabled',
    })
    const [item] = page.header.add.mock.calls[0]
    expect(item).toMatchObject({
      name: 'create_quotation',
      label: 'Create Quotation',
      group: 'erpnext',
    })
    expect(item.display).toBeUndefined()
  })

  it('adds nothing while ERPNext CRM Settings is off', () => {
    const page = fakePage({ enabled: 0 })
    placeQuotationItems(page, LABELS)
    expect(page.header.add).not.toHaveBeenCalled()
    expect(page.call).toHaveBeenCalledTimes(1)
  })

  it('adds nothing on a new deal', () => {
    const page = fakePage({ isNew: true })
    placeQuotationItems(page, LABELS)
    expect(page.cached).not.toHaveBeenCalled()
  })

  it('adds View Customer once the deal has a customer', () => {
    const page = fakePage({
      customerUrl: 'https://erp.example/app/customer/C-1',
    })
    placeQuotationItems(page, LABELS)
    expect(page.call).toHaveBeenCalledWith(CUSTOMER_METHOD, {
      crm_deal: 'CRM-DEAL-45968',
    })
    expect(page.header.add.mock.calls.map(([item]) => item.name)).toEqual([
      'create_quotation',
      'view_customer',
    ])
  })

  it('keys the customer read by the deal’s customer, so a new one is read again', () => {
    const page = fakePage()
    page.doc.erpnext_customer = 'C-1'
    placeQuotationItems(page, LABELS)
    expect(page.cached).toHaveBeenCalledWith(
      'erpnext_customer:C-1',
      expect.any(Function),
    )
  })
})

describe('openQuotation', () => {
  it('opens the quotation ERPNext answers with in a new tab', async () => {
    const open = vi.fn()
    vi.stubGlobal('window', { open })
    const page = fakePage()
    await openQuotation(page, LABELS.quotationFailed)
    expect(page.call).toHaveBeenCalledWith(QUOTATION_METHOD, {
      crm_deal: 'CRM-DEAL-45968',
      organization: 'Org 45968',
    })
    expect(open).toHaveBeenCalledWith('https://erp.example/q', '_blank')
  })

  it('toasts when ERPNext answers with no quotation', async () => {
    const open = vi.fn()
    vi.stubGlobal('window', { open })
    const page = fakePage({ quotationUrl: '' })
    await openQuotation(page, LABELS.quotationFailed)
    expect(open).not.toHaveBeenCalled()
    expect(page.toast.error).toHaveBeenCalledWith(LABELS.quotationFailed)
  })
})
