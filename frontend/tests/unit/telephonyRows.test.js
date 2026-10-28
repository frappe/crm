import { describe, expect, it } from 'vitest'
import { telephonyRows } from '../../../crm/fcrm/frontend/settings/telephonyRows.js'

describe('telephonyRows', () => {
  it('shows only mobile no. and device while no provider is on', () => {
    expect(telephonyRows({ twilio: false, exotel: false })).toEqual([
      'mobile_no',
      'call_receiving_device',
    ])
    expect(telephonyRows({})).toEqual(['mobile_no', 'call_receiving_device'])
  })

  it("shows the default medium and Twilio's number while only Twilio is on", () => {
    expect(telephonyRows({ twilio: true, exotel: false })).toEqual([
      'mobile_no',
      'default_medium',
      'call_receiving_device',
      'twilio_number',
    ])
  })

  it("shows the default medium and Exotel's number while only Exotel is on", () => {
    expect(telephonyRows({ twilio: false, exotel: true })).toEqual([
      'mobile_no',
      'default_medium',
      'call_receiving_device',
      'exotel_number',
    ])
  })

  it('shows every row while both are on', () => {
    expect(telephonyRows({ twilio: true, exotel: true })).toEqual([
      'mobile_no',
      'default_medium',
      'call_receiving_device',
      'twilio_number',
      'exotel_number',
    ])
  })
})
