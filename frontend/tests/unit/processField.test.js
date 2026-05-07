import { processField } from '@/utils/fieldTransforms'

describe('processField', () => {
  // ─── Cloning ──────────────────────────────────────────────────

  it('returns a new object, not the original', () => {
    const raw = { fieldname: 'status', fieldtype: 'Data', label: 'Status' }
    const result = processField(raw)
    expect(result).not.toBe(raw)
  })

  it('does not mutate the original field', () => {
    const raw = {
      fieldname: 'status',
      fieldtype: 'Select',
      options: 'New\nOpen',
    }
    processField(raw)
    expect(raw.options).toBe('New\nOpen')
    expect(raw.fieldtype).toBe('Select')
  })

  it('does not mutate the original when overrides are applied', () => {
    const raw = { fieldname: 'x', fieldtype: 'Data', label: 'Original' }
    processField(raw, { propertyOverrides: { x: { label: 'Changed' } } })
    expect(raw.label).toBe('Original')
  })

  it('returns null for null input', () => {
    expect(processField(null)).toBeNull()
  })

  it('returns null for undefined input', () => {
    expect(processField(undefined)).toBeNull()
  })

  // ─── Select option transform ──────────────────────────────────

  it('converts Select options string to {label,value} array', () => {
    const raw = {
      fieldname: 'status',
      fieldtype: 'Select',
      options: 'New\nOpen\nClosed',
    }
    const result = processField(raw)
    expect(result.options).toEqual([
      { label: '', value: '' },
      { label: 'New', value: 'New' },
      { label: 'Open', value: 'Open' },
      { label: 'Closed', value: 'Closed' },
    ])
  })

  it('prepends blank option for non-required Select', () => {
    const raw = {
      fieldname: 'priority',
      fieldtype: 'Select',
      options: 'Low\nHigh',
    }
    const result = processField(raw)
    expect(result.options[0]).toEqual({ label: '', value: '' })
    expect(result.options).toHaveLength(3)
  })

  it('skips blank option for required Select', () => {
    const raw = {
      fieldname: 'status',
      fieldtype: 'Select',
      options: 'New\nOpen',
      reqd: 1,
    }
    const result = processField(raw)
    expect(result.options[0]).toEqual({ label: 'New', value: 'New' })
    expect(result.options).toHaveLength(2)
  })

  it('does not prepend blank when first option is already blank', () => {
    const raw = { fieldname: 'x', fieldtype: 'Select', options: '\nA\nB' }
    const result = processField(raw)
    expect(result.options[0]).toEqual({ label: '', value: '' })
    // should NOT have two blanks
    expect(result.options.filter((o) => o.value === '')).toHaveLength(1)
  })

  it('handles single option Select', () => {
    const raw = { fieldname: 'x', fieldtype: 'Select', options: 'Only' }
    const result = processField(raw)
    expect(result.options).toEqual([
      { label: '', value: '' },
      { label: 'Only', value: 'Only' },
    ])
  })

  it('handles empty options string', () => {
    const raw = { fieldname: 'x', fieldtype: 'Select', options: '' }
    const result = processField(raw)
    // '' split by \n gives [''] — first value is '' so no blank prepended
    expect(result.options).toEqual([{ label: '', value: '' }])
  })

  it('does not transform if options is already an array', () => {
    const opts = [{ label: 'A', value: 'A' }]
    const raw = { fieldname: 'x', fieldtype: 'Select', options: opts }
    const result = processField(raw)
    expect(result.options).toEqual(opts)
  })

  it('does not transform options for non-Select field types', () => {
    const raw = { fieldname: 'x', fieldtype: 'Data', options: 'Email' }
    const result = processField(raw)
    expect(result.options).toBe('Email')
  })

  // ─── Link→User transform ─────────────────────────────────────

  it('transforms Link with options=User to fieldtype User', () => {
    const raw = { fieldname: 'owner', fieldtype: 'Link', options: 'User' }
    const result = processField(raw)
    expect(result.fieldtype).toBe('User')
    // original untouched
    expect(raw.fieldtype).toBe('Link')
  })

  it('does not transform Link with other options', () => {
    const raw = { fieldname: 'org', fieldtype: 'Link', options: 'Organization' }
    const result = processField(raw)
    expect(result.fieldtype).toBe('Link')
    expect(result.options).toBe('Organization')
  })

  it('does not transform non-Link field types', () => {
    const raw = { fieldname: 'x', fieldtype: 'Data', options: 'User' }
    const result = processField(raw)
    expect(result.fieldtype).toBe('Data')
  })

  // ─── Perm overrides ──────────────────────────────────────────

  it('applies perm overrides', () => {
    const raw = { fieldname: 'salary', fieldtype: 'Currency', read_only: 0 }
    const result = processField(raw, {
      permOverrides: { salary: { read_only: 1 } },
    })
    expect(result.read_only).toBe(1)
  })

  it('perm overrides do not mutate original', () => {
    const raw = { fieldname: 'salary', fieldtype: 'Currency', read_only: 0 }
    processField(raw, { permOverrides: { salary: { read_only: 1 } } })
    expect(raw.read_only).toBe(0)
  })

  // ─── Script property overrides ────────────────────────────────

  it('applies script property overrides', () => {
    const raw = {
      fieldname: 'email',
      fieldtype: 'Data',
      hidden: 0,
      label: 'Email',
    }
    const result = processField(raw, {
      propertyOverrides: { email: { hidden: 1, label: 'Work Email' } },
    })
    expect(result.hidden).toBe(1)
    expect(result.label).toBe('Work Email')
  })

  it('script overrides win over perm overrides', () => {
    const raw = { fieldname: 'salary', fieldtype: 'Currency', read_only: 0 }
    const result = processField(raw, {
      permOverrides: { salary: { read_only: 1 } },
      propertyOverrides: { salary: { read_only: 0 } },
    })
    expect(result.read_only).toBe(0)
  })

  it('script overrides win over raw field values', () => {
    const raw = { fieldname: 'x', fieldtype: 'Data', label: 'Old', hidden: 0 }
    const result = processField(raw, {
      propertyOverrides: { x: { label: 'New', hidden: true } },
    })
    expect(result.label).toBe('New')
    expect(result.hidden).toBe(true)
  })

  it('unrelated overrides do not affect the field', () => {
    const raw = { fieldname: 'email', fieldtype: 'Data', label: 'Email' }
    const result = processField(raw, {
      propertyOverrides: { other_field: { hidden: true } },
    })
    expect(result.label).toBe('Email')
    expect(result.hidden).toBeUndefined()
  })

  // ─── Override changes Select options ──────────────────────────

  it('override can replace Select options string', () => {
    const raw = { fieldname: 'status', fieldtype: 'Select', options: 'A\nB' }
    const result = processField(raw, {
      propertyOverrides: { status: { options: 'X\nY\nZ' } },
    })
    expect(result.options).toEqual([
      { label: '', value: '' },
      { label: 'X', value: 'X' },
      { label: 'Y', value: 'Y' },
      { label: 'Z', value: 'Z' },
    ])
  })

  it('override reqd affects blank option prepending', () => {
    const raw = {
      fieldname: 'status',
      fieldtype: 'Select',
      options: 'A\nB',
      reqd: 0,
    }
    const result = processField(raw, {
      propertyOverrides: { status: { reqd: 1 } },
    })
    // reqd=1 from override → no blank option
    expect(result.options[0]).toEqual({ label: 'A', value: 'A' })
  })

  // ─── Combined transforms ─────────────────────────────────────

  it('applies overrides before Select transform', () => {
    // Override changes options string, then transform converts to array
    const raw = { fieldname: 's', fieldtype: 'Select', options: 'Old1\nOld2' }
    const result = processField(raw, {
      propertyOverrides: { s: { options: 'New1\nNew2\nNew3' } },
    })
    expect(result.options).toHaveLength(4) // blank + 3
    expect(result.options[1].value).toBe('New1')
  })

  it('preserves non-overridden properties', () => {
    const raw = {
      fieldname: 'x',
      fieldtype: 'Data',
      label: 'X',
      description: 'Help text',
      placeholder: 'Enter X',
    }
    const result = processField(raw, {
      propertyOverrides: { x: { label: 'Y' } },
    })
    expect(result.label).toBe('Y')
    expect(result.description).toBe('Help text')
    expect(result.placeholder).toBe('Enter X')
  })
})
