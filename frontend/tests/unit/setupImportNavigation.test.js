import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick, ref } from 'vue'

vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ capture: vi.fn() }),
}))
vi.mock('frappe-ui', () => ({ toast: { error: vi.fn() } }))
vi.mock('@/composables/leadImport', () => ({
  useLeadImport: () => ({
    preview: ref({ total_number_of_rows: 2 }),
    progress: ref(null),
    createImport: vi.fn().mockResolvedValue(),
    saveMapping: vi.fn().mockResolvedValue(),
    runImport: vi.fn(),
  }),
}))
vi.mock('@/components/Stepper/Stepper.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Setup/SetupImportUpload.vue', () => ({
  default: {
    emits: ['uploaded'],
    setup(_, { emit }) {
      return () =>
        h('button', { onClick: () => emit('uploaded', '/test.csv') }, 'Upload')
    },
  },
}))
vi.mock('@/components/Setup/SetupImportMap.vue', () => ({
  default: {
    emits: ['continue'],
    setup(_, { emit }) {
      return () => h('button', { onClick: () => emit('continue', []) }, 'Map')
    },
  },
}))
vi.mock('@/components/Setup/SetupImportReview.vue', () => ({
  default: { render: () => h('div', 'Review') },
}))
import SetupImport from '@/components/Setup/SetupImport.vue'

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

it('walks back through import stages before leaving import', async () => {
  const root = document.createElement('div')
  const cancel = vi.fn()
  const app = createApp(SetupImport, { onCancel: cancel })
  app.config.globalProperties.__ = (text) => text
  const view = app.mount(root)
  try {
    root.querySelector('button').click()
    await settle()
    expect(root.textContent).toContain('Map')
    root.querySelector('button').click()
    await settle()
    expect(root.textContent).toContain('Review')
    view.back()
    await nextTick()
    expect(root.textContent).toContain('Map')
    view.back()
    await nextTick()
    expect(root.textContent).toContain('Upload')
    expect(cancel).not.toHaveBeenCalled()
    view.back()
    expect(cancel).toHaveBeenCalledOnce()
  } finally {
    app.unmount()
  }
})
