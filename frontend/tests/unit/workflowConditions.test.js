import { describe, expect, it } from 'vitest'
import {
  isFilterExpression,
  toExpression,
  toFilters,
} from '../../src/components/Settings/WorkflowAutomations/workflowConditions'

const fields = [
  { fieldname: 'status', fieldtype: 'Link' },
  { fieldname: 'organization', fieldtype: 'Data' },
  { fieldname: 'job_title', fieldtype: 'Data' },
  { fieldname: 'annual_revenue', fieldtype: 'Currency' },
  { fieldname: 'converted', fieldtype: 'Check' },
]

describe('building a condition from filters', () => {
  it('quotes text and leaves numbers bare', () => {
    expect(toExpression([['status', '=', 'Qualified']], fields)).toBe(
      'doc.status == "Qualified"',
    )
    expect(toExpression([['annual_revenue', '>=', '50000']], fields)).toBe(
      'doc.annual_revenue >= 50000',
    )
  })

  it('writes membership, presence and contains without builtins', () => {
    expect(toExpression([['status', 'in', ['New', 'Open']]], fields)).toBe(
      'doc.status in ["New", "Open"]',
    )
    expect(toExpression([['organization', 'is', 'set']], fields)).toBe(
      '(doc.organization or "") != ""',
    )
    expect(toExpression([['job_title', 'like', '%Head%']], fields)).toBe(
      '"head" in (doc.job_title or "").lower()',
    )
  })

  it('joins every filter with and', () => {
    expect(
      toExpression(
        [
          ['status', '=', 'Qualified'],
          ['converted', '=', 0],
        ],
        fields,
      ),
    ).toBe('doc.status == "Qualified" and doc.converted == 0')
  })

  it('escapes quotes in values', () => {
    expect(toExpression([['organization', '=', 'A "big" co']], fields)).toBe(
      'doc.organization == "A \\"big\\" co"',
    )
  })
})

describe('reading a condition back into filters', () => {
  it('round-trips what it generated', () => {
    const filters = [
      ['status', 'in', ['New', 'Open']],
      ['job_title', 'not like', 'intern'],
      ['organization', 'is', 'not set'],
    ]
    const expression = toExpression(filters, fields)

    expect(toFilters(expression)).toEqual(filters)
  })

  it('accepts the single quotes a Python-authored condition uses', () => {
    expect(toFilters("doc.status in ['New', 'Open']")).toEqual([
      ['status', 'in', ['New', 'Open']],
    ])
    expect(toFilters("doc.status == 'Qualified'")).toEqual([
      ['status', '=', 'Qualified'],
    ])
  })

  it('refuses anything filters cannot express', () => {
    expect(
      isFilterExpression('doc.email.split("@")[-1] not in ["a.com"]'),
    ).toBe(false)
    expect(
      isFilterExpression('context.get("event", {}).get("x") == "Matched"'),
    ).toBe(false)
    expect(toFilters('doc.status == "Qualified"')).not.toBeNull()
  })

  it('treats an empty condition as no filters', () => {
    expect(toFilters('')).toEqual([])
    expect(isFilterExpression('')).toBe(true)
  })
})
