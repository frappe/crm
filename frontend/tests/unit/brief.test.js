import {
  askFlowChips,
  briefActionIcon,
  briefActionLabel,
  briefActionRoute,
  briefAge,
  briefBadge,
  briefCount,
  briefDetail,
  briefEmptyLine,
  briefIcon,
  briefMoreLinks,
  briefOlderLinks,
  briefListQuery,
  briefPerson,
  briefRecordNames,
  briefRoute,
  briefSummary,
  briefTitle,
  flowSessionUrl,
  openFlowSession,
  shortAge,
  waitedFor,
} from '@/utils/brief'

import { setConfig } from 'frappe-ui'

const now = '2026-11-05 12:00:00'
const name = (user) => ({ r: 'Ravi Kumar', t: 'Tom Fischer' })[user] || user

describe('ages', () => {
  it('waitedFor counts days, then hours', () => {
    expect(waitedFor('2026-10-22 12:00:00', now)).toBe('14 days')
    expect(waitedFor('2026-11-04 11:00:00', now)).toBe('1 day')
    expect(waitedFor('2026-11-05 09:00:00', now)).toBe('3 hours')
  })

  it('shortAge moves from today to days to weeks', () => {
    expect(shortAge('2026-11-05 09:00:00', now)).toBe('Today')
    expect(shortAge('2026-10-22 12:00:00', now)).toBe('14 d')
    expect(shortAge('2026-10-15 12:00:00', now)).toBe('3 wk')
  })

  describe('in a time zone other than the system one', () => {
    beforeEach(() => {
      setConfig('systemTimezone', 'America/New_York')
      setConfig('localTimezone', 'Asia/Kolkata')
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2026-11-05T13:00:00Z'))
    })

    afterEach(() => {
      setConfig('systemTimezone', null)
      setConfig('localTimezone', null)
      vi.useRealTimers()
    })

    it('reads server times in the system time zone', () => {
      expect(waitedFor('2026-11-05 07:00:00')).toBe('1 hour')
    })
  })
})

describe('briefAge for late work', () => {
  it('counts hours when late by less than a day', () => {
    expect(
      briefAge(
        { kind: 'follow_up', status: 'Todo', due_date: '2020-01-14 07:00:00' },
        '2020-01-14 10:00:00',
      ),
    ).toEqual({ label: '3 h late', late: true })
  })

  it('counts an all-day follow-up from the day after its day', () => {
    expect(
      briefAge(
        {
          kind: 'follow_up',
          status: 'Todo',
          all_day: 1,
          due_date: '2020-01-13 00:00:00',
        },
        '2020-01-14 23:00:00',
      ),
    ).toEqual({ label: '1 d late', late: true })
  })
})

describe('briefSummary', () => {
  it('invites to Flow only when Flow is available', () => {
    expect(briefSummary({ count: 8, flow: true })).toBe(
      '8 things need you today. Or ask Flow to get something done.',
    )
    expect(briefSummary({ count: 8, flow: false })).toBe(
      '8 things need you today.',
    )
  })

  it('caps a large count at 500+', () => {
    expect(briefCount(500)).toBe(500)
    expect(briefCount(501)).toBe('500+')
    expect(briefSummary({ count: 2067, team: true })).toBe(
      'Your team has 500+ things that need you today.',
    )
  })

  it('speaks for the team on the Team tab', () => {
    expect(briefSummary({ count: 7, team: true })).toBe(
      'Your team has 7 things that need you today.',
    )
  })

  it('says so when nothing is due', () => {
    expect(briefSummary({ count: 0 })).toBe('Nothing needs you today')
  })
})

describe('briefMoreLinks', () => {
  it('links each list to the records the brief had no room for', () => {
    const links = briefMoreLinks({
      'CRM Deal': ['D-1'],
      'CRM Lead': ['L-1', 'L-2'],
    })
    expect(links.map((link) => link.label)).toEqual([
      '2 more leads',
      '1 more deal',
    ])
    expect(links[0].route).toEqual({
      name: 'Leads',
      query: { brief: 'L-1,L-2' },
    })
  })

  it('has nothing to link when everything is shown', () => {
    expect(briefMoreLinks({})).toEqual([])
    expect(briefMoreLinks()).toEqual([])
  })

  it('reads the names back from the link', () => {
    expect(briefRecordNames({ brief: 'L-1,L-2' })).toEqual(['L-1', 'L-2'])
    expect(briefRecordNames({})).toEqual([])
  })
})

