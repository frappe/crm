import { resolveFromEmail, matchReceivingMailbox } from '@/utils/emailFrom'

const fromOptions = [
  { label: 'Support <support@example.com>', value: 'support@example.com' },
  { label: 'Sales <sales@example.com>', value: 'sales@example.com' },
]

describe('resolveFromEmail', () => {
  it('keeps fromEmail when it is one of the permitted options', () => {
    expect(
      resolveFromEmail(fromOptions, 'sales@example.com', 'me@example.com'),
    ).toBe('sales@example.com')
  })

  it('falls back to the user email when fromEmail is not a permitted option', () => {
    expect(
      resolveFromEmail(fromOptions, 'lead@their-company.com', 'me@example.com'),
    ).toBe('me@example.com')
  })

  it('falls back to the user email when there are no permitted options', () => {
    expect(
      resolveFromEmail([], 'lead@their-company.com', 'me@example.com'),
    ).toBe('me@example.com')
  })

  it('falls back to the user email when fromOptions is undefined', () => {
    expect(
      resolveFromEmail(undefined, 'lead@their-company.com', 'me@example.com'),
    ).toBe('me@example.com')
  })
})

describe('matchReceivingMailbox', () => {
  it('returns the permitted mailbox that received the email', () => {
    expect(
      matchReceivingMailbox(fromOptions, [
        'lead@their-company.com',
        'sales@example.com',
      ]),
    ).toBe('sales@example.com')
  })

  it('returns null when none of the recipients are a permitted mailbox', () => {
    expect(matchReceivingMailbox(fromOptions, ['lead@their-company.com'])).toBe(
      null,
    )
  })

  it('returns null when fromOptions is empty', () => {
    expect(matchReceivingMailbox([], ['sales@example.com'])).toBe(null)
  })

  it('returns null when recipients is empty or undefined', () => {
    expect(matchReceivingMailbox(fromOptions, [])).toBe(null)
    expect(matchReceivingMailbox(fromOptions, undefined)).toBe(null)
  })

  it('matches a recipient formatted as "Name <email>"', () => {
    expect(
      matchReceivingMailbox(fromOptions, [
        'Lead Name <lead@their-company.com>',
        'Sales Team <sales@example.com>',
      ]),
    ).toBe('sales@example.com')
  })

  it('matches regardless of casing', () => {
    expect(matchReceivingMailbox(fromOptions, ['Sales@Example.com'])).toBe(
      'sales@example.com',
    )
  })

  it('matches when the recipient has surrounding whitespace', () => {
    expect(matchReceivingMailbox(fromOptions, ['  sales@example.com  '])).toBe(
      'sales@example.com',
    )
  })
})
