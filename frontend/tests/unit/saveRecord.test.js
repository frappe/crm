import { describe, expect, it, vi } from 'vitest'
import { saveRecord } from '../../../crm/fcrm/frontend/saveRecord.js'

function fakePage(overrides = {}) {
  return {
    toast: { error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    ...overrides,
  }
}

describe('saveRecord', () => {
  it('saves the record and answers true', async () => {
    const page = fakePage()
    expect(await saveRecord(page)).toBe(true)
    expect(page.save).toHaveBeenCalledOnce()
  })

  it('answers false and toasts the reason when the save is refused', async () => {
    const page = fakePage({
      save: vi.fn(() => Promise.reject(new Error('Invalid email'))),
    })
    expect(await saveRecord(page)).toBe(false)
    expect(page.toast.error).toHaveBeenCalledWith('Invalid email')
  })

  it('does not toast a refusal the page has explained in its own dialog', async () => {
    const conflict = Object.assign(new Error('Saved by someone else'), {
      name: 'SaveConflict',
    })
    const page = fakePage({ save: vi.fn(() => Promise.reject(conflict)) })
    expect(await saveRecord(page)).toBe(false)
    expect(page.toast.error).not.toHaveBeenCalled()
  })
})
