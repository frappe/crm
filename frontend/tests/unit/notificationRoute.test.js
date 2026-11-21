import { notificationRoute } from '@/utils/notificationRoute'

describe('notificationRoute', () => {
  it('opens the lead a notification refers to', () => {
    expect(
      notificationRoute({
        route_name: 'Lead',
        reference_name: 'CRM-LEAD-2026-00001',
        hash: '#activity',
      }),
    ).toEqual({
      name: 'Lead',
      params: { leadId: 'CRM-LEAD-2026-00001' },
      hash: '#activity',
    })
  })

  it('opens the deal a notification refers to', () => {
    expect(
      notificationRoute({
        route_name: 'Deal',
        reference_name: 'CRM-DEAL-2026-00001',
        hash: '#comments',
      }),
    ).toEqual({
      name: 'Deal',
      params: { dealId: 'CRM-DEAL-2026-00001' },
      hash: '#comments',
    })
  })

  it('opens the Tasks list for a task with no lead or deal', () => {
    // get_notifications still sends route_name "Lead" for such a task
    for (const reference_name of ['', null, undefined]) {
      expect(
        notificationRoute({ route_name: 'Lead', reference_name, hash: '' }),
      ).toEqual({
        name: 'Tasks',
      })
    }
  })
})
