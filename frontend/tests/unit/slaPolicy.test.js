import { describe, expect, it, vi } from 'vitest'

const listDocuments = vi.fn()

vi.mock('@framework/ui/api', () => ({ listDocuments }))

const { default: script } = await import(
  '../../../crm/fcrm/doctype/crm_service_level_agreement/frontend/record.js'
)

function fakePage(doc = {}, overrides = {}) {
  return {
    doctype: 'CRM Service Level Agreement',
    isNew: true,
    doc: { sla_name: 'SLA 45959', ...doc },
    fields: { setError: vi.fn((_, message) => new Error(message)) },
    ...overrides,
  }
}

describe('a new SLA policy', () => {
  it('starts with office hours and one priority per communication status', async () => {
    listDocuments.mockResolvedValueOnce({
      data: [{ name: 'Open' }, { name: 'Replied' }],
    })
    const page = fakePage()
    await script.onOpen(page)

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
    await script.onOpen(page)

    expect(listDocuments).not.toHaveBeenCalled()
    expect(page.doc.priorities).toBe(priorities)
    expect(page.doc.working_hours).toBe(working_hours)
  })

  it('does not overwrite priorities added while the statuses load', async () => {
    let answer
    listDocuments.mockReturnValueOnce(new Promise((resolve) => (answer = resolve)))
    const page = fakePage()
    const opening = script.onOpen(page)
    page.doc.priorities = [{ priority: 'Replied' }]
    answer({ data: [{ name: 'Open' }] })
    await opening

    expect(page.doc.priorities).toEqual([{ priority: 'Replied' }])
  })

  it('fills nothing on a saved policy', async () => {
    listDocuments.mockClear()
    const page = fakePage({}, { isNew: false })
    await script.onOpen(page)

    expect(listDocuments).not.toHaveBeenCalled()
    expect(page.doc.working_hours).toBeUndefined()
  })
})

describe('the default policy', () => {
  it('turns enabled on when set as default', () => {
    const page = fakePage({ default: 1, enabled: 0 })
    script.default(page)
    expect(page.doc.enabled).toBe(1)
  })

  it('leaves enabled alone when the default is cleared', () => {
    const page = fakePage({ default: 0, enabled: 0 })
    script.default(page)
    expect(page.doc.enabled).toBe(0)
  })

  it('refuses to save a disabled default', () => {
    const page = fakePage({ default: 1, enabled: 0 })
    expect(() => script.beforeSave(page)).toThrow(
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
    expect(() => script.beforeSave(page)).toThrow(
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
      expect(() => script.beforeSave(fakePage({ priorities }))).not.toThrow()
    }
  })
})
