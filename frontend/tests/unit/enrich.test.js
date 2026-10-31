import { describe, expect, it, vi } from 'vitest'
import {
  ENRICHABLE_METHOD,
  ENRICH_METHOD,
  enrichRecord,
  placeEnrichItem,
} from '../../../crm/fcrm/frontend/enrich/enrich.js'

function fakePage(overrides = {}) {
  return {
    doctype: 'CRM Deal',
    docname: 'CRM-DEAL-45896',
    isNew: false,
    header: { add: vi.fn() },
    toast: { success: vi.fn(), error: vi.fn() },
    save: vi.fn(() => Promise.resolve()),
    cached: vi.fn((key, fetch) => fetch()),
    call: vi.fn(() => ['CRM Lead', 'CRM Deal', 'CRM Organization']),
    ...overrides,
  }
}

describe('placeEnrichItem', () => {
  it('adds a `⋯` entry gated on write when enrichment is set up for the doctype', () => {
    const page = fakePage()
    const run = () => {}
    placeEnrichItem(page, { label: 'Enrich from website', run })
    expect(page.cached).toHaveBeenCalledWith(
      'enrichable_doctypes',
      expect.any(Function),
    )
    expect(page.call).toHaveBeenCalledWith(ENRICHABLE_METHOD)
    expect(page.header.add).toHaveBeenCalledWith({
      name: 'enrich',
      icon: 'lucide-zap',
      right: 'write',
      label: 'Enrich from website',
      run,
    })
  })

  it('draws no button, so Status, Convert and Save keep their slots', () => {
    const page = fakePage()
    placeEnrichItem(page, { label: 'Enrich from website' })
    const [item] = page.header.add.mock.calls[0]
    expect(item.display).toBeUndefined()
    expect(item.component).toBeUndefined()
  })

  it('adds nothing when enrichment is off for the doctype', () => {
    const page = fakePage({ call: vi.fn(() => ['CRM Lead']) })
    placeEnrichItem(page, { label: 'Enrich from website' })
    expect(page.header.add).not.toHaveBeenCalled()
  })

  it('adds nothing when enrichment is off everywhere', () => {
    const page = fakePage({ call: vi.fn(() => []) })
    placeEnrichItem(page, { label: 'Enrich from website' })
    expect(page.header.add).not.toHaveBeenCalled()
  })

  it('adds nothing before the read lands', () => {
    const page = fakePage({ cached: vi.fn(() => undefined) })
    placeEnrichItem(page, { label: 'Enrich from website' })
    expect(page.header.add).not.toHaveBeenCalled()
  })

  it('adds nothing on a new record', () => {
    const page = fakePage({ isNew: true })
    placeEnrichItem(page, { label: 'Enrich from website' })
    expect(page.cached).not.toHaveBeenCalled()
    expect(page.header.add).not.toHaveBeenCalled()
  })
})

describe('enrichRecord', () => {
  it('saves the draft before it queues, since the server reads the saved website', async () => {
    const order = []
    const page = fakePage({
      save: vi.fn(() => order.push('save')),
      call: vi.fn(() => order.push('call')),
    })
    await enrichRecord(page, 'Enrichment started.')
    expect(order).toEqual(['save', 'call'])
  })

  it('queues nothing when the save is refused, and keeps the draft', async () => {
    const page = fakePage({
      save: vi.fn(() => Promise.reject(new Error('Invalid website'))),
    })
    await enrichRecord(page, 'Enrichment started.')
    expect(page.toast.error).toHaveBeenCalledWith('Invalid website')
    expect(page.call).not.toHaveBeenCalled()
    expect(page.toast.success).not.toHaveBeenCalled()
  })

  it('queues enrichment for the record, then toasts that it started', async () => {
    const page = fakePage({
      call: vi.fn(() => Promise.resolve({ queued: true })),
    })
    await enrichRecord(page, 'Enrichment started.')
    expect(page.call).toHaveBeenCalledWith(ENRICH_METHOD, {
      reference_doctype: 'CRM Deal',
      reference_name: 'CRM-DEAL-45896',
    })
    expect(page.toast.success).toHaveBeenCalledWith('Enrichment started.')
  })

  it('leaves a refusal to the host and toasts no success', async () => {
    const refusal = new Error('Set a website on this record before enriching.')
    const page = fakePage({ call: vi.fn(() => Promise.reject(refusal)) })
    await expect(enrichRecord(page, 'Enrichment started.')).rejects.toBe(
      refusal,
    )
    expect(page.toast.success).not.toHaveBeenCalled()
  })
})
