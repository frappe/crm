import {
  askFlowChips,
  briefActionLabel,
  briefActionRoute,
  briefAge,
  briefBadge,
  briefDetail,
  briefIcon,
  briefPerson,
  briefRoute,
  briefSummary,
  briefTitle,
  flowSessionUrl,
  shortAge,
  waitedFor,
} from '@/utils/brief'

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

  it('speaks for the team on the Team tab', () => {
    expect(briefSummary({ count: 7, team: true })).toBe(
      'Your team has 7 things that need you today.',
    )
  })

  it('says so when nothing is due', () => {
    expect(briefSummary({ count: 0 })).toBe('Nothing needs you today')
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

  it('replies on the channel the customer used', () => {
    const lead = { kind: 'waiting', doctype: 'CRM Lead', name: 'L1' }
    expect(briefActionRoute({ ...lead, channel: 'whatsapp' }).hash).toBe(
      '#whatsapp',
    )
    expect(briefActionRoute({ ...lead, channel: 'email' }).hash).toBe('#emails')
    expect(briefActionLabel(lead)).toBe('Reply')
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
