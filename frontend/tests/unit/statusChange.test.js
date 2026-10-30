import { describe, expect, it, vi } from 'vitest'
import {
  changeStatus,
  findStatus,
  statusInk,
  statusPicker,
} from '../../../crm/fcrm/frontend/status/statusChange.js'

function fakePage(status, save = () => Promise.resolve()) {
  const page = {
    doc: { status },
    saved: { status },
    toast: { error: vi.fn() },
    save: vi.fn(() => {
      page.savedWith = page.doc.status
      return save()
    }),
  }
  return page
}

describe('statusInk', () => {
  it("draws each status colour in CRM v1's shade", () => {
    expect(statusInk('red')).toBe('text-ink-red-6')
    expect(statusInk('green')).toBe('text-ink-green-7')
    expect(statusInk('black')).toBe('text-ink-gray-9')
  })

  it('falls back to gray for no colour or an unknown one', () => {
    expect(statusInk(undefined)).toBe('text-ink-gray-6')
    expect(statusInk('magenta')).toBe('text-ink-gray-6')
  })
})

describe('findStatus', () => {
  it('finds the row by name, and nothing while the statuses are unread', () => {
    const statuses = [{ name: 'New' }, { name: 'Won' }]
    expect(findStatus(statuses, 'Won')).toBe(statuses[1])
    expect(findStatus(undefined, 'Won')).toBeUndefined()
  })
})

describe('changeStatus', () => {
  it('writes the status, then saves the record with it', async () => {
    const page = fakePage('New')
    await changeStatus(page, { name: 'Contacted' })
    expect(page.savedWith).toBe('Contacted')
    expect(page.doc.status).toBe('Contacted')
    expect(page.toast.error).not.toHaveBeenCalled()
  })

  it('does not save when the pick is the current status', async () => {
    const page = fakePage('New')
    await changeStatus(page, { name: 'New' })
    expect(page.save).not.toHaveBeenCalled()
  })

  it('goes back to the saved status and shows the message when the save is refused', async () => {
    const refusal = new Error('Please specify a reason for losing the deal.')
    const page = fakePage('Qualification', () => Promise.reject(refusal))
    await changeStatus(page, { name: 'Lost' })
    expect(page.doc.status).toBe('Qualification')
    expect(page.toast.error).toHaveBeenCalledWith(
      'Please specify a reason for losing the deal.',
    )
  })

  it('keeps the record a conflict reload brought in, and leaves the message to its dialog', async () => {
    const page = fakePage('Qualification', () => {
      page.doc = { status: 'Won' }
      page.saved = { status: 'Won' }
      return Promise.reject(
        Object.assign(new Error('Saved elsewhere'), { name: 'SaveConflict' }),
      )
    })
    await changeStatus(page, { name: 'Negotiation' })
    expect(page.doc.status).toBe('Won')
    expect(page.toast.error).not.toHaveBeenCalled()
  })
})

describe('statusPicker', () => {
  it('ignores a pick while a save is running', async () => {
    let answer
    const page = fakePage(
      'New',
      () => new Promise((resolve) => (answer = resolve)),
    )
    const { busy, pick } = statusPicker(page)
    const first = pick({ name: 'Contacted' })
    expect(busy.value).toBe(true)
    await pick({ name: 'Qualified' })
    expect(page.save).toHaveBeenCalledTimes(1)
    expect(page.doc.status).toBe('Contacted')
    answer()
    await first
    expect(busy.value).toBe(false)
  })
})
