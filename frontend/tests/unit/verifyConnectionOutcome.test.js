import { describe, expect, it, vi } from 'vitest'
import { verifyConnection } from '../../../crm/fcrm/frontend/settings/verifyConnection/outcome.js'

const OTHER_SITE = {
  is_erpnext_in_different_site: 1,
  erpnext_site_url: 'https://erp.example.com',
  api_key: 'key',
  api_secret: '*****',
  erpnext_company: 'Acme',
}

/** The other ERPNext site: it answers with `companies`, or throws what v2 reports for a failed request. */
function site({ companies, failure, installed } = {}) {
  return {
    isInstalled: vi.fn(async () => installed),
    companies: vi.fn(async () => {
      if (failure) throw Object.assign(new Error(failure), { type: failure })
      return companies
    }),
  }
}

describe('verifyConnection on this site', () => {
  it('is verified when ERPNext is installed', async () => {
    const ask = site({ installed: true })
    const result = await verifyConnection({ is_erpnext_in_different_site: 0 }, ask)
    expect(result.state).toBe('verified')
    expect(ask.companies).not.toHaveBeenCalled()
  })

  it('says ERPNext is missing here when it is not installed', async () => {
    const result = await verifyConnection({}, site({ installed: false }))
    expect(result.state).toBe('wrong-site')
  })
})

describe('verifyConnection on another site', () => {
  it('is verified when the company is one the site returns', async () => {
    const result = await verifyConnection(
      OTHER_SITE,
      site({ companies: [{ company_name: 'Acme' }, { company_name: 'Beta' }] })
    )
    expect(result.state).toBe('verified')
    expect(result.title).toContain('https://erp.example.com')
  })

  it('names the wrong company and lists the ones found', async () => {
    const result = await verifyConnection(
      { ...OTHER_SITE, erpnext_company: 'Acm' },
      site({ companies: [{ company_name: 'Acme' }, { company_name: 'Beta' }] })
    )
    expect(result.state).toBe('wrong-company')
    expect(result.title).toContain('Acm')
    expect(result.companies).toEqual(['Acme', 'Beta'])
  })

  it('treats a missing company as a wrong one', async () => {
    const result = await verifyConnection(
      { ...OTHER_SITE, erpnext_company: '' },
      site({ companies: [{ company_name: 'Acme' }] })
    )
    expect(result.state).toBe('wrong-company')
    expect(result.companies).toEqual(['Acme'])
  })

  it.each(['ConnectionError', 'MissingSchema', 'Timeout', 'JSONDecodeError'])(
    'blames the URL when the request fails with %s',
    async (failure) => {
      expect((await verifyConnection(OTHER_SITE, site({ failure }))).state).toBe('wrong-url')
    }
  )

  it('blames the key when the site refuses the request', async () => {
    const result = await verifyConnection(OTHER_SITE, site({ failure: 'FrappeException' }))
    expect(result.state).toBe('wrong-key')
  })

  it('blames the key when the key sees no company', async () => {
    const result = await verifyConnection(OTHER_SITE, site({ companies: [] }))
    expect(result.state).toBe('wrong-key')
  })

  it('shows the message of a failure it does not know', async () => {
    const ask = site({})
    ask.companies = async () => {
      throw Object.assign(new Error('Server went away'), { type: 'OperationalError' })
    }
    const result = await verifyConnection(OTHER_SITE, ask)
    expect(result.state).toBe('failed')
    expect(result.description).toBe('Server went away')
  })

  it('names the missing field without asking the site', async () => {
    const ask = site({ companies: [] })
    const result = await verifyConnection({ ...OTHER_SITE, api_key: '', api_secret: '' }, ask)
    expect(result.state).toBe('incomplete')
    expect(result.description).toContain('API key, API secret')
    expect(ask.companies).not.toHaveBeenCalled()
  })
})
