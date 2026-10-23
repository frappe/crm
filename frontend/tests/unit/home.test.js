import { greetingFor } from '@/utils/home'

const at = (hour) => new Date(2026, 9, 23, hour)

describe('greetingFor', () => {
  it('follows the time of day', () => {
    expect(greetingFor(at(9), 'Asha')).toBe('Good morning, Asha')
    expect(greetingFor(at(13), 'Asha')).toBe('Good afternoon, Asha')
    expect(greetingFor(at(20), 'Asha')).toBe('Good evening, Asha')
  })

  it('works without a name', () => {
    expect(greetingFor(at(9))).toBe('Good morning')
  })
})
