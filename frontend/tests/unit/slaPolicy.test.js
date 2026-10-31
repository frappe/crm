import { describe, expect, it, vi } from 'vitest'

const listDocuments = vi.fn()

vi.mock('@framework/ui/api', () => ({ listDocuments }))

const {
  SLA_CONDITION,
  enableDefaultPolicy,
  refuseBadDefaults,
  startNewPolicy,
} = await import('../../../crm/fcrm/frontend/sla/slaPolicy.js')
const { keepExpression, placeConditions } = await import(
  '../../../crm/fcrm/frontend/conditions/conditions.js'
)

function fakePage(doc = {}, overrides = {}) {
  return {
    doctype: 'CRM Service Level Agreement',
    isNew: true,
    doc: { sla_name: 'SLA 45959', ...doc },
    app: 'crm',
    fields: {
      update: vi.fn(),
      setError: vi.fn((_, message) => new Error(message)),
    },
    form: { add: vi.fn() },
    ...overrides,
  }
}

describe('a new SLA policy', () => {
  it('starts with office hours and one priority per communication status', async () => {
    listDocuments.mockResolvedValueOnce({
      data: [{ name: 'Open' }, { name: 'Replied' }],
    })
    const page = fakePage()
    await startNewPolicy(page)

    expect(listDocuments).toHaveBeenCalledWith(
      'CRM Communication Status',
      expect.objectContaining({ order_by: 'creation asc' }),
    )
    expect(page.doc.priorities).toEqual([
      { priority: 'Open', first_response_time: 3600, default_priority: 1 },
      { priority: 'Replied', first_response_time: 3600, default_priority: 0 },
    ])
    expect(page.doc.working_hours.map((row) => row.workday)).toEqual([
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
    ])
    expect(page.doc.working_hours[0]).toMatchObject({
      start_time: '09:00:00',
      end_time: '17:00:00',
    })
  })

  it('keeps the rows a duplicate brings', async () => {
    listDocuments.mockClear()
    const priorities = [{ priority: 'Open', default_priority: 1 }]
    const working_hours = [{ workday: 'Sunday' }]
    const page = fakePage({ priorities, working_hours })
    await startNewPolicy(page)

    expect(listDocuments).not.toHaveBeenCalled()
    expect(page.doc.priorities).toBe(priorities)
    expect(page.doc.working_hours).toBe(working_hours)
  })

  it('does not overwrite priorities added while the statuses load', async () => {
    let answer
    listDocuments.mockReturnValueOnce(
      new Promise((resolve) => (answer = resolve)),
    )
    const page = fakePage()
    const opening = startNewPolicy(page)
    page.doc.priorities = [{ priority: 'Replied' }]
    answer({ data: [{ name: 'Open' }] })
    await opening

    expect(page.doc.priorities).toEqual([{ priority: 'Replied' }])
  })

  it('fills nothing on a saved policy', async () => {
    listDocuments.mockClear()
    const page = fakePage({}, { isNew: false })
    await startNewPolicy(page)

    expect(listDocuments).not.toHaveBeenCalled()
    expect(page.doc.working_hours).toBeUndefined()
  })
})

describe('the default policy', () => {
  it('turns enabled on when set as default', () => {
    const page = fakePage({ default: 1, enabled: 0 })
    enableDefaultPolicy(page)
    expect(page.doc.enabled).toBe(1)
  })

  it('leaves enabled alone when the default is cleared', () => {
    const page = fakePage({ default: 0, enabled: 0 })
    enableDefaultPolicy(page)
    expect(page.doc.enabled).toBe(0)
  })

  it('refuses to save a disabled default', () => {
    const page = fakePage({ default: 1, enabled: 0 })
    expect(() => refuseBadDefaults(page)).toThrow(
      'An SLA set as default cannot be disabled',
    )
    expect(page.fields.setError).toHaveBeenCalledWith(
      'enabled',
      'An SLA set as default cannot be disabled',
    )
  })
})

describe('the default priority', () => {
  it('refuses two default priorities', () => {
    const page = fakePage({
      priorities: [
        { priority: 'Open', default_priority: 1 },
        { priority: 'Replied', default_priority: 1 },
      ],
    })
    expect(() => refuseBadDefaults(page)).toThrow(
      'There can only be one default priority',
    )
    expect(page.fields.setError).toHaveBeenCalledWith(
      'priorities',
      'There can only be one default priority',
    )
  })

  it('saves with one default priority, or none', () => {
    for (const flags of [
      [1, 0],
      [0, 0],
    ]) {
      const priorities = flags.map((default_priority) => ({ default_priority }))
      expect(() => refuseBadDefaults(fakePage({ priorities }))).not.toThrow()
    }
  })
})

describe('the condition', () => {
  const builder = { name: 'ConditionsField' }

  it('builds on the Apply On doctype', () => {
    const page = fakePage({ apply_on: 'CRM Deal' })
    placeConditions(page, [SLA_CONDITION], { builder, legacyNote: {} })
    expect(page.fields.update).toHaveBeenCalledWith(
      'condition_json',
      expect.objectContaining({
        component: builder,
        description: 'Choose which CRM Deal this SLA applies to.',
        props: expect.objectContaining({ doctypeField: 'apply_on' }),
      }),
    )
    expect(page.fields.update).toHaveBeenCalledWith('condition', {
      hidden: true,
    })
  })

  it('asks for Apply On before the builder takes conditions', () => {
    const page = fakePage()
    placeConditions(page, [SLA_CONDITION], { builder, legacyNote: {} })
    const [, patch] = page.fields.update.mock.calls[0]
    expect(patch.description).toBe('Set Apply On to add conditions.')
  })

  it('compiles against the Apply On fields with the record as `doc`', async () => {
    const json = JSON.stringify([['status', 'equals', 'New']])
    const page = fakePage({ apply_on: 'CRM Lead', condition_json: json })
    const fieldsOf = vi.fn(async () => [])
    const compile = vi.fn(
      (json, fields, pair) => `${pair.fieldPrefix}.status == "New"`,
    )
    await keepExpression(page, SLA_CONDITION, { fieldsOf, compile })
    expect(fieldsOf).toHaveBeenCalledWith('CRM Lead')
    expect(page.doc.condition).toBe('doc.status == "New"')
  })
})
