import { reactive } from 'vue'

/**
 * Mirrors the actual setFieldProperty / removeFieldProperty / setFieldProperties
 * logic that will be added to script.js prototype methods.
 * Tests the override map manipulation in isolation.
 */

function setFieldProperty(ctx, target, property, value, rowName) {
  if (!ctx.fieldPropertyOverrides) ctx.fieldPropertyOverrides = {}
  const key = rowName ? `${target}:${rowName}` : target
  if (!ctx.fieldPropertyOverrides[key]) ctx.fieldPropertyOverrides[key] = {}
  ctx.fieldPropertyOverrides[key][property] = value
}

function setFieldProperties(ctx, target, properties, rowName) {
  for (const [key, value] of Object.entries(properties)) {
    setFieldProperty(ctx, target, key, value, rowName)
  }
}

function removeFieldProperty(ctx, target, property, rowName) {
  const key = rowName ? `${target}:${rowName}` : target
  if (!ctx.fieldPropertyOverrides?.[key]) return
  delete ctx.fieldPropertyOverrides[key][property]
  if (Object.keys(ctx.fieldPropertyOverrides[key]).length === 0) {
    delete ctx.fieldPropertyOverrides[key]
  }
}

function createCtx() {
  return reactive({ fieldPropertyOverrides: {} })
}

describe('fieldPropertyOverrides map operations', () => {
  // ─── setFieldProperty ─────────────────────────────────────────

  it('sets a single property on a field', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    expect(ctx.fieldPropertyOverrides.email.hidden).toBe(true)
  })

  it('sets multiple properties on the same field', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    setFieldProperty(ctx, 'email', 'label', 'Work Email')
    expect(ctx.fieldPropertyOverrides.email).toEqual({
      hidden: true,
      label: 'Work Email',
    })
  })

  it('overwrites a previously set property', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    setFieldProperty(ctx, 'email', 'hidden', false)
    expect(ctx.fieldPropertyOverrides.email.hidden).toBe(false)
  })

  it('sets properties on different fields independently', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    setFieldProperty(ctx, 'phone', 'read_only', true)
    expect(ctx.fieldPropertyOverrides.email).toEqual({ hidden: true })
    expect(ctx.fieldPropertyOverrides.phone).toEqual({ read_only: true })
  })

  it('handles string values', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'status', 'options', 'New\nOpen\nClosed')
    expect(ctx.fieldPropertyOverrides.status.options).toBe('New\nOpen\nClosed')
  })

  it('handles object values (link_filters)', () => {
    const ctx = createCtx()
    const filters = { company: 'ACME', enabled: 1 }
    setFieldProperty(ctx, 'contact', 'link_filters', filters)
    expect(ctx.fieldPropertyOverrides.contact.link_filters).toEqual(filters)
  })

  it('initializes fieldPropertyOverrides if missing', () => {
    const ctx = reactive({})
    setFieldProperty(ctx, 'x', 'hidden', true)
    expect(ctx.fieldPropertyOverrides.x.hidden).toBe(true)
  })

  // ─── setFieldProperties (batch) ────────────────────────────────

  it('sets multiple properties at once', () => {
    const ctx = createCtx()
    setFieldProperties(ctx, 'revenue', {
      hidden: false,
      read_only: true,
      label: 'Revenue (USD)',
    })
    expect(ctx.fieldPropertyOverrides.revenue).toEqual({
      hidden: false,
      read_only: true,
      label: 'Revenue (USD)',
    })
  })

  it('batch set merges with existing properties', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'x', 'hidden', true)
    setFieldProperties(ctx, 'x', { label: 'New', description: 'Help' })
    expect(ctx.fieldPropertyOverrides.x).toEqual({
      hidden: true,
      label: 'New',
      description: 'Help',
    })
  })

  // ─── removeFieldProperty ──────────────────────────────────────

  it('removes a single property', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    setFieldProperty(ctx, 'email', 'label', 'X')
    removeFieldProperty(ctx, 'email', 'hidden')
    expect(ctx.fieldPropertyOverrides.email).toEqual({ label: 'X' })
  })

  it('cleans up empty field key after last property removed', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    removeFieldProperty(ctx, 'email', 'hidden')
    expect(ctx.fieldPropertyOverrides.email).toBeUndefined()
  })

  it('is safe to call on non-existent field', () => {
    const ctx = createCtx()
    expect(() => removeFieldProperty(ctx, 'nope', 'hidden')).not.toThrow()
  })

  it('is safe to call on non-existent property', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'email', 'hidden', true)
    expect(() => removeFieldProperty(ctx, 'email', 'nope')).not.toThrow()
    // original property still there
    expect(ctx.fieldPropertyOverrides.email.hidden).toBe(true)
  })

  // ─── Dot notation (child table fields) ────────────────────────

  it('handles dot notation for child table fields', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'products.qty', 'read_only', true)
    expect(ctx.fieldPropertyOverrides['products.qty'].read_only).toBe(true)
  })

  it('removes dot notation overrides', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'products.qty', 'read_only', true)
    removeFieldProperty(ctx, 'products.qty', 'read_only')
    expect(ctx.fieldPropertyOverrides['products.qty']).toBeUndefined()
  })

  // ─── Section and tab names ────────────────────────────────────

  it('handles section names', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'details_section', 'hidden', true)
    expect(ctx.fieldPropertyOverrides.details_section.hidden).toBe(true)
  })

  it('handles tab names', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'advanced_tab', 'hidden', true)
    expect(ctx.fieldPropertyOverrides.advanced_tab.hidden).toBe(true)
  })

  it('section override with multiple properties', () => {
    const ctx = createCtx()
    setFieldProperties(ctx, 'notes_section', {
      collapsible: true,
      opened: false,
      label: 'Internal Notes',
    })
    expect(ctx.fieldPropertyOverrides.notes_section).toEqual({
      collapsible: true,
      opened: false,
      label: 'Internal Notes',
    })
  })

  // ─── Per-row overrides (4th param: rowName) ─────────────────

  it('sets per-row override with rowName', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'products.qty', 'read_only', true, 'row_abc')
    expect(ctx.fieldPropertyOverrides['products.qty:row_abc'].read_only).toBe(
      true,
    )
  })

  it('per-row and column-level overrides coexist', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'products.qty', 'read_only', true)
    setFieldProperty(ctx, 'products.qty', 'read_only', false, 'row_abc')
    expect(ctx.fieldPropertyOverrides['products.qty'].read_only).toBe(true)
    expect(ctx.fieldPropertyOverrides['products.qty:row_abc'].read_only).toBe(
      false,
    )
  })

  it('removes per-row override independently', () => {
    const ctx = createCtx()
    setFieldProperty(ctx, 'products.qty', 'read_only', true)
    setFieldProperty(ctx, 'products.qty', 'read_only', false, 'row_abc')
    removeFieldProperty(ctx, 'products.qty', 'read_only', 'row_abc')
    expect(ctx.fieldPropertyOverrides['products.qty:row_abc']).toBeUndefined()
    expect(ctx.fieldPropertyOverrides['products.qty'].read_only).toBe(true)
  })

  it('batch set with per-row', () => {
    const ctx = createCtx()
    setFieldProperties(
      ctx,
      'products.rate',
      { read_only: true, label: 'Fixed Rate' },
      'row_xyz',
    )
    expect(ctx.fieldPropertyOverrides['products.rate:row_xyz']).toEqual({
      read_only: true,
      label: 'Fixed Rate',
    })
  })
})
