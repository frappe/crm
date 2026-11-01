import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  CUSTOMER_METHOD,
  QUOTATION_METHOD,
  QUOTATION_SCRIPT,
  openQuotation,
  placeQuotationItems,
} from '../../../crm/fcrm/frontend/erpnext/quotation.js'

const LABELS = {
  createQuotation: 'Create Quotation',
  viewCustomer: 'View Customer',
  quotationFailed: 'Error while creating quotation in ERPNext',
}

const NO_CUSTOMER = { customerUrl: '' }

function fakePage(options = {}) {
  const {
    enabled = 1,
    customerUrl = '',
    isNew = false,
    quotationUrl = 'https://erp.example/q',
  } = options
  const held = 'held' in options ? options.held : NO_CUSTOMER
  return {
    isNew,
    docname: 'CRM-DEAL-45968',
    doc: { organization: 'Org 45968', erpnext_customer: null },
    header: { add: vi.fn() },
    toast: { error: vi.fn() },
    cached: vi.fn(() => held),
    call: vi.fn(async (method) => {
      if (method === 'frappe.client.get_single_value') return enabled
      if (method === CUSTOMER_METHOD) return customerUrl
      return quotationUrl
    }),
  }
}

/** The fetcher `placeQuotationItems` hands `page.cached`, run as the page would. */
function readERPNext(page, scriptEnabled = vi.fn(async () => true)) {
  placeQuotationItems(page, LABELS, scriptEnabled)
  const [, fetch] = page.cached.mock.calls[0]
  return fetch()
}

afterEach(() => vi.unstubAllGlobals())

describe('placeQuotationItems', () => {
  it('adds Create Quotation to `⋯` while ERPNext CRM Settings is enabled', () => {
    const page = fakePage()
    placeQuotationItems(page, LABELS)
    const [item] = page.header.add.mock.calls[0]
    expect(item).toMatchObject({
      name: 'create_quotation',
      label: 'Create Quotation',
      group: 'erpnext',
    })
    expect(item.display).toBeUndefined()
    expect(page.header.add).toHaveBeenCalledTimes(1)
  })

  it('adds nothing while ERPNext CRM Settings is off, or before it is read', () => {
    for (const held of [null, undefined]) {
      const page = fakePage({ held })
      placeQuotationItems(page, LABELS)
      expect(page.header.add).not.toHaveBeenCalled()
    }
  })

  it('adds nothing on a new deal', () => {
    const page = fakePage({ isNew: true })
    placeQuotationItems(page, LABELS)
    expect(page.cached).not.toHaveBeenCalled()
  })

  it('adds View Customer once the deal has a customer', () => {
    const page = fakePage({
      held: { customerUrl: 'https://erp.example/app/customer/C-1' },
    })
    placeQuotationItems(page, LABELS)
    expect(page.header.add.mock.calls.map(([item]) => item.name)).toEqual([
      'create_quotation',
      'view_customer',
    ])
  })

  it('keys the read by the deal’s customer, so a new one is read again', () => {
    const page = fakePage()
    page.doc.erpnext_customer = 'C-1'
    placeQuotationItems(page, LABELS)
    expect(page.cached).toHaveBeenCalledWith(
      'erpnext:C-1',
      expect.any(Function),
    )
  })
})

describe('the ERPNext read', () => {
  it("reads ERPNext CRM Settings' switch, then the deal's customer link, in one fetch", async () => {
    const page = fakePage({
      customerUrl: 'https://erp.example/app/customer/C-1',
    })
    expect(await readERPNext(page)).toEqual({
      customerUrl: 'https://erp.example/app/customer/C-1',
    })
    expect(page.call).toHaveBeenCalledWith('frappe.client.get_single_value', {
      doctype: 'ERPNext CRM Settings',
      field: 'enabled',
    })
    expect(page.call).toHaveBeenCalledWith(CUSTOMER_METHOD, {
      crm_deal: 'CRM-DEAL-45968',
    })
  })

  it('reads no customer while ERPNext CRM Settings is off', async () => {
    const page = fakePage({ enabled: 0 })
    expect(await readERPNext(page)).toBeNull()
    expect(page.call).toHaveBeenCalledTimes(1)
  })

  it('reads no customer while the v1 "Create Quotation from CRM Deal" row is disabled', async () => {
    const page = fakePage()
    const scriptEnabled = vi.fn(async () => false)
    expect(await readERPNext(page, scriptEnabled)).toBeNull()
    expect(scriptEnabled).toHaveBeenCalledWith(QUOTATION_SCRIPT)
    expect(page.call).toHaveBeenCalledTimes(1)
  })

  it('keeps Create Quotation when the customer lookup fails', async () => {
    const page = fakePage()
    page.call.mockImplementation(async (method) => {
      if (method === CUSTOMER_METHOD) throw new Error('no crm_deal column')
      return 1
    })
    expect(await readERPNext(page)).toEqual(NO_CUSTOMER)
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

  it('toasts a refused call instead of throwing, so the host keeps the draft', async () => {
    const open = vi.fn()
    vi.stubGlobal('window', { open })
    const page = fakePage()
    page.call = vi.fn(() =>
      Promise.reject(new Error('ERPNext is not reachable')),
    )
    await expect(
      openQuotation(page, LABELS.quotationFailed),
    ).resolves.toBeUndefined()
    expect(open).not.toHaveBeenCalled()
    expect(page.toast.error).toHaveBeenCalledWith('ERPNext is not reachable')
  })
})
