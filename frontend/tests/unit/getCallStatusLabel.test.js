// callLog.js pulls in unrelated heavy dependencies (icon-resolving imports,
// a live createResource network call) that aren't wired up for vitest —
// stub them so this test exercises only getCallStatusLabel's pure logic.
vi.mock('@/utils', () => ({ formatDate: vi.fn() }))
vi.mock('@/stores/meta', () => ({
  getMeta: () => ({
    getFormattedPercent: vi.fn(),
    getFormattedFloat: vi.fn(),
    getFormattedCurrency: vi.fn(),
  }),
}))
vi.mock('@/composables/useTimelinePreferences', () => ({
  timestampCell: vi.fn(),
}))

import { getCallStatusLabel } from '@/utils/callLog'

describe('getCallStatusLabel', () => {
  it('labels an unanswered incoming call as Missed Call', () => {
    expect(getCallStatusLabel('No Answer', 'Incoming')).toBe('Missed Call')
  })

  it('labels an unanswered outgoing call as No Answer', () => {
    expect(getCallStatusLabel('No Answer', 'Outgoing')).toBe('No Answer')
  })

  it('falls back to No Answer when call type is missing', () => {
    expect(getCallStatusLabel('No Answer', undefined)).toBe('No Answer')
  })

  it('leaves other statuses unaffected by call type', () => {
    expect(getCallStatusLabel('Completed', 'Incoming')).toBe('Completed')
    expect(getCallStatusLabel('Completed', 'Outgoing')).toBe('Completed')
  })
})
