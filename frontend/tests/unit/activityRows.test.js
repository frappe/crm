import { describe, expect, it, vi } from 'vitest'
import {
  activityItem,
  fetchActivityRows,
} from '../../../crm/fcrm/frontend/activity/activityRows.js'

vi.mock('frappe/i18n', () => ({
  __: (text, args = []) => text.replace(/\{(\d+)\}/g, (_, i) => args[i]),
}))

const Row = {}
const task = { doctype: 'CRM Task', key: 'task' }
const note = { doctype: 'FCRM Note', key: 'note' }
const call = { doctype: 'CRM Call Log', key: 'call' }

describe('fetchActivityRows', () => {
  const reads = (page) =>
    page.call.mock.calls.filter(
      ([method]) => method === 'frappe.client.get_list',
    )
  const pageFor = (doc, call) => ({
    doctype: 'CRM Deal',
    docname: 'D1',
    doc,
    call: vi.fn(call),
  })

  it("reads each source by the record's own name and the lead's, when the user can read the lead", async () => {
    const page = pageFor({ lead: 'L1' }, (method, args) =>
      Promise.resolve(
        method === 'frappe.client.has_permission'
          ? { has_permission: true }
          : [{ name: args.doctype }],
      ),
    )
    const rows = await fetchActivityRows(page)()
    expect(reads(page)).toHaveLength(3)
    expect(reads(page)[0][1].filters).toEqual({
      reference_doctype: ['in', ['CRM Deal', 'CRM Lead']],
      reference_docname: ['in', ['D1', 'L1']],
    })
    expect(rows.map((row) => row.source.key)).toEqual(['task', 'note', 'call'])
  })

  it("leaves out the lead's records when the user cannot read the lead", async () => {
    const page = pageFor({ lead: 'L1' }, (method) =>
      Promise.resolve(
        method === 'frappe.client.has_permission'
          ? { has_permission: false }
          : [],
      ),
    )
    await fetchActivityRows(page)()
    expect(reads(page)[0][1].filters.reference_docname).toEqual(['in', ['D1']])
  })

  it('draws no rows for a source the user cannot read, and lets any other failure reject', async () => {
    const refuse = pageFor({}, (method, args) =>
      args.doctype === 'FCRM Note'
        ? Promise.reject({ status: 403 })
        : Promise.resolve([{ name: args.doctype }]),
    )
    const rows = await fetchActivityRows(refuse)()
    expect(rows.map((row) => row.source.key)).toEqual(['task', 'call'])

    const broken = pageFor({}, () => Promise.reject(new Error('Network down')))
    await expect(fetchActivityRows(broken)()).rejects.toThrow('Network down')
  })
})

describe('activityItem', () => {
  it('places a task by its creation and tells its status, priority and due date', () => {
    const item = activityItem(
      {
        source: task,
        name: 'T1',
        title: 'Send quote',
        status: 'Todo',
        priority: 'High',
        due_date: '2026-11-10 09:00:00',
        creation: '2026-11-01 10:15:00.123456',
      },
      Row,
    )
    expect(item).toMatchObject({
      name: 'task:T1',
      timestamp: '2026-11-01 10:15:00',
      component: Row,
    })
    expect(item.props).toMatchObject({
      doctype: 'CRM Task',
      record: 'T1',
      title: 'Send quote',
      detail: 'Todo · High · Due 2026-11-10',
    })
  })

  it("titles a note without a title by its content's text", () => {
    const item = activityItem(
      {
        source: note,
        name: 'N1',
        title: '',
        content: '<p>Met <b>Ann</b></p>',
        creation: '2026-11-01 10:15:00',
      },
      Row,
    )
    expect(item.props.title).toBe('Met Ann')
  })

  it('places a call by its start and tells its direction, numbers and length', () => {
    const item = activityItem(
      {
        source: call,
        name: 'C1',
        type: 'Incoming',
        status: 'Completed',
        from: '+1',
        to: '+2',
        duration: 75,
        start_time: '2026-11-02 08:00:00',
        creation: '2026-11-03 08:00:00',
      },
      Row,
    )
    expect(item.timestamp).toBe('2026-11-02 08:00:00')
    expect(item.icon).toBe('lucide-phone-incoming')
    expect(item.props).toMatchObject({
      title: '+1 → +2',
      detail: 'Completed · 1m 15s',
    })
  })
})

describe('activityItem gutter icons', () => {
  const at = { creation: '2026-11-01 10:15:00' }

  it('takes the icons CRM v1 draws for a task, a note and a call', () => {
    expect(activityItem({ source: task, name: 'T1', ...at }, Row).icon).toBe(
      'lucide-circle-check-big',
    )
    expect(activityItem({ source: note, name: 'N1', ...at }, Row).icon).toBe(
      'lucide-file-text',
    )
    expect(
      activityItem({ source: call, name: 'C1', type: 'Outgoing', ...at }, Row)
        .icon,
    ).toBe('lucide-phone-outgoing')
  })

  it('shows a missed and a declined call by its outcome, not its direction', () => {
    const icon = (status) =>
      activityItem(
        { source: call, name: 'C1', type: 'Incoming', status, ...at },
        Row,
      ).icon
    expect(icon('No Answer')).toBe('lucide-phone-missed')
    expect(icon('Busy')).toBe('lucide-phone-off')
  })
})

describe('activityItem names', () => {
  it("keeps a task's numeric name as the string the row takes", () => {
    const item = activityItem(
      { source: task, name: 12, title: 'x', creation: '2026-11-01 10:15:00' },
      Row,
    )
    expect(item).toMatchObject({ name: 'task:12', props: { record: '12' } })
  })
})
