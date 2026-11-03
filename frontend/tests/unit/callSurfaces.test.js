import { describe, expect, it } from 'vitest'

const { default: fieldActions } =
  await import('../../../crm/fcrm/frontend/field-actions.js')
const { callRowAction } =
  await import('../../../crm/fcrm/frontend/telephony/callRowAction.js')
const { default: leadList } =
  await import('../../../crm/fcrm/doctype/crm_lead/frontend/list.js')
const { default: dealList } =
  await import('../../../crm/fcrm/doctype/crm_deal/frontend/list.js')

describe('Make a call on a phone field', () => {
  it('places the act on every Phone control', () => {
    expect(fieldActions).toEqual([
      { fieldtype: 'Phone', act: 'shell.crm.make_a_call' },
    ])
  })
})

describe('Make a call on a list row', () => {
  it('is a row action on Lead and Deal lists', () => {
    expect(leadList.rowActions).toEqual([callRowAction])
    expect(dealList.rowActions).toEqual([callRowAction])
  })

  it('reads both number fields into the list query', () => {
    expect(callRowAction.act).toBe('shell.crm.make_a_call')
    expect(callRowAction.fields).toEqual(['mobile_no', 'phone'])
  })

  it('calls the mobile number, else the phone', () => {
    expect(callRowAction.value({ mobile_no: '+1 1', phone: '+1 2' })).toBe(
      '+1 1',
    )
    expect(callRowAction.value({ mobile_no: '', phone: '+1 2' })).toBe('+1 2')
  })

  it('is drawn only on a row with a number', () => {
    expect(callRowAction.when({ mobile_no: '', phone: null })).toBe(false)
    expect(callRowAction.when({ mobile_no: null, phone: '+1 2' })).toBe(true)
  })
})
