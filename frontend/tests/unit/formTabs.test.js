import { isProxy, reactive } from 'vue'
import { mergeFormTabs, composerTab } from '@/utils/formTabs'

const component = { render: () => null }
const base = [
  { name: 'Activity', value: 'activity' },
  { name: 'Emails', value: 'emails' },
]

describe('mergeFormTabs', () => {
  it('patches a built-in tab by name, ignoring case, keeping name and value', () => {
    const result = mergeFormTabs(base, [
      { name: 'emails', value: 'inbox', label: 'Inbox' },
    ])
    expect(result).toEqual([
      base[0],
      { name: 'Emails', value: 'emails', label: 'Inbox' },
    ])
  })

  it('appends a component tab with a slug value, keeping non-latin letters', () => {
    const result = mergeFormTabs(base, [
      { name: '  Shipping  Notes ', component },
      { name: 'عروض الأسعار', component },
      { name: 'Q&A / FAQ?', component },
    ])
    expect(result.slice(2).map((t) => t.value)).toEqual([
      'shipping-notes',
      'عروض-الأسعار',
      'qa--faq',
    ])
  })

  it('skips appended tabs without a component or a unique value', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const result = mergeFormTabs(base, [
      { name: 'Empty' },
      { name: 'Mail', value: 'emails', component },
      { name: 'Excom', value: 'x', component },
      { name: 'Other', value: 'x', component },
      { name: '???', component },
    ])
    expect(result.map((t) => t.name)).toEqual(['Activity', 'Emails', 'Excom'])
    expect(warn).toHaveBeenCalledTimes(4)
    warn.mockRestore()
  })

  it('requires both the built-in and the script condition', () => {
    const tabs = [
      ...base,
      { name: 'WhatsApp', value: 'whatsapp', condition: () => false },
    ]
    const result = mergeFormTabs(tabs, [
      { name: 'WhatsApp', condition: () => true },
      { name: 'Emails', condition: () => false },
    ])
    expect(result.map((t) => t.name)).toEqual(['Activity'])
  })

  it('hides a tab with hide, as a flag or a function', () => {
    const tabs = [
      ...base,
      { name: 'Comments', value: 'comments', condition: () => true },
    ]
    const result = mergeFormTabs(tabs, [
      { name: 'Activity', hide: () => true },
      { name: 'Emails', hide: false },
      { name: 'Comments', hide: true },
    ])
    expect(result.map((t) => t.name)).toEqual(['Emails'])
  })

  it('labels an appended tab with its name by default', () => {
    expect(
      mergeFormTabs(base, [{ name: 'Shipping', component }])[2].label,
    ).toBe('Shipping')
  })

  it('hides only the tab whose condition throws', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    const result = mergeFormTabs(base, [
      {
        name: 'Emails',
        condition: () => {
          throw new Error('boom')
        },
      },
    ])
    expect(result.map((t) => t.name)).toEqual(['Activity'])
    expect(error).toHaveBeenCalledOnce()
    error.mockRestore()
  })

  it('does not let a reactive tab list proxy the component', () => {
    const result = mergeFormTabs(base, reactive([{ name: 'X', component }]))
    expect(isProxy(result[2].component)).toBe(false)
    expect(result[2].component).toBe(component)
  })
})

describe('composerTab', () => {
  const tabs = [
    { name: 'Activity', value: 'activity' },
    { name: 'Emails', value: 'emails' },
    { name: 'Comments', value: 'comments' },
    { name: 'Calls', value: 'calls' },
  ]

  it('keeps the active tab when it has a composer', () => {
    expect(composerTab(tabs, 'activity')).toBe('activity')
    expect(composerTab(tabs, 'comments')).toBe('comments')
  })

  it('opens Emails from a tab without a composer', () => {
    expect(composerTab(tabs, 'calls')).toBe('emails')
  })

  it('falls back to Activity when Emails is hidden', () => {
    const rest = tabs.filter((tab) => tab.value !== 'emails')
    expect(composerTab(rest, 'calls')).toBe('activity')
  })

  it('skips a hidden or component tab', () => {
    const rest = tabs.filter((tab) => tab.value !== 'activity')
    const replaced = rest.map((tab) =>
      tab.value === 'emails' ? { ...tab, component } : tab,
    )
    expect(composerTab(replaced, 'emails')).toBe('comments')
  })

  it('returns null when no tab has a composer', () => {
    expect(composerTab([tabs[3]], 'calls')).toBeNull()
  })
})
