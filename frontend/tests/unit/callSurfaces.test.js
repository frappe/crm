import { describe, expect, it, vi } from 'vitest'

const { default: fieldActions } = await import(
  '../../../crm/fcrm/frontend/field-actions.js'
)
const { callRowAction } = await import(
  '../../../crm/fcrm/frontend/telephony/callRowAction.js'
)
const { default: leadList } = await import(
  '../../../crm/fcrm/doctype/crm_lead/frontend/list.js'
)
const { default: dealList } = await import(
  '../../../crm/fcrm/doctype/crm_deal/frontend/list.js'
)

describe('Make a call on a phone field', () => {
  it('places the act on every Phone control', () => {
    expect(fieldActions).toEqual([
      {
        fieldtype: 'Phone',
        act: 'shell.crm.make_a_call',
        quickActionLabel: 'Call',
      },
    ])
  })
})

describe('Make a call on a list row', () => {
  const page = { rowActions: { add: vi.fn() }, run: vi.fn() }

  it('is a row action on Lead and Deal lists', () => {
    leadList.onRefresh(page)
    dealList.onRefresh(page)
    expect(page.rowActions.add.mock.calls).toEqual([
      [callRowAction],
      [callRowAction],
    ])
  })

  it('reads both number fields into the list query', () => {
    expect(callRowAction.fields).toEqual(['mobile_no', 'phone'])
  })

  it('calls the mobile number, else the phone', () => {
    callRowAction.run(page, { mobile_no: '+1 1', phone: '+1 2' })
    callRowAction.run(page, { mobile_no: '', phone: '+1 2' })
    expect(page.run.mock.calls).toEqual([
      ['shell.crm.make_a_call', '+1 1'],
      ['shell.crm.make_a_call', '+1 2'],
    ])
  })

  it('is drawn only on a row with a number', () => {
    expect(callRowAction.when(page, { mobile_no: '', phone: null })).toBe(false)
    expect(callRowAction.when(page, { mobile_no: null, phone: '+1 2' })).toBe(
      true,
    )
  })
})
