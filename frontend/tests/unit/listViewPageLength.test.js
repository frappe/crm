import { describe, it, expect, vi, beforeAll } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// utils/view.js resolves the views store at module scope.
vi.mock('frappe-ui', () => ({
  createResource: () => ({ data: [], reload() {}, promise: Promise.resolve() }),
}))

let DEFAULT_PAGE_LENGTH, resolvePageLength

beforeAll(async () => {
  setActivePinia(createPinia())
  ;({ DEFAULT_PAGE_LENGTH, resolvePageLength } = await import('@/utils/view'))
})

describe('resolvePageLength', () => {
  it('defaults when the list has no previous response to read', () => {
    // The cold-load case behind #2835.
    expect(resolvePageLength(undefined)).toBe(DEFAULT_PAGE_LENGTH)
    expect(resolvePageLength(null)).toBe(DEFAULT_PAGE_LENGTH)
  })

  it('keeps a page size the server already reported', () => {
    expect(resolvePageLength(40)).toBe(40)
    expect(resolvePageLength('60')).toBe(60)
  })

  it('rejects anything that cannot be sent as a positive int', () => {
    expect(resolvePageLength(NaN)).toBe(DEFAULT_PAGE_LENGTH)
    expect(resolvePageLength(0)).toBe(DEFAULT_PAGE_LENGTH)
    expect(resolvePageLength(-20)).toBe(DEFAULT_PAGE_LENGTH)
  })
})

describe('Load More on a cold list view', () => {
  // Regression for #2835: the first Load More after opening a view sent
  // page_length as null and get_data raised FrappeTypeError.
  it('advances 20 -> 40 -> 60 and never serialises null', () => {
    const params = {
      page_length: resolvePageLength(undefined),
      page_length_count: resolvePageLength(undefined),
    }
    expect(params.page_length).toBe(20)

    const sent = []
    const clickLoadMore = () => {
      // Mirrors updatePageLength(value, loadMore = true) in ViewControls.vue.
      params.page_length += params.page_length_count
      sent.push(JSON.parse(JSON.stringify(params)).page_length)
    }

    clickLoadMore()
    clickLoadMore()

    expect(sent).toEqual([40, 60])
    expect(sent).not.toContain(null)
  })
})
