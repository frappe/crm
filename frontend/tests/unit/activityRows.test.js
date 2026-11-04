import { describe, expect, it, vi } from 'vitest'
import {
  activityItem,
  fetchActivityRows,
  referenceNames,
} from '../../../crm/fcrm/frontend/activity/activityRows.js'

vi.mock('frappe/i18n', () => ({
  __: (text, args = []) => text.replace(/\{(\d+)\}/g, (_, i) => args[i]),
}))

const Row = {}
const task = { doctype: 'CRM Task', key: 'task' }
const note = { doctype: 'FCRM Note', key: 'note' }
const call = { doctype: 'CRM Call Log', key: 'call' }

describe('referenceNames', () => {
  it("lists a deal's own name and its lead's", () => {
    expect(
      referenceNames({ docname: 'CRM-DEAL-1', doc: { lead: 'CRM-LEAD-1' } }),
    ).toEqual(['CRM-DEAL-1', 'CRM-LEAD-1'])
  })

  it('lists a lead by its own name', () => {
    expect(referenceNames({ docname: 'CRM-LEAD-1', doc: {} })).toEqual([
      'CRM-LEAD-1',
    ])
  })
})

describe('fetchActivityRows', () => {
  it('reads each source filtered by the names, and keeps the rows of a source the user can read', async () => {
    const page = {
      call: vi.fn((method, args) =>
        args.doctype === 'FCRM Note'
          ? Promise.reject(new Error('Not permitted'))
          : Promise.resolve([{ name: args.doctype }]),
      ),
    }
    const rows = await fetchActivityRows(page, ['A', 'B'])()
    expect(page.call).toHaveBeenCalledTimes(3)
    expect(page.call.mock.calls[0][1]).toMatchObject({
      filters: { reference_docname: ['in', ['A', 'B']] },
    })
    expect(rows.map((row) => [row.name, row.source.key])).toEqual([
      ['CRM Task', 'task'],
      ['CRM Call Log', 'call'],
    ])
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
    expect(item.props).toMatchObject({
      icon: 'lucide-phone-incoming',
      title: '+1 → +2',
      detail: 'Completed · 1m 15s',
    })
  })
})
