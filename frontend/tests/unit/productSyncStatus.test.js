import { describe, expect, it } from 'vitest'
import {
  canSync,
  countsLine,
  unsyncedLine,
} from '../../../crm/fcrm/frontend/settings/productSync/syncStatus.js'

describe('canSync', () => {
  it('needs the integration on and ERPNext on this site', () => {
    expect(canSync({ enabled: 1, is_erpnext_in_different_site: 0 })).toBe(true)
    expect(canSync({ enabled: 0, is_erpnext_in_different_site: 0 })).toBe(false)
    expect(canSync({ enabled: 1, is_erpnext_in_different_site: 1 })).toBe(false)
    expect(canSync({})).toBe(false)
    expect(canSync(undefined)).toBe(false)
  })
})

describe('countsLine', () => {
  it('counts CRM products and the ERPNext items linked to them', () => {
    expect(countsLine({ products: { count: 12 }, items: { count: 9 } })).toBe(
      '12 CRM products, 9 linked to ERPNext items',
    )
  })

  it('reads nothing before the status or without CRM Product read', () => {
    expect(countsLine(null)).toBe('')
    expect(countsLine({})).toBe('')
  })
})

describe('unsyncedLine', () => {
  it('names the unsynced items, and products only while the sync runs both ways', () => {
    expect(
      unsyncedLine({
        unsynced: { items: 3, products: 2, sync_products: true },
      }),
    ).toBe('3 items and 2 products not yet synced')
    expect(
      unsyncedLine({
        unsynced: { items: 1, products: 2, sync_products: false },
      }),
    ).toBe('1 item not yet synced')
    expect(
      unsyncedLine({
        unsynced: { items: 0, products: 1, sync_products: true },
      }),
    ).toBe('1 product not yet synced')
  })

  it('says nothing when all is synced', () => {
    expect(
      unsyncedLine({
        unsynced: { items: 0, products: 4, sync_products: false },
      }),
    ).toBe('')
    expect(unsyncedLine({})).toBe('')
  })
})
