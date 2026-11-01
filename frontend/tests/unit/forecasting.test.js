import { describe, expect, it, vi } from 'vitest'
import {
  SINGLE_VALUE_METHOD,
  forecastProbability,
  readForecasting,
} from '../../../crm/fcrm/frontend/forecasting/forecasting.js'

const PROBABILITIES = { Qualification: 10, Negotiation: 60, Won: 100 }

function fakePage(options = {}) {
  const { forecasting = 1, status = 'Negotiation' } = options
  const probabilities =
    'probabilities' in options ? options.probabilities : PROBABILITIES
  const held = { forecasting, 'probabilities:CRM Deal Status': probabilities }
  return {
    doc: { status, probability: 10 },
    saved: { status: 'Qualification' },
    call: vi.fn(),
    cached: vi.fn((key) => held[key]),
  }
}

describe('readForecasting', () => {
  it("reads FCRM Settings' switch, then the statuses' probabilities", () => {
    const page = fakePage()
    const readProbabilities = vi.fn()
    expect(readForecasting(page, readProbabilities)).toBe(PROBABILITIES)
    expect(page.cached).toHaveBeenCalledWith(
      'forecasting',
      expect.any(Function),
    )
    expect(page.cached).toHaveBeenCalledWith(
      'probabilities:CRM Deal Status',
      readProbabilities,
    )
  })

  it('reads the switch through page.call', () => {
    const page = fakePage()
    page.cached = vi.fn((key, fetch) => fetch())
    readForecasting(page, vi.fn())
    expect(page.call).toHaveBeenCalledWith(SINGLE_VALUE_METHOD, {
      doctype: 'FCRM Settings',
      field: 'enable_forecasting',
    })
  })

  it('reads no probabilities while forecasting is off', () => {
    const page = fakePage({ forecasting: 0 })
    expect(readForecasting(page, vi.fn())).toBeUndefined()
    expect(page.cached).toHaveBeenCalledTimes(1)
  })
})

describe('forecastProbability', () => {
  it('runs the handler, then sets the picked status probability', async () => {
    const page = fakePage()
    const handler = vi.fn()
    await forecastProbability(handler, vi.fn())(page)
    expect(handler).toHaveBeenCalledWith(page)
    expect(page.doc.probability).toBe(60)
  })

  it('sets nothing while forecasting is off', async () => {
    const page = fakePage({ forecasting: 0 })
    await forecastProbability(vi.fn(), vi.fn())(page)
    expect(page.doc.probability).toBe(10)
  })

  it('sets nothing when the handler took the pick back, as a cancelled lost reason does', async () => {
    const page = fakePage({ status: 'Lost' })
    const cancel = vi.fn((page) => (page.doc.status = page.saved.status))
    await forecastProbability(cancel, vi.fn())(page)
    expect(page.doc).toMatchObject({ status: 'Qualification', probability: 10 })
  })

  it('sets nothing before the probabilities are read', async () => {
    const page = fakePage({ probabilities: undefined })
    await forecastProbability(vi.fn(), vi.fn())(page)
    expect(page.doc.probability).toBe(10)
  })

  it('sets a 0 probability', async () => {
    const page = fakePage({ status: 'Junk', probabilities: { Junk: 0 } })
    await forecastProbability(vi.fn(), vi.fn())(page)
    expect(page.doc.probability).toBe(0)
  })
})
