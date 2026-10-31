import { describe, expect, it, vi } from 'vitest'
import {
  CONDITIONS,
  isLegacy,
  keepExpression,
  keepExpressions,
  parseConditions,
  placeConditions,
  refuseEmptyCondition,
  startOnEveryDay,
  switchToBuilder,
} from '../../../crm/fcrm/frontend/assignment_rule/assignmentRule.js'

const [assign, unassign] = CONDITIONS
const builder = { name: 'ConditionsField' }
const legacyNote = { name: 'LegacyCondition' }
const STATUS_OPEN = JSON.stringify([['status', 'equals', 'Open']])

function fakePage({ doc = {}, saved, ...overrides } = {}) {
  const fullDoc = { document_type: 'CRM Lead', ...doc }
  return {
    app: 'crm',
    doctype: 'Assignment Rule',
    isNew: false,
    doc: fullDoc,
    saved: saved ?? { ...fullDoc },
    fields: {
      update: vi.fn(),
      setError: vi.fn((fieldname, message) =>
        Object.assign(new Error(message), { fieldname }),
      ),
    },
    form: { add: vi.fn() },
    refresh: vi.fn(),
    ...overrides,
  }
}

function updatesFor(page, fieldname) {
  return page.fields.update.mock.calls
    .filter(([name]) => name === fieldname)
    .map(([, patch]) => patch)
}

describe('placeConditions', () => {
  it('puts the builder in the JSON field and hides the Python on a new CRM rule', () => {
    const page = fakePage({ isNew: true })
    placeConditions(page, { builder, legacyNote })
    for (const pair of CONDITIONS) {
      const [patch] = updatesFor(page, pair.json)
      expect(patch).toMatchObject({ hidden: false, component: builder })
      expect(patch.props).toEqual({
        page,
        python: pair.python,
        required: pair.required,
      })
      expect(updatesFor(page, pair.python)).toEqual([{ hidden: true }])
    }
    expect(page.form.add).not.toHaveBeenCalled()
  })

  it('leaves a rule with no JSON to frappe on /apps/desk', () => {
    const page = fakePage({ app: 'frappe' })
    placeConditions(page, { builder, legacyNote })
    expect(page.fields.update).not.toHaveBeenCalled()
  })

  it('puts the builder on a rule that holds its JSON in every app', () => {
    const page = fakePage({
      app: 'frappe',
      doc: {
        assign_condition_json: STATUS_OPEN,
        assign_condition: 'status == "Open"',
      },
    })
    placeConditions(page, { builder, legacyNote })
    expect(updatesFor(page, assign.json)).toHaveLength(1)
    expect(updatesFor(page, unassign.json)).toEqual([])
    expect(page.form.add).not.toHaveBeenCalled()
  })

  it('keeps a Python condition and puts the note above it', () => {
    const page = fakePage({ doc: { assign_condition: 'status == "Open"' } })
    placeConditions(page, { builder, legacyNote })
    expect(updatesFor(page, assign.json)).toEqual([])
    expect(updatesFor(page, assign.python)).toEqual([])
    expect(page.form.add).toHaveBeenCalledWith(
      {
        name: 'legacy_assign_condition',
        component: legacyNote,
        props: { pair: assign },
      },
      { before: 'assign_condition' },
    )
  })

  it('puts the note above the builder once the reader switches, until the save', () => {
    const page = fakePage({ doc: { assign_condition: 'status == "Open"' } })
    switchToBuilder(page, assign)
    placeConditions(page, { builder, legacyNote })
    expect(updatesFor(page, assign.json)).toHaveLength(1)
    expect(page.form.add).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'legacy_assign_condition' }),
      {
        before: 'assign_condition_json',
      },
    )
  })

  it('asks for a document type before the builder takes conditions', () => {
    const page = fakePage({ isNew: true, doc: { document_type: '' } })
    placeConditions(page, { builder, legacyNote })
    const [patch] = updatesFor(page, assign.json)
    expect(patch.description).toBe('Set the document type to add conditions.')
  })
})

