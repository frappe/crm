import { beforeEach, describe, expect, it, vi } from 'vitest'

const runMethod = vi.fn()

vi.mock('@framework/ui/api', () => ({ runMethod }))

const { default: script } = await import(
  '../../../crm/fcrm/doctype/crm_holiday_list/frontend/record.js'
)

const LIST = {
  name: 'Holidays 45959',
  holiday_list_name: 'Holidays 45959',
  from_date: '2026-11-01',
  to_date: '2026-11-15',
  weekly_off: 'Sunday',
}

function fakePage(doc = {}, overrides = {}) {
  const items = []
  return {
    doctype: 'CRM Holiday List',
    isNew: false,
    doc: { ...LIST, ...doc },
    items,
    header: { add: vi.fn((added) => items.push(...added)) },
    fields: { hide: vi.fn(), setError: vi.fn() },
    ...overrides,
  }
}

function act(page, name) {
  script.onRefresh(page)
  return page.items.find((item) => item.name === name)
}

beforeEach(() => runMethod.mockReset())

describe('the holiday acts', () => {
  it('hide the inert buttons and take their place before Save', () => {
    const page = fakePage()
    script.onRefresh(page)

    expect(page.fields.hide).toHaveBeenCalledWith('add_to_holidays')
    expect(page.fields.hide).toHaveBeenCalledWith('clear_table')
    expect(page.header.add).toHaveBeenCalledWith(expect.any(Array), {
      before: 'save',
    })
    expect(page.items.map((item) => [item.name, item.right])).toEqual([
      ['add_to_holidays', 'write'],
      ['clear_table', 'write'],
    ])
  })

  it('need no record right on a new list', () => {
    const page = fakePage({}, { isNew: true })
    script.onRefresh(page)
    expect(page.items.every((item) => item.right === undefined)).toBe(true)
  })
})

describe('Add to Holidays', () => {
  it('appends the weekly offs the server finds after the rows already listed', async () => {
    const kept = { name: 'row1', date: '2026-11-03', description: 'Diwali' }
    const page = fakePage({ holidays: [kept] })
    runMethod.mockResolvedValueOnce({
      data: null,
      docs: [
        {
          holidays: [
            kept,
            {
              date: '2026-11-01',
              description: 'Sunday',
              weekly_off: 1,
              idx: 2,
              doctype: 'CRM Holiday',
            },
            {
              date: '2026-11-08',
              description: 'Sunday',
              weekly_off: 1,
              idx: 3,
            },
          ],
        },
      ],
    })
    await act(page, 'add_to_holidays').run(page)

    expect(runMethod).toHaveBeenCalledWith(
      'run_doc_method',
      {
        document: expect.objectContaining({
          doctype: 'CRM Holiday List',
          __islocal: 0,
          weekly_off: 'Sunday',
          holidays: [kept],
        }),
        method: 'get_weekly_off_dates',
      },
      { nullable: true },
    )
    expect(page.doc.holidays).toEqual([
      kept,
      { date: '2026-11-01', description: 'Sunday', weekly_off: 1 },
      { date: '2026-11-08', description: 'Sunday', weekly_off: 1 },
    ])
  })

  it('marks each missing field instead of asking the server', async () => {
    const page = fakePage({ weekly_off: '', to_date: null })
    await act(page, 'add_to_holidays').run(page)

    expect(runMethod).not.toHaveBeenCalled()
    expect(page.fields.setError.mock.calls.map(([field]) => field)).toEqual([
      'to_date',
      'weekly_off',
    ])
  })

  it('keeps a row added while the server answers', async () => {
    const page = fakePage({ holidays: [] })
    runMethod.mockImplementationOnce(async () => {
      page.doc.holidays = [{ date: '2026-11-05', description: 'Added' }]
      return {
        data: null,
        docs: [{ holidays: [{ date: '2026-11-01', description: 'Sunday' }] }],
      }
    })
    await act(page, 'add_to_holidays').run(page)

    expect(page.doc.holidays.map((row) => row.date)).toEqual([
      '2026-11-05',
      '2026-11-01',
    ])
  })
})

describe('Clear Table', () => {
  it('empties the holidays', () => {
    const page = fakePage({ holidays: [{ date: '2026-11-01' }] })
    act(page, 'clear_table').run(page)
    expect(page.doc.holidays).toEqual([])
  })
})
