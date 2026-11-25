import { describe, it, expect, vi } from 'vitest'
import { createApp, nextTick, reactive } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  const stub = (name) =>
    defineComponent({
      name,
      setup:
        (_, { slots }) =>
        () =>
          h('div', slots.default?.()),
    })
  return {
    ErrorMessage: stub('ErrorMessage'),
    FormControl: stub('FormControl'),
    Switch: stub('Switch'),
    toast: { success: () => {} },
  }
})

vi.mock('@/components/Controls/Link.vue', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    default: defineComponent({
      props: { doctype: { type: String, default: '' } },
      setup: (props) => () => h('div', { 'data-link-doctype': props.doctype }),
    }),
  }
})

vi.mock('@/stores/settings', () => ({
  getSettings: () => ({
    _settings: reactive({ doc: {}, save: { submit: () => {} } }),
  }),
}))
vi.mock('@/stores/global', () => ({
  globalStore: () => ({ $dialog: () => {} }),
}))
vi.mock('@/composables/useBroadcast', () => ({
  useBroadcast: () => ({ send: () => {} }),
}))
vi.mock('vue-router', () => ({ useRoute: () => ({}) }))

describe('DashboardSettings', () => {
  it('lets the dashboard currency be picked from every currency', async () => {
    const { default: DashboardSettings } = await import(
      '@/components/Settings/DashboardSettings.vue'
    )
    const el = document.createElement('div')
    const app = createApp(DashboardSettings)
    app.config.globalProperties.__ = globalThis.__
    app.mount(el)
    await nextTick()

    expect(el.querySelector('[data-link-doctype="Currency"]')).not.toBeNull()
    app.unmount()
  })
})
