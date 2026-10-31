import { describe, expect, it, vi } from 'vitest'
import {
  CONVERT_METHOD,
  convertLead,
  leadDefaults,
  placeConvertButton,
  requiredDealFields,
  toDialogField,
} from '../../../crm/fcrm/frontend/convert/convertToDeal.js'

function fakePage(overrides = {}) {
  return {
    docname: 'CRM-LEAD-0001',
    isNew: false,
    header: { add: vi.fn() },
    toast: { error: vi.fn() },
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

  it('keeps the fields that are reqd without a default', () => {
    expect(requiredDealFields(meta).map((field) => field.fieldname)).toEqual([
      'status',
      'custom_region',
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

describe('toDialogField', () => {
  it('forces the field mandatory and keeps what a dialog field may carry', () => {
    const field = {
      fieldname: 'custom_region',
      fieldtype: 'Data',
      label: 'Region',
      reqd: 1,
      depends_on: 'eval:1',
      in_list_view: 1,
    }
    expect(toDialogField(field)).toEqual({
      fieldname: 'custom_region',
      fieldtype: 'Data',
      label: 'Region',
      options: undefined,
      reqd: 1,
      depends_on: 'eval:1',
      description: undefined,
    })
  })
})

describe('leadDefaults', () => {
  const leadFields = [
    { fieldname: 'status' },
    { fieldname: 'lead_owner' },
    { fieldname: 'industry' },
    {
      fieldname: 'custom_lead_region',
      label: 'Region',
      fieldtype: 'Data',
      is_custom_field: 1,
    },
    {
      fieldname: 'custom_tier',
      label: 'Tier',
      fieldtype: 'Data',
      is_custom_field: 1,
    },
    {
      fieldname: 'custom_tier_2',
      label: 'Tier',
      fieldtype: 'Data',
      is_custom_field: 1,
    },
  ]
  const lead = {
    status: 'New',
    lead_owner: 'a@example.com',
    industry: '',
    custom_lead_region: 'EU',
    custom_tier: 'Gold',
    custom_tier_2: 'Silver',
  }
  const field = (fieldname, label, fieldtype = 'Data') => ({
    fieldname,
    label,
    fieldtype,
    is_custom_field: 1,
  })

  it('fills deal_owner from lead_owner and skips status and empty values', () => {
    const fields = [
      { fieldname: 'status' },
      { fieldname: 'deal_owner' },
      { fieldname: 'industry' },
    ]
    expect(leadDefaults(lead, leadFields, fields)).toEqual({
      deal_owner: 'a@example.com',
    })
  })

  it('fills a custom field from the one custom lead field of its label and type', () => {
    expect(
      leadDefaults(lead, leadFields, [field('custom_deal_region', 'Region')]),
    ).toEqual({
      custom_deal_region: 'EU',
    })
  })

  it('leaves a custom field empty when the label matches no lead field, or more than one', () => {
    const fields = [
      field('custom_deal_tier', 'Tier'),
      field('custom_size', 'Region', 'Int'),
    ]
    expect(leadDefaults(lead, leadFields, fields)).toEqual({})
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
