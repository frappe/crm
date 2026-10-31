import { describe, expect, it, vi } from 'vitest'
import {
  GUIDE,
  callRows,
  placeCallsSection,
} from '../../../crm/fcrm/frontend/form_script/v1Calls.js'

const V1Calls = { name: 'V1Calls' }
const SECTION = { label: 'V1 Calls', component: V1Calls }
const CALLS = [
  {
    name: 'row-1',
    line: 3,
    v1_call: 'onLoad()',
    verb: 'onOpen(page)',
    catalog_key: 'on-load',
    gap: null,
  },
  {
    name: 'row-2',
    line: 9,
    v1_call: 'toast.info',
    verb: 'No counterpart',
    catalog_key: 'toast-info',
    gap: 'https://github.com/frappe/frappe/issues/46005',
  },
  {
    name: 'row-3',
    line: 12,
    v1_call: 'onError()',
    verb: 'No counterpart',
    catalog_key: 'on-error',
    gap: 'No handler runs on a failed save',
  },
]

function fakePage(overrides = {}) {
  return {
    isNew: false,
    doc: { v1_calls: CALLS },
    panelSections: { add: vi.fn() },
    ...overrides,
  }
}

describe('callRows', () => {
  it('links each call to its guide section by catalog key', () => {
    const [onLoad] = callRows(CALLS)

    expect(onLoad).toEqual({
      name: 'row-1',
      line: 3,
      call: 'onLoad()',
      verb: 'onOpen(page)',
      guide: `${GUIDE}#on-load`,
      gap: null,
    })
  })

  it('gives a call with no counterpart no verb, and its gap issue as a link', () => {
    const [, toast] = callRows(CALLS)

    expect(toast.verb).toBeNull()
    expect(toast.guide).toBe(`${GUIDE}#toast-info`)
    expect(toast.gap).toEqual({
      url: 'https://github.com/frappe/frappe/issues/46005',
      label: 'frappe/frappe#46005',
    })
  })

  it('keeps a gap that is no issue as its reason', () => {
    const [, , onError] = callRows(CALLS)

    expect(onError.gap).toEqual({ label: 'No handler runs on a failed save' })
  })

  it('reads no calls as none', () => {
    expect(callRows(undefined)).toEqual([])
    expect(callRows([])).toEqual([])
  })
})

describe('placeCallsSection', () => {
  it('adds an open section with the calls', () => {
    const page = fakePage()
    placeCallsSection(page, SECTION)

    expect(page.panelSections.add).toHaveBeenCalledWith({
      name: 'v1_calls',
      opened: true,
      label: 'V1 Calls',
      component: V1Calls,
      props: { calls: callRows(CALLS) },
    })
  })

  it('adds the section with no calls for a script that has none', () => {
    const page = fakePage({ doc: {} })
    placeCallsSection(page, SECTION)

    expect(page.panelSections.add.mock.calls[0][0].props).toEqual({ calls: [] })
  })

  it('adds nothing on a new script', () => {
    const page = fakePage({ isNew: true })
    placeCallsSection(page, SECTION)

    expect(page.panelSections.add).not.toHaveBeenCalled()
  })
})
