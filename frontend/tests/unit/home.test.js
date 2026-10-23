import {
  greetingFor,
  recordListViews,
  recordRoute,
  recordTitle,
} from '@/utils/home'

const at = (hour) => new Date(2026, 9, 23, hour)

describe('greetingFor', () => {
  it('follows the time of day', () => {
    expect(greetingFor(at(9), 'Asha')).toBe('Good morning, Asha')
    expect(greetingFor(at(13), 'Asha')).toBe('Good afternoon, Asha')
    expect(greetingFor(at(20), 'Asha')).toBe('Good evening, Asha')
  })

  it('works without a name', () => {
    expect(greetingFor(at(9))).toBe('Good morning')
  })
})

describe('home records', () => {
  it('routes leads and deals to their pages', () => {
    expect(recordRoute({ doctype: 'CRM Deal', name: 'D-1' })).toEqual({
      name: 'Deal',
      params: { dealId: 'D-1' },
    })
    expect(recordRoute({ doctype: 'CRM Lead', name: 'L-1' })).toEqual({
      name: 'Lead',
      params: { leadId: 'L-1' },
    })
  })

  it('links to the list views of the doctype setting', () => {
    const routes = (doctype) =>
      recordListViews(doctype).map((view) => view.route.name)
    expect(routes('Both')).toEqual(['Leads', 'Deals'])
    expect(routes('Deal')).toEqual(['Deals'])
  })

  it('falls back to the contact name and then the ID', () => {
    expect(
      recordTitle({ title: 'Stripe', subtitle: 'Casey Brown', name: 'D-1' }),
    ).toEqual({ title: 'Stripe', subtitle: 'Casey Brown' })
    expect(recordTitle({ subtitle: 'Casey Brown', name: 'D-1' })).toEqual({
      title: 'Casey Brown',
      subtitle: '',
    })
    expect(recordTitle({ name: 'D-1' })).toEqual({ title: 'D-1', subtitle: '' })
  })
})
