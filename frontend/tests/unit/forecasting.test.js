import { describe, expect, it, vi } from 'vitest'
import {
  SINGLE_VALUE_METHOD,
  forecastOnSave,
  forecastProbability,
  readForecasting,
} from '../../../crm/fcrm/frontend/forecasting/forecasting.js'

const PROBABILITIES = { Qualification: 10, Negotiation: 60, Won: 100 }

function fakePage(options = {}) {
  const { forecasting = 1, status = 'Negotiation' } = options
  const probabilities =
    'probabilities' in options ? options.probabilities : PROBABILITIES
  const held = { forecasting: forecasting ? probabilities : null }
  return {
    doc: { status, probability: 10 },
    saved: { status: 'Qualification', probability: 10 },
    isNew: false,
    call: vi.fn(),
    cached: vi.fn((key) => held[key]),
  }
}

describe('readForecasting', () => {
  it('holds the probabilities under one key', () => {
    const page = fakePage()
    expect(readForecasting(page, vi.fn())).toBe(PROBABILITIES)
    expect(page.cached).toHaveBeenCalledTimes(1)
    expect(page.cached).toHaveBeenCalledWith(
      'forecasting',
      expect.any(Function),
    )
  })

  it("reads FCRM Settings' switch, then the statuses' probabilities, in one fetch", async () => {
    const page = fakePage()
    page.call = vi.fn(async () => 1)
    const readProbabilities = vi.fn(async () => PROBABILITIES)
    readForecasting(page, readProbabilities)
    const [, fetch] = page.cached.mock.calls[0]
    expect(await fetch()).toBe(PROBABILITIES)
    expect(page.call).toHaveBeenCalledWith(SINGLE_VALUE_METHOD, {
      doctype: 'FCRM Settings',
      field: 'enable_forecasting',
    })
  })

  it('reads no probabilities while forecasting is off', async () => {
    const page = fakePage()
    page.call = vi.fn(async () => 0)
    const readProbabilities = vi.fn()
    readForecasting(page, readProbabilities)
    const [, fetch] = page.cached.mock.calls[0]
    expect(await fetch()).toBeNull()
    expect(readProbabilities).not.toHaveBeenCalled()
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

describe('forecastOnSave', () => {
  it('sets the probability of a status changed outside the form, as a header pick saves it', () => {
    const page = fakePage()
    forecastOnSave(vi.fn())(page)
    expect(page.doc.probability).toBe(60)
  })

  it('keeps a probability the draft already moved, by the status handler or the reader', () => {
    const page = fakePage()
    page.doc.probability = 45
    forecastOnSave(vi.fn())(page)
    expect(page.doc.probability).toBe(45)
  })

  it('sets nothing when the status is the saved one', () => {
    const page = fakePage({ status: 'Qualification' })
    forecastOnSave(vi.fn())(page)
    expect(page.doc.probability).toBe(10)
    expect(page.cached).not.toHaveBeenCalled()
  })

  it('leaves a new deal to the server default', () => {
    const page = fakePage()
    page.isNew = true
    forecastOnSave(vi.fn())(page)
    expect(page.doc.probability).toBe(10)
  })

  it('sets nothing while forecasting is off', () => {
    const page = fakePage({ forecasting: 0 })
    forecastOnSave(vi.fn())(page)
    expect(page.doc.probability).toBe(10)
  })
})
