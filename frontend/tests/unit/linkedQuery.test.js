import { describe, expect, it } from 'vitest'
import { linkedQuery } from '../../../crm/fcrm/frontend/linked/linkedQuery.js'

const SOURCE = { doctype: 'Contact', field: 'company_name', fields: ['name'] }

describe('linkedQuery', () => {
  it("filters `source`'s rows by the page's record, newest change first", () => {
    expect(linkedQuery(SOURCE, 'Org 46018')).toEqual({
      fields: ['name'],
      filters: { company_name: 'Org 46018' },
      order_by: 'modified desc',
    })
  })

  it('groups a distinct source by name, so a child-table filter lists each record once', () => {
    const source = { ...SOURCE, field: 'contacts.contact', distinct: true }
    expect(linkedQuery(source, 'Contact 46018')).toMatchObject({
      filters: { 'contacts.contact': 'Contact 46018' },
      group_by: 'name',
    })
  })
})