describe('switchToBuilder', () => {
  it('drops the Python, so a save never keeps the old condition running', () => {
    const page = fakePage({ doc: { unassign_condition: 'status == "Closed"' } })
    switchToBuilder(page, unassign)
    expect(page.doc).toMatchObject({
      unassign_condition_json: '[]',
      unassign_condition: '',
    })
    expect(isLegacy(page.doc, unassign)).toBe(false)
    expect(page.refresh).toHaveBeenCalledOnce()
  })
})

describe('keepExpression', () => {
  const fields = [{ fieldname: 'status', fieldtype: 'Select' }]

  it('compiles the JSON with the target fields into the Python', async () => {
    const compile = vi.fn(() => 'status == "Open"')
    const fieldsOf = vi.fn(async () => fields)
    const page = fakePage({
      doc: { assign_condition_json: STATUS_OPEN, assign_condition: 'old' },
    })
    await keepExpression(page, assign, { fieldsOf, compile })
    expect(fieldsOf).toHaveBeenCalledWith('CRM Lead')
    expect(compile).toHaveBeenCalledWith(STATUS_OPEN, fields)
    expect(page.doc.assign_condition).toBe('status == "Open"')
  })

  it('compiles the JSON as it is when the fields arrive', async () => {
    const page = fakePage({ doc: { assign_condition_json: '[]' } })
    const fieldsOf = async () => {
      page.doc.assign_condition_json = STATUS_OPEN
      return fields
    }
    const compile = vi.fn(() => 'compiled')
    await keepExpression(page, assign, { fieldsOf, compile })
    expect(compile).toHaveBeenCalledWith(STATUS_OPEN, fields)
  })

  it('leaves a Python condition alone', async () => {
    const compile = vi.fn()
    const page = fakePage({ doc: { assign_condition: 'status == "Open"' } })
    await keepExpressions(page, { fieldsOf: async () => fields, compile })
    expect(compile).not.toHaveBeenCalled()
    expect(page.doc.assign_condition).toBe('status == "Open"')
  })
})

describe('startOnEveryDay', () => {
  it('fills all seven days on a new CRM rule', () => {
    const page = fakePage({ isNew: true })
    startOnEveryDay(page)
    expect(page.doc.assignment_days.map((row) => row.day)).toEqual([
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
      'Sunday',
    ])
  })

  it('keeps the days a duplicate brings, a saved rule and /apps/desk alone', () => {
    const copy = fakePage({
      isNew: true,
      doc: { assignment_days: [{ day: 'Monday' }] },
    })
    const saved = fakePage()
    const desk = fakePage({ isNew: true, app: 'frappe' })
    for (const page of [copy, saved, desk]) startOnEveryDay(page)
    expect(copy.doc.assignment_days).toEqual([{ day: 'Monday' }])
    expect(saved.doc.assignment_days).toBeUndefined()
    expect(desk.doc.assignment_days).toBeUndefined()
  })
})

describe('refuseEmptyCondition', () => {
  const complete = { assign_condition_json: STATUS_OPEN }

  it('passes a rule with a condition', () => {
    expect(() =>
      refuseEmptyCondition(fakePage({ doc: complete })),
    ).not.toThrow()
  })

  it('refuses an empty assign condition in the builder', () => {
    const page = fakePage({ doc: { ...complete, assign_condition_json: '[]' } })
    expect(() => refuseEmptyCondition(page)).toThrow(
      'Add at least one condition',
    )
    expect(page.fields.setError).toHaveBeenCalledWith(
      'assign_condition_json',
      'Add at least one condition',
    )
  })

  it('leaves a Python condition to the server', () => {
    const page = fakePage({
      doc: { ...complete, assign_condition_json: '', assign_condition: 'True' },
    })
    expect(() => refuseEmptyCondition(page)).not.toThrow()
  })
})

describe('parseConditions', () => {
  it('reads an empty or unreadable value as no conditions', () => {
    expect(parseConditions('')).toEqual([])
    expect(parseConditions('not json')).toEqual([])
    expect(parseConditions('{"a": 1}')).toEqual([])
    expect(parseConditions(STATUS_OPEN)).toEqual([['status', 'equals', 'Open']])
  })
})
