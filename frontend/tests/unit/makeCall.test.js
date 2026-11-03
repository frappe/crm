import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  callState,
  registerOutgoingStarter,
} from '../../../crm/fcrm/frontend/telephony/callState.js'
import {
  MAKE_A_CALL,
  addCallItem,
  makeACallAct,
  recordNumbers,
  typedNumberOptions,
} from '../../../crm/fcrm/frontend/telephony/makeCall.js'

afterEach(() => {
  callState.media = []
})

describe('the Make a call act', () => {
  it('is hidden while the user has no calling medium', () => {
    expect(makeACallAct.when()).toBe(false)
    callState.media = ['Exotel']
    expect(makeACallAct.when()).toBe(true)
  })

  it('takes a typed number as its one choice', () => {
    expect(makeACallAct.argument.options({}, ' +1 (555) 010-0100 ')).toEqual([
      {
        value: '+1 (555) 010-0100',
        label: '+1 (555) 010-0100',
        icon: 'lucide-phone',
      },
    ])
  })

  it.each(['', 'ab', '12', 'call me 555'])(
    'offers no choice for %j',
    (query) => {
      expect(typedNumberOptions(query)).toEqual([])
    },
  )

  it('starts the outgoing call to the number it was given', () => {
    const start = vi.fn()
    const unregister = registerOutgoingStarter(start)
    makeACallAct.run({}, '+15550100')
    unregister()
    expect(start).toHaveBeenCalledWith('+15550100')
  })

  it('refuses to run without a number', () => {
    expect(() => makeACallAct.run({}, undefined)).toThrow()
  })
})

describe('recordNumbers', () => {
  it('lists the mobile number first and drops blanks and repeats', () => {
    expect(recordNumbers({ mobile_no: ' 111 ', phone: '222' })).toEqual([
      '111',
      '222',
    ])
    expect(recordNumbers({ mobile_no: '111', phone: '111' })).toEqual(['111'])
    expect(recordNumbers({ mobile_no: '', phone: null })).toEqual([])
  })
})

describe('the record header entry', () => {
  const pageOf = (doc, isNew = false) => ({
    isNew,
    doc,
    header: { add: vi.fn() },
    run: vi.fn(),
  })

  it('is not added on a new record or one with no number', () => {
    const fresh = pageOf({ mobile_no: '111' }, true)
    const empty = pageOf({})
    addCallItem(fresh)
    addCallItem(empty)
    expect(fresh.header.add).not.toHaveBeenCalled()
    expect(empty.header.add).not.toHaveBeenCalled()
  })

  it('calls the only number with no question, and hides with the act', () => {
    const page = pageOf({ phone: '222' })
    addCallItem(page)
    const [item] = page.header.add.mock.calls[0]
    expect(item.argument).toBeUndefined()
    expect(item.when()).toBe(false)
    item.run(page)
    expect(page.run).toHaveBeenCalledWith(MAKE_A_CALL, '222')
  })

  it('asks which of two numbers to call', () => {
    const page = pageOf({ mobile_no: '111', phone: '222' })
    addCallItem(page)
    const [item] = page.header.add.mock.calls[0]
    expect(item.argument.options(page).map((option) => option.value)).toEqual([
      '111',
      '222',
    ])
    item.run(page, '222')
    expect(page.run).toHaveBeenCalledWith(MAKE_A_CALL, '222')
  })
})
