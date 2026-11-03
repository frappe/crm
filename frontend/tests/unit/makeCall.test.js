import { afterEach, describe, expect, it } from 'vitest'
import {
  callState,
  registerOutgoingStarter,
} from '../../../crm/fcrm/frontend/telephony/callState.js'
import {
  MAKE_A_CALL,
  makeACallAct,
  phoneValues,
  recordPhoneOptions,
  typedNumberOptions,
} from '../../../crm/fcrm/frontend/telephony/makeCall.js'

let unregister = () => {}

afterEach(() => {
  callState.media = []
  unregister()
  unregister = () => {}
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

  describe('on a record page', () => {
    const fields = [
      { fieldname: 'status', label: 'Status', fieldtype: 'Link' },
      { fieldname: 'mobile_no', label: 'Mobile No', fieldtype: 'Phone' },
      { fieldname: 'phone', label: 'Phone', fieldtype: 'Phone' },
      { fieldname: 'fax', label: 'Fax', fieldtype: 'Phone' },
    ]
    const shellOf = (doc) => ({
      record: () => ({ doctype: 'CRM Lead', name: 'L-1', doc, fields }),
    })
    const option = (value, description) => ({
      value,
      label: value,
      description,
      icon: 'lucide-phone',
    })

    it("offers the record's numbers first, each with its field label", () => {
      const shell = shellOf({ mobile_no: ' 111 ', phone: '222', status: '333' })
      expect(makeACallAct.argument.options(shell, '')).toEqual([
        option('111', 'Mobile No'),
        option('222', 'Phone'),
      ])
    })

    it('still offers the typed number after them', () => {
      const shell = shellOf({ mobile_no: '111' })
      expect(makeACallAct.argument.options(shell, '+1 555 0100')).toEqual([
        option('111', 'Mobile No'),
        {
          value: '+1 555 0100',
          label: '+1 555 0100',
          icon: 'lucide-phone',
        },
      ])
    })

    it('does not offer a typed number the record already has', () => {
      const shell = shellOf({ mobile_no: '111' })
      expect(makeACallAct.argument.options(shell, '111')).toEqual([
        option('111', 'Mobile No'),
      ])
    })

    it('names every field that holds the same number', () => {
      const doc = { mobile_no: '111', phone: '111' }
      expect(recordPhoneOptions({ doc, fields })).toEqual([
        option('111', 'Mobile No, Phone'),
      ])
    })

    it('reads a Data field of Phone options as a Phone, from the page meta', () => {
      const meta = {
        fields: [
          {
            fieldname: 'mobile_no',
            label: 'Mobile No',
            fieldtype: 'Data',
            options: 'Phone',
          },
          {
            fieldname: 'email',
            label: 'Email',
            fieldtype: 'Data',
            options: 'Email',
          },
        ],
      }
      expect(phoneValues({ mobile_no: '111', email: 'a@b.c' }, meta)).toEqual([
        { value: '111', label: 'Mobile No' },
      ])
      expect(phoneValues(undefined, undefined)).toEqual([])
    })

    it('offers only the typed number on a record with no numbers', () => {
      const shell = shellOf({ mobile_no: '', phone: null })
      expect(makeACallAct.argument.options(shell, '')).toEqual([])
      expect(makeACallAct.argument.options(shell, '555 0100')).toHaveLength(1)
    })

    it('is as before off a record page', () => {
      const shell = { record: () => null }
      expect(makeACallAct.argument.options(shell, '')).toEqual([])
      expect(makeACallAct.argument.options(shell, '555 0100')).toHaveLength(1)
      expect(makeACallAct.argument.options({}, '555 0100')).toHaveLength(1)
    })
  })

  it.each([
    '',
    'ab',
    '12',
    'call me 555',
    '+',
    '---',
    '(((1-2-3',
    '1-800-FLOWERS',
    '1234567890123456',
  ])('offers no choice for %j', (query) => {
    expect(typedNumberOptions(query)).toEqual([])
  })

  it('starts the outgoing call to the number it was given', () => {
    const start = vi.fn()
    unregister = registerOutgoingStarter(start)
    makeACallAct.run({}, '+15550100')
    expect(start).toHaveBeenCalledWith('+15550100')
  })

  it('says so when the call window has not mounted yet', () => {
    expect(() => makeACallAct.run({}, '+15550100')).toThrow(/still loading/)
  })

  it('refuses to run without a number', () => {
    expect(() => makeACallAct.run({}, undefined)).toThrow()
  })
})

describe('the act name', () => {
  it('runs the act the shell registers under that name', () => {
    expect(MAKE_A_CALL).toBe(`shell.crm.${makeACallAct.name}`)
  })
})