describe('briefOlderLinks', () => {
  const labels = (links) => links.map((link) => link.label)

  it('names the older conversations and tasks', () => {
    const links = briefOlderLinks({
      older: { conversations: { Deal: 54 }, tasks: 98 },
      doctype: 'Deal',
      tab: 'mine',
    })
    expect(labels(links)).toEqual(['54 older conversations', '98 older tasks'])
  })

  it('uses the singular for one', () => {
    const links = briefOlderLinks({
      older: { conversations: { Lead: 1 }, tasks: 1 },
      doctype: 'Lead',
      tab: 'mine',
    })
    expect(labels(links)).toEqual(['1 older conversation', '1 older task'])
  })

  it('caps a large count', () => {
    const links = briefOlderLinks({ older: { tasks: 1200 }, tab: 'team' })
    expect(links[0].label).toBe('500+ older tasks')
  })

  it('gives leads and deals a link each with both types', () => {
    const links = briefOlderLinks({
      older: { conversations: { Lead: 3, Deal: 1 } },
      doctype: 'Both',
      tab: 'team',
    })
    expect(labels(links)).toEqual([
      '3 older lead conversations',
      '1 older deal conversation',
    ])
  })

  it('opens each list with the query for its names', () => {
    const links = briefOlderLinks({
      older: { conversations: { Lead: 3, Deal: 1 }, tasks: 2 },
      doctype: 'Both',
      tab: 'team',
    })
    expect(links.map((link) => link.route)).toEqual([
      {
        name: 'Leads',
        query: {
          brief_list: 'conversations',
          brief_tab: 'team',
          brief_doctype: 'Lead',
        },
      },
      {
        name: 'Deals',
        query: {
          brief_list: 'conversations',
          brief_tab: 'team',
          brief_doctype: 'Deal',
        },
      },
      { name: 'Tasks', query: { brief_list: 'tasks', brief_tab: 'team' } },
    ])
  })

  it('has no link when nothing is older', () => {
    expect(briefOlderLinks({ older: {}, tab: 'mine' })).toEqual([])
    expect(briefOlderLinks()).toEqual([])
  })
})

describe('briefListQuery', () => {
  it('reads the link back', () => {
    expect(
      briefListQuery({
        brief_list: 'conversations',
        brief_tab: 'mine',
        brief_doctype: 'Deal',
        view: 'x',
      }),
    ).toEqual({ kind: 'conversations', tab: 'mine', doctype: 'Deal' })
    expect(briefListQuery({ brief_list: 'tasks', brief_tab: 'team' })).toEqual({
      kind: 'tasks',
      tab: 'team',
    })
  })

  it('reads a member link back', () => {
    expect(
      briefListQuery({
        brief_list: 'behind',
        brief_tab: 'team',
        brief_doctype: 'Deal',
        brief_member: 'asha@x.com',
      }),
    ).toEqual({
      kind: 'behind',
      tab: 'team',
      doctype: 'Deal',
      member: 'asha@x.com',
    })
  })

  it('is empty without a list link', () => {
    expect(briefListQuery({})).toBeNull()
    expect(briefListQuery({ brief: 'L-1' })).toBeNull()
  })
})

describe('briefTitle', () => {
  it('tells an agent what to do', () => {
    expect(briefTitle({ kind: 'waiting', title: 'Penguin House' })).toBe(
      'Reply to Penguin House',
    )
    expect(briefTitle({ kind: 'no_next_step', title: 'Liam Müller' })).toBe(
      'Plan a follow-up for Liam Müller',
    )
  })

  it('joins new leads into one line', () => {
    expect(briefTitle({ kind: 'new', count: 3 })).toBe('Contact 3 new leads')
    expect(briefTitle({ kind: 'new', count: 1, title: 'Lumen' })).toBe(
      'Contact Lumen',
    )
  })

  it('names who has a client', () => {
    expect(
      briefTitle({ kind: 'client', title: 'Asteria', owner: 'r' }, { name }),
    ).toBe('Asteria is waiting on Ravi Kumar')
    expect(briefTitle({ kind: 'client', title: 'Asteria' }, { name })).toBe(
      'Asteria is waiting on a reply',
    )
  })

  it('counts people and leads with no owner', () => {
    expect(
      briefTitle({ kind: 'overdue_person', member: 'r', count: 3 }, { name }),
    ).toBe('Ravi Kumar has 3 overdue follow-ups')
    expect(briefTitle({ kind: 'ownerless', count: 4 })).toBe(
      'Assign 4 leads with no owner',
    )
    expect(
      briefTitle(
        { kind: 'workload', member: 'r', behind: 4, past_response: true },
        { name },
      ),
    ).toBe('Ravi Kumar has 4 records past response time')
  })
})

