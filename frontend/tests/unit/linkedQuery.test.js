import { describe, expect, it } from 'vitest'
import {
  linkedQuery,
  uniqueRows,
} from '../../../crm/fcrm/frontend/linked/linkedQuery.js'

const SOURCE = {
  doctype: 'CRM Deal',
  field: 'contacts.contact',
  fields: ['name'],
}

describe('linkedQuery', () => {
  it("filters `source`'s rows by the page's record, newest change first", () => {
    expect(linkedQuery(SOURCE, 'Contact 46018')).toEqual({
      fields: ['name'],
      filters: { 'contacts.contact': 'Contact 46018' },
      order_by: 'modified desc',
    })
  })
})

describe('uniqueRows', () => {
  it('keeps the first row of each record, in order', () => {
    const rows = [{ name: 'B' }, { name: 'A' }, { name: 'B' }, { name: 'C' }]
    expect(uniqueRows(rows)).toEqual([
      { name: 'B' },
      { name: 'A' },
      { name: 'C' },
    ])
  })
})
