import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive, ref } from 'vue'

const { initialItems } = vi.hoisted(() => ({
  initialItems: [
    { key: 'leads', label: 'Leads', type: 'Route', route: '/leads' },
  ],
}))

const settingsState = {
  _settings: reactive({
    doc: null,
    setValue: { submit: vi.fn() },
  }),
  settings: ref({}),
}

vi.mock('@/stores/settings', () => ({
  getSettings: () => settingsState,
}))

vi.mock('frappe-ui', () => ({
  createDocumentResource: () => ({}),
  createResource: () => ({}),
  createToast: vi.fn(),
  toast: Object.assign(vi.fn(), { error: vi.fn(), success: vi.fn() }),
  Badge: (_, { attrs }) => h('span', { 'data-testid': 'badge' }, attrs.label),
  ErrorMessage: (_, { attrs }) =>
    attrs.message
      ? h('div', { 'data-testid': 'error-message' }, String(attrs.message))
      : null,
}))

vi.mock('vuedraggable', () => ({
  default: (_, { attrs, slots }) =>
    h(
      'ul',
      (attrs.modelValue || []).map((element) =>
        slots.item ? slots.item({ element }) : null,
      ),
    ),
}))

vi.mock('@/components/Settings/AppMenu/AppMenuRow.vue', () => ({
  default: (_, { attrs }) =>
    h(
      'div',
      { 'data-testid': 'app-menu-row' },
      attrs.item?.label || 'Divider',
    ),
}))

vi.mock('@/components/Settings/AppMenu/AppMenuPreview.vue', () => ({
  default: (_, { attrs }) =>
    h('div', {
      'data-testid': 'app-menu-preview',
      'data-count': String((attrs.items || []).length),
    }),
}))

vi.mock('@/components/Settings/AppMenu/AppMenuItemDialog.vue', () => ({
  default: () => null,
}))

import AppMenuSettings from '@/components/Settings/AppMenu/AppMenuSettings.vue'

function mountAppMenu() {
  const root = document.createElement('div')
  const app = createApp(AppMenuSettings)
  app.config.globalProperties.__ = (text) => text
  const buttonName = 'Button'
  app.component(buttonName, (_, { attrs }) =>
    h('button', { onClick: attrs.onClick }, attrs.label),
  )
  app.mount(root)
  const button = (label) =>
    [...root.querySelectorAll('button')].find(
      (el) => el.textContent.trim() === label,
    )
  const previewCount = () =>
    Number(
      root
        .querySelector('[data-testid="app-menu-preview"]')
        ?.getAttribute('data-count'),
    )
  const errorText = () =>
    root.querySelector('[data-testid="error-message"]')?.textContent || ''
  return { root, app, button, previewCount, errorText }
}

describe('AppMenuSettings', () => {
  beforeEach(() => {
    settingsState._settings.doc = {
      dropdown_items: initialItems.map((row) => ({ ...row })),
    }
    settingsState._settings.setValue.submit = vi.fn()
    settingsState.settings.value = settingsState._settings.doc
  })

  it('preserves unsaved edits and error when setValue reverts doc on failure', async () => {
    const { app, button, previewCount, errorText } = mountAppMenu()
    try {
      expect(previewCount()).toBe(1)
      expect(button('Save')).toBeUndefined()

      button('Add divider').click()
      await nextTick()

      expect(previewCount()).toBe(2)
      expect(button('Save')).toBeDefined()
      expect(button('Discard')).toBeDefined()

      // Simulate frappe-ui setValue optimistic update followed by revert + onError
      settingsState._settings.setValue.submit.mockImplementationOnce(
        (values, { onError }) => {
          const previousDoc = settingsState._settings.doc
          settingsState._settings.doc = { ...previousDoc, ...values }
          settingsState._settings.doc = {
            ...previousDoc,
            dropdown_items: initialItems.map((row) => ({ ...row })),
          }
          onError({ messages: ['Invalid menu configuration'] })
        },
      )

      button('Save').click()
      await nextTick()

      expect(previewCount()).toBe(2)
      expect(button('Save')).toBeDefined()
      expect(button('Discard')).toBeDefined()
      expect(errorText()).toContain('Invalid menu configuration')

      // Retrying and succeeding refreshes baseline and clears dirty state
      settingsState._settings.setValue.submit.mockImplementationOnce(
        (values, { onSuccess }) => {
          settingsState._settings.doc = {
            ...settingsState._settings.doc,
            ...values,
          }
          onSuccess()
        },
      )

      button('Save').click()
      await nextTick()

      expect(previewCount()).toBe(2)
      expect(button('Save')).toBeUndefined()
      expect(errorText()).toBe('')
      expect(settingsState.settings.value).toStrictEqual(
        settingsState._settings.doc,
      )
    } finally {
      app.unmount()
    }
  })

  it('loads baseline once settings.doc arrives and discards back to it', async () => {
    settingsState._settings.doc = null
    const { app, button, previewCount } = mountAppMenu()
    try {
      expect(previewCount()).toBe(0)

      settingsState._settings.doc = {
        dropdown_items: initialItems.map((row) => ({ ...row })),
      }
      await nextTick()

      expect(previewCount()).toBe(1)
      expect(button('Save')).toBeUndefined()

      button('Add divider').click()
      await nextTick()
      expect(previewCount()).toBe(2)
      expect(button('Discard')).toBeDefined()

      button('Discard').click()
      await nextTick()
      expect(previewCount()).toBe(1)
      expect(button('Save')).toBeUndefined()
    } finally {
      app.unmount()
    }
  })
})
