import { describe, expect, it, vi } from 'vitest'
import {
  changeStatus,
  findStatus,
  keepLostReason,
  statusInk,
  placeStatusControl,
  statusPicker,
} from '../../../crm/fcrm/frontend/status/statusChange.js'

function fakePage(status, save = () => Promise.resolve(), reason = null) {
  const page = {
    doctype: 'CRM Deal',
    doc: { status },
    saved: { status },
    toast: { error: vi.fn() },
    dialog: { form: vi.fn(() => Promise.resolve(reason)) },
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

describe('changeStatus to a Lost status', () => {
  const lost = { name: 'Lost', type: 'Lost' }

  it('asks for the lost reason, then saves it with the status', async () => {
    const reason = { lost_reason: 'Other', lost_notes: 'Went with a rival' }
    const page = fakePage('Negotiation', undefined, reason)
    await changeStatus(page, lost, 'Lost Reason')
    expect(page.dialog.form).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Lost Reason',
        doctype: 'CRM Deal',
        fieldnames: ['lost_reason', 'lost_notes'],
        required: ['lost_reason'],
      }),
    )
    expect(page.save).toHaveBeenCalledTimes(1)
    expect(page.doc).toMatchObject({ status: 'Lost', ...reason })
  })

  it('keeps the old status and saves nothing when the dialog is cancelled', async () => {
    const page = fakePage('Negotiation', undefined, null)
    await changeStatus(page, lost)
    expect(page.save).not.toHaveBeenCalled()
    expect(page.doc.status).toBe('Negotiation')
  })

  it('puts the saved reason back with the status when the save is refused', async () => {
    const page = fakePage(
      'Negotiation',
      () => Promise.reject(new Error('Expected closure date is required.')),
      { lost_reason: 'Pricing', lost_notes: null },
    )
    await changeStatus(page, lost)
    expect(page.doc.status).toBe('Negotiation')
    expect(page.doc.lost_reason).toBeUndefined()
    expect(page.toast.error).toHaveBeenCalledWith(
      'Expected closure date is required.',
    )
  })

  it('opens the dialog on the reason the record already has', async () => {
    const page = fakePage('Negotiation', undefined, null)
    page.doc.lost_reason = 'Pricing'
    await changeStatus(page, lost)
    expect(page.dialog.form.mock.calls[0][0].defaults).toEqual({
      lost_reason: 'Pricing',
    })
  })

  it('asks nothing for a status of another type', async () => {
    const page = fakePage('New')
    await changeStatus(page, { name: 'Won', type: 'Won' })
    expect(page.dialog.form).not.toHaveBeenCalled()
    expect(page.savedWith).toBe('Won')
  })
})

describe('keepLostReason', () => {
  const statuses = [
    { name: 'Negotiation', type: 'Ongoing' },
    { name: 'Lost', type: 'Lost' },
  ]

  function editedPage(status, reason) {
    const page = fakePage('Negotiation', undefined, reason)
    page.doc.status = status
    return page
  }

  it('writes the reason into the draft without saving', async () => {
    const page = editedPage('Lost', { lost_reason: 'Pricing', lost_notes: '' })
    await keepLostReason(page, Promise.resolve(statuses), 'Lost Reason')
    expect(page.doc).toMatchObject({ status: 'Lost', lost_reason: 'Pricing' })
    expect(page.save).not.toHaveBeenCalled()
  })

  it('goes back to the saved status when the dialog is cancelled', async () => {
    const page = editedPage('Lost', null)
    await keepLostReason(page, Promise.resolve(statuses))
    expect(page.doc.status).toBe('Negotiation')
  })

  it('leaves a pick made while the statuses load to its own handler', async () => {
    const page = editedPage('Lost', null)
    let answer
    const statusesRead = new Promise((resolve) => (answer = resolve))
    const first = keepLostReason(page, statusesRead)
    page.doc.status = 'Negotiation'
    answer(statuses)
    await first
    expect(page.dialog.form).not.toHaveBeenCalled()
  })

  it('leaves a status of another type alone', async () => {
    const page = editedPage('Negotiation', null)
    page.saved = { status: 'New' }
    await keepLostReason(page, Promise.resolve(statuses))
    expect(page.dialog.form).not.toHaveBeenCalled()
    expect(page.doc.status).toBe('Negotiation')
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

describe('placeStatusControl', () => {
  function recordPage(isNew = false) {
    return {
      doctype: 'CRM Lead',
      isNew,
      cached: vi.fn(() => []),
      fields: { get: () => ({}) },
      header: { add: vi.fn() },
    }
  }

  it("puts the control in the header's right zone, before Save", () => {
    const page = recordPage()
    const control = {}
    placeStatusControl(page, control, vi.fn())
    expect(page.header.add).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'status',
        zone: 'right',
        component: control,
      }),
      { before: 'save' },
    )
  })

  it('leaves a doctype with no status doctype without the control', () => {
    const page = { ...recordPage(), doctype: 'CRM Task' }
    placeStatusControl(page, {}, vi.fn())
    expect(page.header.add).not.toHaveBeenCalled()
  })

  it('leaves a new record without the control', () => {
    const page = recordPage(true)
    placeStatusControl(page, {}, vi.fn())
    expect(page.header.add).not.toHaveBeenCalled()
  })
})
