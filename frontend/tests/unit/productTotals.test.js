import { describe, expect, it, vi } from 'vitest'
import {
  RATE_METHOD,
  priceRow,
  productHandlers,
  updateTotals,
} from '../../../crm/fcrm/frontend/products/index.js'

function fakePage(rows, overrides = {}) {
  return {
    doctype: 'CRM Deal',
    docname: 'CRM-DEAL-45968',
    isNew: false,
    doc: { products: rows },
    call: vi.fn(() => Promise.resolve({ product_name: 'Widget', rate: 50 })),
    ...overrides,
  }
}

describe('priceRow', () => {
  it('sets the amount from quantity and rate, and nets out the discount', () => {
    const row = { qty: 2, rate: 100, discount_percentage: 10 }
    priceRow(row)
    expect(row).toMatchObject({
      amount: 200,
      discount_amount: 20,
      net_amount: 180,
    })
  })

  it('clears a discount once its percentage goes', () => {
    const row = {
      qty: 1,
      rate: 100,
      discount_percentage: 0,
      discount_amount: 20,
      net_amount: 80,
    }
    priceRow(row)
    expect(row).toMatchObject({
      amount: 100,
      discount_amount: 0,
      net_amount: 100,
    })
  })
})

describe('updateTotals', () => {
  it('sums the rows into total and net total', () => {
    const doc = {
      products: [
        { amount: 200, net_amount: 180, discount_percentage: 10 },
        { amount: 50, net_amount: 50 },
      ],
    }
    updateTotals(doc)
    expect(doc).toMatchObject({ total: 250, net_total: 230 })
  })

  it('takes the total as the net total when no row has a net amount', () => {
    const doc = { products: [{ amount: 120 }] }
    updateTotals(doc)
    expect(doc).toMatchObject({ total: 120, net_total: 120 })
  })

  it('keeps a net total of 0 under a full discount', () => {
    const doc = {
      products: [{ amount: 100, net_amount: 0, discount_percentage: 100 }],
    }
    updateTotals(doc)
    expect(doc).toMatchObject({ total: 100, net_total: 0 })
  })

  it('sets 0 for a record with no rows', () => {
    const doc = { products: [] }
    updateTotals(doc)
    expect(doc).toMatchObject({ total: 0, net_total: 0 })
  })
})

describe('productHandlers', () => {
  it('prices an added row and updates the totals', () => {
    const row = { qty: 3, rate: 10 }
    const page = fakePage([row])
    productHandlers.onAdd(page, row)
    expect(row.amount).toBe(30)
    expect(page.doc).toMatchObject({ total: 30, net_total: 30 })
  })

  it('updates the totals after a row is removed', () => {
    const page = fakePage([{ amount: 40, net_amount: 40 }], {
      doc: { products: [{ amount: 40, net_amount: 40 }], total: 90 },
    })
    productHandlers.onRemove(page)
    expect(page.doc.total).toBe(40)
  })

  it('reprices a row on a quantity, rate or discount change', () => {
    for (const fieldname of ['qty', 'rate', 'discount_percentage']) {
      const row = { qty: 2, rate: 25, discount_percentage: 50 }
      const page = fakePage([row])
      productHandlers[fieldname](page, row)
      expect(page.doc).toMatchObject({ total: 50, net_total: 25 })
    }
  })

  it("reads a picked product's name and rate, then prices the row", async () => {
    const row = { product_code: 'WIDGET', qty: 2 }
    const page = fakePage([row])
    await productHandlers.product_code(page, row)
    expect(page.call).toHaveBeenCalledWith(RATE_METHOD, {
      product_code: 'WIDGET',
      deal: 'CRM-DEAL-45968',
    })
    expect(row).toMatchObject({ product_name: 'Widget', rate: 50, amount: 100 })
    expect(page.doc.total).toBe(100)
  })

  it('sends no deal for a lead, whose name prices nothing', async () => {
    const row = { product_code: 'WIDGET', qty: 1 }
    const page = fakePage([row], {
      doctype: 'CRM Lead',
      docname: 'CRM-LEAD-45968',
    })
    await productHandlers.product_code(page, row)
    expect(page.call).toHaveBeenCalledWith(RATE_METHOD, {
      product_code: 'WIDGET',
      deal: undefined,
    })
  })

  it('takes a rate of 0 for a product with none', async () => {
    const row = { product_code: 'FREE', qty: 1 }
    const page = fakePage([row], {
      call: vi.fn(() => Promise.resolve({ product_name: 'Free', rate: null })),
    })
    await productHandlers.product_code(page, row)
    expect(row).toMatchObject({ rate: 0, amount: 0 })
  })

  it('leaves the row to a later pick made while the read was out', async () => {
    const row = { product_code: 'WIDGET', qty: 1 }
    let answer
    const page = fakePage([row], {
      call: vi.fn(() => new Promise((resolve) => (answer = resolve))),
    })
    const picking = productHandlers.product_code(page, row)
    row.product_code = 'GADGET'
    answer({ product_name: 'Widget', rate: 50 })
    await picking
    expect(row.product_name).toBeUndefined()
    expect(page.doc.total).toBeUndefined()
  })
})