describe('briefDetail', () => {
  it('shows the last email', () => {
    const item = {
      kind: 'waiting',
      channel: 'email',
      last_email: { sender: 'Priya Nair', date: '21 Oct' },
    }
    expect(briefDetail(item)).toBe('Last email from Priya Nair on 21 Oct')
  })

  it('shows only the channel for WhatsApp', () => {
    expect(briefDetail({ kind: 'client', channel: 'whatsapp' })).toBe(
      'Last message on WhatsApp',
    )
  })

  it('gives the due date and record for a follow-up', () => {
    expect(
      briefDetail(
        { kind: 'follow_up', due_date: '23 Oct', reference_title: 'Bluestone' },
        { formatDue: (task) => task.due_date },
      ),
    ).toBe('Task due 23 Oct · Bluestone')
  })

  it('lists the new leads', () => {
    expect(briefDetail({ kind: 'new', names: ['Lumen', 'Sara'] })).toBe(
      'Assigned in the last 7 days · Lumen, Sara',
    )
  })

  it('names who has room when there is someone', () => {
    expect(
      briefDetail(
        { kind: 'workload', lightest: 't', lightest_open: 12 },
        { name },
      ),
    ).toBe('Tom Fischer has none and 12 open')
    expect(briefDetail({ kind: 'workload', lightest: null })).toBe('')
  })
})

describe('row parts', () => {
  it('picks the icon from the channel, then the kind', () => {
    expect(briefIcon({ kind: 'waiting', channel: 'whatsapp' })).toBe(
      'lucide-message-circle',
    )
    expect(briefIcon({ kind: 'waiting', channel: 'email' })).toBe('lucide-mail')
  })

  it('shows a person for team rows', () => {
    expect(briefPerson({ kind: 'client', owner: 'r' })).toBe('r')
    expect(briefPerson({ kind: 'overdue_person', member: 't' })).toBe('t')
    expect(briefPerson({ kind: 'waiting' })).toBeNull()
  })

  it('badges past SLA and high priority', () => {
    expect(briefBadge({ kind: 'waiting', past_response: 1 }).label).toBe(
      'Past SLA',
    )
    expect(briefBadge({ kind: 'waiting', past_response: 0 })).toBeNull()
    expect(briefBadge({ kind: 'workload', past_response: true })).toBeNull()
    expect(briefBadge({ kind: 'follow_up', priority: 'High' }).label).toBe(
      'High',
    )
  })

  it('shows a short age, in red when late', () => {
    expect(
      briefAge(
        { kind: 'waiting', awaiting_reply_since: '2026-10-22 12:00:00' },
        now,
      ),
    ).toEqual({ label: '14 d' })
    expect(
      briefAge(
        { kind: 'follow_up', status: 'Todo', due_date: '2020-01-01 10:00:00' },
        '2020-01-14 10:00:00',
      ),
    ).toEqual({ label: '13 d late', late: true })
    expect(briefAge({ kind: 'workload' })).toBeNull()
  })
})

