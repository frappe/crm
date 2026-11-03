import { describe, expect, it, vi } from 'vitest'

vi.mock('@/utils', () => ({ formatDate: () => '12 Nov' }))

import { trialCardContent } from '@/utils/trialCard'

const trial = (fields) => ({
  state: 'Active',
  ends_on: '2026-11-12',
  days_left: 10,
  deletes_on: null,
  ...fields,
})

describe('trialCardContent', () => {
  it('shows days left in gray while the trial is far from ending', () => {
    const content = trialCardContent(trial())
    expect(content).toMatchObject({ theme: 'gray', dismissible: true })
    expect(content.title).toBe('Your trial ends in 10 days')
  })

  it('turns amber with three or fewer days left', () => {
    expect(trialCardContent(trial({ days_left: 3 })).theme).toBe('amber')
    expect(trialCardContent(trial({ days_left: 1 })).title).toBe(
      'Your trial ends tomorrow',
    )
    expect(trialCardContent(trial({ days_left: 0 })).title).toBe(
      'Your trial ends today',
    )
  })

  it('asks to manage billing when the plan is over the spending limit', () => {
    const content = trialCardContent(trial({ held: true }))
    expect(content).toMatchObject({ theme: 'amber', action: 'Manage billing' })
  })

  it('shows the deletion date once the trial has ended and cannot be dismissed', () => {
    const content = trialCardContent(
      trial({ state: 'Ended', days_left: 0, deletes_on: '2026-11-12' }),
    )
    expect(content).toMatchObject({ theme: 'red', dismissible: false })
    expect(content.description).toContain('12 Nov')
  })
})
