import {
  getFetchSource,
  getSourceFieldnames,
  getFieldsToFetch,
  getPendingFetchFields,
  isFetchedFromLink,
} from '@/utils/fetchFrom'

const fields = [
  { fieldname: 'organization', fieldtype: 'Link', options: 'CRM Organization' },
  { fieldname: 'website', fetch_from: 'organization.website' },
  { fieldname: 'territory', fetch_from: 'organization.territory' },
  {
    fieldname: 'industry',
    fetch_from: 'organization.industry',
    fetch_if_empty: 1,
  },
  { fieldname: 'annual_revenue', fetch_from: '.annual_revenue' },
  { fieldname: 'first_name' },
  { fieldname: 'email', fetch_from: 'contact.email_id' },
]

describe('getFetchSource', () => {
  it('splits a fetch_from into its link and source field', () => {
    expect(getFetchSource('organization.website')).toEqual({
      link: 'organization',
      source: 'website',
    })
  })

  it('takes the last segment as the source, like the server does', () => {
    expect(getFetchSource('a.b.c')).toEqual({ link: 'a', source: 'c' })
  })

  it('returns null when there is no link field to fetch from', () => {
    expect(getFetchSource('.website')).toBeNull()
    expect(getFetchSource('website')).toBeNull()
    expect(getFetchSource('organization.')).toBeNull()
    expect(getFetchSource('')).toBeNull()
    expect(getFetchSource(undefined)).toBeNull()
    expect(getFetchSource(null)).toBeNull()
    expect(getFetchSource(123)).toBeNull()
  })
})

describe('getFieldsToFetch', () => {
  it('picks the fields that hang off a link field', () => {
    expect(getFieldsToFetch(fields, 'organization').map((f) => f.fieldname)) //
      .toEqual(['website', 'territory', 'industry'])
  })

  it('ignores fields pointing at a different link', () => {
    expect(getFieldsToFetch(fields, 'contact').map((f) => f.fieldname)).toEqual(
      ['email'],
    )
  })

  it('skips a fetch_from with no link field, matching the server', () => {
    expect(getFieldsToFetch(fields, '')).toEqual([])
    expect(getFieldsToFetch(fields, 'annual_revenue')).toEqual([])
  })
})

describe('getPendingFetchFields', () => {
  it('fetches everything when the doc is empty', () => {
    expect(
      getPendingFetchFields(fields, 'organization', {}).map((f) => f.fieldname),
    ).toEqual(['website', 'territory', 'industry'])
  })

  it('leaves a fetch_if_empty field alone once it has a value', () => {
    const doc = { industry: 'Manufacturing' }
    expect(
      getPendingFetchFields(fields, 'organization', doc).map(
        (f) => f.fieldname,
      ),
    ).toEqual(['website', 'territory'])
  })

  it('still overwrites a plain fetched field that has a value', () => {
    const doc = { website: 'https://old.example.com' }
    expect(
      getPendingFetchFields(fields, 'organization', doc).map(
        (f) => f.fieldname,
      ),
    ).toEqual(['website', 'territory', 'industry'])
  })
})

describe('getSourceFieldnames', () => {
  it('returns the source fieldnames to ask the server for', () => {
    expect(
      getSourceFieldnames(getFieldsToFetch(fields, 'organization')),
    ).toEqual(['website', 'territory', 'industry'])
  })

  it('asks for a shared source only once', () => {
    const dupes = [
      { fieldname: 'a', fetch_from: 'org.website' },
      { fieldname: 'b', fetch_from: 'org.website' },
    ]
    expect(getSourceFieldnames(dupes)).toEqual(['website'])
  })
})

describe('isFetchedFromLink', () => {
  it('locks the field once its link has a value', () => {
    const field = { fetch_from: 'organization.website' }
    expect(isFetchedFromLink(field, { organization: 'Acme' })).toBe(true)
  })

  it('leaves the field editable while the link is empty', () => {
    const field = { fetch_from: 'organization.website' }
    expect(isFetchedFromLink(field, {})).toBe(false)
    expect(isFetchedFromLink(field, { organization: '' })).toBe(false)
    expect(isFetchedFromLink(field, { organization: null })).toBe(false)
  })

  it('leaves ordinary and malformed fields editable', () => {
    expect(isFetchedFromLink({ fieldname: 'first_name' }, {})).toBe(false)
    expect(
      isFetchedFromLink({ fetch_from: '.website' }, { website: 'x' }),
    ).toBe(false)
  })
})
