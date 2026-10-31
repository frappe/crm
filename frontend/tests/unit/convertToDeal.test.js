import { describe, expect, it, vi } from 'vitest'
import {
  CONVERT_METHOD,
  convertLead,
  leadDefaults,
  placeConvertButton,
  requiredDealFields,
  saveBeforeConvert,
} from '../../../crm/fcrm/frontend/convert/convertToDeal.js'

function fakePage(overrides = {}) {
  return {
    docname: 'CRM-LEAD-0001',
    isNew: false,
    isDirty: false,
    header: { add: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    call: vi.fn(() => Promise.resolve('CRM-DEAL-0001')),
    ...overrides,
  }
}

describe('placeConvertButton', () => {
  it('adds a right-zone button after the status control, gated on write', () => {
    const page = fakePage()
    const run = () => {}
    placeConvertButton(page, { label: 'Convert to Deal', run })
    expect(page.header.add).toHaveBeenCalledWith(
      {
        name: 'convert_to_deal',
        zone: 'right',
        display: 'button',
        right: 'write',
        label: 'Convert to Deal',
        run,
      },
      { after: 'status' },
    )
  })

  it('adds nothing on a new lead', () => {
    const page = fakePage({ isNew: true })
    placeConvertButton(page, { label: 'Convert to Deal' })
    expect(page.header.add).not.toHaveBeenCalled()
  })
})

describe('requiredDealFields', () => {
  const meta = [
    {
      fieldname: 'status',
      fieldtype: 'Link',
      options: 'CRM Deal Status',
      label: 'Status',
      reqd: 1,
    },
    {
      fieldname: 'probability',
      fieldtype: 'Percent',
      label: 'Probability',
      reqd: 1,
      default: '10',
    },
    {
      fieldname: 'deal_value',
      fieldtype: 'Currency',
      label: 'Deal Value',
      reqd: 0,
    },
    {
      fieldname: 'organization',
      fieldtype: 'Link',
      options: 'CRM Organization',
      reqd: 1,
    },
    {
      fieldname: 'contacts',
      fieldtype: 'Table',
      options: 'CRM Contacts',
      reqd: 1,
    },
    {
      fieldname: 'custom_region',
      fieldtype: 'Data',
      label: 'Region',
      reqd: 1,
      depends_on: 'eval:1',
    },
  ]

  it('keeps the fields that are reqd without a default, as dialog fields', () => {
    expect(requiredDealFields(meta)).toEqual([
      {
        fieldname: 'status',
        fieldtype: 'Link',
        label: 'Status',
        options: 'CRM Deal Status',
        reqd: 1,
        depends_on: undefined,
        description: undefined,
      },
      {
        fieldname: 'custom_region',
        fieldtype: 'Data',
        label: 'Region',
        options: undefined,
        reqd: 1,
        depends_on: 'eval:1',
        description: undefined,
      },
    ])
  })

  it("leaves out the dialog's own Links and fields a dialog cannot draw", () => {
    const names = requiredDealFields(meta).map((field) => field.fieldname)
    expect(names).not.toContain('organization')
    expect(names).not.toContain('contacts')
  })

  it('answers empty for no meta', () => {
    expect(requiredDealFields(undefined)).toEqual([])
  })
})

describe('leadDefaults', () => {
  const fields = [
    { fieldname: 'status' },
    { fieldname: 'deal_owner' },
    { fieldname: 'custom_region' },
    { fieldname: 'industry' },
  ]

  it("fills each field from the lead's value of the same name, and deal_owner from lead_owner", () => {
    const lead = {
      status: 'New',
      lead_owner: 'a@example.com',
      custom_region: 'EU',
      industry: '',
    }
    expect(leadDefaults(lead, fields)).toEqual({
      deal_owner: 'a@example.com',
      custom_region: 'EU',
    })
  })
})

describe('saveBeforeConvert', () => {
  it('saves a lead with unsaved edits', async () => {
    const page = fakePage({ isDirty: true })
    await saveBeforeConvert(page)
    expect(page.save).toHaveBeenCalledOnce()
  })

  it('does not save a clean lead', async () => {
    const page = fakePage()
    await saveBeforeConvert(page)
    expect(page.save).not.toHaveBeenCalled()
  })
})

describe('convertLead', () => {
  it('sends the chosen organization and contact apart from the deal values', async () => {
    const page = fakePage()
    const deal = await convertLead(page, {
      organization: 'Acme',
      contact: 'Jane Doe',
      status: 'Qualification',
    })
    expect(deal).toBe('CRM-DEAL-0001')
    expect(page.call).toHaveBeenCalledWith(CONVERT_METHOD, {
      lead: 'CRM-LEAD-0001',
      deal: { status: 'Qualification' },
      existing_organization: 'Acme',
      existing_contact: 'Jane Doe',
    })
  })

  it('leaves blank Links to the server and drops empty deal values', async () => {
    const page = fakePage()
    await convertLead(page, {
      organization: null,
      contact: '',
      status: 'Won',
      custom_region: null,
    })
    expect(page.call).toHaveBeenCalledWith(CONVERT_METHOD, {
      lead: 'CRM-LEAD-0001',
      deal: { status: 'Won' },
      existing_organization: null,
      existing_contact: null,
    })
  })
})