describe('routes and actions', () => {
  it('opens the reference record for a follow-up', () => {
    expect(
      briefRoute({
        kind: 'follow_up',
        reference_doctype: 'CRM Deal',
        reference_docname: 'D1',
      }),
    ).toEqual({ name: 'Deal', params: { dealId: 'D1' } })
  })

  it('sends several new leads to the list', () => {
    expect(briefRoute({ kind: 'new', count: 3 })).toEqual({ name: 'Leads' })
  })

  it("opens a member's records past response time in their list", () => {
    const item = { kind: 'workload', member: 'asha@x.com', doctype: 'Deal' }
    expect(briefRoute(item)).toEqual({
      name: 'Deals',
      query: {
        brief_list: 'behind',
        brief_tab: 'team',
        brief_member: 'asha@x.com',
        brief_doctype: 'Deal',
      },
    })
    expect(briefActionLabel(item)).toBe('View deals')
    expect(briefActionLabel({ ...item, doctype: 'Lead' })).toBe('View leads')
  })

  it('names the count when the link leaves out the other record type', () => {
    const item = { kind: 'workload', doctype: 'Deal', behind: 3, linked: 2 }
    expect(briefActionLabel(item)).toBe('View 2 deals')
    expect(briefActionLabel({ ...item, doctype: 'Lead', linked: 1 })).toBe(
      'View 1 lead',
    )
    expect(briefActionLabel({ ...item, linked: 3 })).toBe('View deals')
  })

  it("opens a member's overdue follow-ups in Tasks", () => {
    expect(
      briefRoute({ kind: 'overdue_person', member: 'asha@x.com' }),
    ).toEqual({
      name: 'Tasks',
      query: {
        brief_list: 'overdue',
        brief_tab: 'team',
        brief_member: 'asha@x.com',
      },
    })
  })

  it('replies on the channel the customer used', () => {
    const lead = { kind: 'waiting', doctype: 'CRM Lead', name: 'L1' }
    expect(briefActionRoute({ ...lead, channel: 'whatsapp' }).hash).toBe(
      '#whatsapp',
    )
    expect(briefActionRoute({ ...lead, channel: 'email' }).hash).toBe('#emails')
    expect(briefActionLabel(lead)).toBe('Reply')
    expect(briefActionIcon(lead)).toBe('lucide-reply')
  })
})

describe('Ask Flow', () => {
  it('builds the chat address', () => {
    expect(flowSessionUrl('abc 1')).toBe('/flow/s/abc%201')
  })

  it('offers drafts only when someone is waiting', () => {
    expect(askFlowChips({ repliesWaiting: 3, now })[0]).toBe(
      'Draft replies for the 3 customers waiting on me',
    )
    expect(askFlowChips({ repliesWaiting: 0, now })[0]).toBe(
      'How did my pipeline do in October?',
    )
  })

  it('gives managers team questions', () => {
    expect(askFlowChips({ team: true })[0]).toBe(
      'Who on my team is behind on replies?',
    )
  })
})

describe('openFlowSession', () => {
  it('opens the session in the Flow panel when the page has one', () => {
    const flow = { open: vi.fn() }
    const assign = vi.fn()
    expect(openFlowSession('abc 1', { flow, assign })).toBe(true)
    expect(flow.open).toHaveBeenCalledWith({ session: 'abc 1' })
    expect(assign).not.toHaveBeenCalled()
  })

  it('opens the Flow page when the page has no panel', () => {
    const assign = vi.fn()
    expect(openFlowSession('abc', { flow: undefined, assign })).toBe(false)
    expect(assign).toHaveBeenCalledWith('/flow/s/abc')
  })

  it('opens the Flow page when Frappe has a panel but no open', () => {
    const assign = vi.fn()
    expect(openFlowSession('abc', { flow: { toggle() {} }, assign })).toBe(
      false,
    )
    expect(assign).toHaveBeenCalledWith('/flow/s/abc')
  })

  it('opens the Flow page when the panel throws', () => {
    const assign = vi.fn()
    const flow = {
      open: () => {
        throw new Error('panel failed')
      },
    }
    expect(openFlowSession('abc', { flow, assign })).toBe(false)
    expect(assign).toHaveBeenCalledWith('/flow/s/abc')
  })
})

describe('briefEmptyLine', () => {
  it('points a manager on For you to the team when it has work', () => {
    const line = briefEmptyLine({
      tab: 'mine',
      isManager: true,
      counts: { team: 4 },
    })
    expect(line).toEqual({
      text: 'Your team has 4 things to look at.',
      team: true,
    })
  })

  it('caps the team count', () => {
    const line = briefEmptyLine({
      tab: 'mine',
      isManager: true,
      counts: { team: 900 },
    })
    expect(line.text).toBe('Your team has 500+ things to look at.')
  })

  it('mentions older items when there are some', () => {
    const line = briefEmptyLine({
      tab: 'team',
      isManager: true,
      counts: { mine: 2 },
      older: { tasks: 3 },
    })
    expect(line).toEqual({
      text: 'Older items are waiting below if you have time.',
      team: false,
    })
  })

  it('says what will show up when there is nothing at all', () => {
    expect(briefEmptyLine({ tab: 'mine', isManager: false }).text).toBe(
      'New replies and follow-ups will show up here.',
    )
  })
})
