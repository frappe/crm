import { findMissingMandatory } from '@/utils/fieldTransforms'
import { leadFields } from '../fixtures/leadMeta'

describe('findMissingMandatory', () => {
  // ─── Basic mandatory checks ───────────────────────────────────

  it('catches missing required field', () => {
    const doc = { lead_name: '', status: 'New' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Lead Name')
  })

  it('does not flag filled required field', () => {
    const doc = { lead_name: 'John', status: 'New', priority: 'High' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).not.toContain('Lead Name')
    expect(missing).not.toContain('Status')
  })

  it('catches null value as missing', () => {
    const doc = { lead_name: null, status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Lead Name')
  })

  it('catches undefined value as missing', () => {
    const doc = { status: 'New', priority: 'Low' } // lead_name not present
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Lead Name')
  })

  it('catches whitespace-only string as missing', () => {
    const doc = { lead_name: '   ', status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Lead Name')
  })

  it('catches empty array as missing', () => {
    const doc = { lead_name: [], status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Lead Name')
  })

  it('returns empty array when all mandatory fields filled', () => {
    const doc = { lead_name: 'John', status: 'New', priority: 'High' }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toEqual([])
  })

  it('returns empty array for empty fields list', () => {
    expect(findMissingMandatory([], {})).toEqual([])
  })

  it('returns empty array for null fields', () => {
    expect(findMissingMandatory(null, {})).toEqual([])
  })

  it('returns empty array for null doc', () => {
    expect(findMissingMandatory(leadFields, null)).toEqual([])
  })

  // ─── Hidden fields ───────────────────────────────────────────

  it('skips hidden mandatory fields', () => {
    // lost_reason is hidden: 1 in meta — should be skipped even if reqd was set
    const fields = [
      { fieldname: 'x', label: 'X', reqd: 1, hidden: 1, fieldtype: 'Data' },
    ]
    const doc = { x: '' }
    const missing = findMissingMandatory(fields, doc)
    expect(missing).not.toContain('X')
  })

  // ─── Script overrides: reqd ───────────────────────────────────

  it('script override reqd=true makes non-required field mandatory', () => {
    const doc = { lead_name: 'John', status: 'New', priority: 'Low', email: '' }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { email: { reqd: true } },
    })
    expect(missing).toContain('Email')
  })

  it('script override reqd=false removes mandatory', () => {
    const doc = { lead_name: '', status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { lead_name: { reqd: false } },
    })
    expect(missing).not.toContain('Lead Name')
  })

  // ─── Script overrides: hidden ─────────────────────────────────

  it('script override hidden=true skips mandatory check', () => {
    const doc = { lead_name: '', status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { lead_name: { hidden: true } },
    })
    expect(missing).not.toContain('Lead Name')
  })

  it('script override hidden=false on originally-hidden field re-enables check', () => {
    // lost_reason is hidden:1 in meta and not reqd
    // Script un-hides it AND makes it reqd
    const doc = {
      lead_name: 'John',
      status: 'Lost',
      priority: 'Low',
      lost_reason: '',
    }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { lost_reason: { hidden: false, reqd: true } },
    })
    expect(missing).toContain('Lost Reason')
  })

  // ─── Combined overrides ───────────────────────────────────────

  it('hidden override wins — hidden+reqd via override skips check', () => {
    const doc = { lead_name: '', status: 'New', priority: 'Low' }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { lead_name: { hidden: true, reqd: true } },
    })
    // hidden takes priority — field is not validated
    expect(missing).not.toContain('Lead Name')
  })

  // ─── mandatory_depends_on ─────────────────────────────────────

  it('evaluates mandatory_depends_on expression', () => {
    // website has mandatory_depends_on: eval:doc.source === "Website"
    const doc = {
      lead_name: 'John',
      status: 'New',
      priority: 'High',
      source: 'Website',
      website: '',
    }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).toContain('Website')
  })

  it('mandatory_depends_on not triggered when condition false', () => {
    const doc = {
      lead_name: 'John',
      status: 'New',
      priority: 'High',
      source: 'Referral',
      website: '',
    }
    const missing = findMissingMandatory(leadFields, doc)
    expect(missing).not.toContain('Website')
  })

  it('script override reqd wins over mandatory_depends_on', () => {
    // Even though source is not "Website", script forces reqd
    const doc = {
      lead_name: 'John',
      status: 'New',
      priority: 'High',
      source: 'Referral',
      website: '',
    }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { website: { reqd: true } },
    })
    expect(missing).toContain('Website')
  })

  it('script override reqd=false overrides mandatory_depends_on', () => {
    const doc = {
      lead_name: 'John',
      status: 'New',
      priority: 'High',
      source: 'Website',
      website: '',
    }
    const missing = findMissingMandatory(leadFields, doc, {
      propertyOverrides: { website: { reqd: false } },
    })
    expect(missing).not.toContain('Website')
  })

  // ─── Uses label fallback ──────────────────────────────────────

  it('uses fieldname if label is missing', () => {
    const fields = [{ fieldname: 'custom_field', reqd: 1, fieldtype: 'Data' }]
    const doc = { custom_field: '' }
    const missing = findMissingMandatory(fields, doc)
    expect(missing).toContain('custom_field')
  })
})
