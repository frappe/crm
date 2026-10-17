import { normalizeLinkFilters, parseLinkFilters } from '@/utils/fieldTransforms'

describe('parseLinkFilters', () => {
  it('returns null for falsy input', () => {
    expect(parseLinkFilters(null)).toBeNull()
    expect(parseLinkFilters(undefined)).toBeNull()
    expect(parseLinkFilters('')).toBeNull()
    expect(parseLinkFilters(0)).toBeNull()
  })

  it('parses a valid JSON string', () => {
    expect(parseLinkFilters('{"company":"ACME"}')).toEqual({ company: 'ACME' })
  })

  it('returns object as-is if already an object', () => {
    const obj = { company: 'ACME', enabled: 1 }
    expect(parseLinkFilters(obj)).toBe(obj)
  })

  it('returns null for invalid JSON string', () => {
    expect(parseLinkFilters('not json')).toBeNull()
  })

  it('converts the stored list format to the search_link mapping format', () => {
    expect(
      parseLinkFilters('[["User","user_type","=","System User"]]'),
    ).toEqual({ user_type: ['=', 'System User'] })
  })

  it('converts an already-parsed list', () => {
    expect(
      parseLinkFilters([['CRM Lead Source', 'name', '!=', 'Web']]),
    ).toEqual({ name: ['!=', 'Web'] })
  })

  it('returns an empty mapping for an empty list', () => {
    expect(parseLinkFilters('[]')).toEqual({})
  })

  it('passes the context through for eval: conditions', () => {
    expect(
      parseLinkFilters('[["User","company","=","eval:doc.company"]]', {
        doc: { company: 'ACME' },
      }),
    ).toEqual({ company: ['=', 'ACME'] })
  })
})

describe('normalizeLinkFilters', () => {
  it('returns non-list input unchanged', () => {
    const obj = { company: 'ACME' }
    expect(normalizeLinkFilters(obj)).toBe(obj)
    expect(normalizeLinkFilters(null)).toBeNull()
  })

  it('handles multiple conditions', () => {
    expect(
      normalizeLinkFilters([
        ['User', 'user_type', '=', 'System User'],
        ['User', 'enabled', '=', 1],
      ]),
    ).toEqual({ user_type: ['=', 'System User'], enabled: ['=', 1] })
  })

  it('handles 3-tuple conditions without a doctype', () => {
    expect(
      normalizeLinkFilters([['status', 'in', ['Open', 'Replied']]]),
    ).toEqual({ status: ['in', ['Open', 'Replied']] })
  })

  it('handles a dynamic-link descriptor in place of the doctype', () => {
    expect(
      normalizeLinkFilters([
        [
          { fieldname: 'apply_on', field_option: 'DocType' },
          'name',
          'in',
          ['CRM Lead', 'CRM Deal'],
        ],
      ]),
    ).toEqual({ name: ['in', ['CRM Lead', 'CRM Deal']] })
  })

  it('evaluates eval: conditions against the doc', () => {
    expect(
      normalizeLinkFilters([['User', 'company', '=', 'eval:doc.company']], {
        doc: { company: 'ACME' },
      }),
    ).toEqual({ company: ['=', 'ACME'] })
  })

  it('exposes the parent doc to eval: conditions', () => {
    expect(
      normalizeLinkFilters(
        [['CRM Deal', 'organization', '=', 'eval:parent.organization']],
        { doc: {}, parent: { organization: 'Frappe' } },
      ),
    ).toEqual({ organization: ['=', 'Frappe'] })
  })

  it('skips eval: conditions that cannot be evaluated', () => {
    // no doc in context → `doc.company` throws → condition dropped
    expect(
      normalizeLinkFilters([
        ['User', 'company', '=', 'eval:doc.company'],
        ['User', 'enabled', '=', 1],
      ]),
    ).toEqual({ enabled: ['=', 1] })
  })

  it('skips malformed entries', () => {
    expect(
      normalizeLinkFilters([
        'not a condition',
        [],
        ['User', 'enabled', '=', 1],
      ]),
    ).toEqual({ enabled: ['=', 1] })
  })
})
