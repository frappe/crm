import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  io: vi.fn(() => ({ on: vi.fn() })),
  mount: vi.fn(),
  frappeRequest: vi.fn(),
}))

vi.mock('socket.io-client', () => ({ io: mocks.io }))
vi.mock('vue', async (importOriginal) => {
  const vue = await importOriginal()
  return {
    ...vue,
    createApp: (...args) => {
      const app = vue.createApp(...args)
      app.mount = mocks.mount
      return app
    },
  }
})
vi.mock('frappe-ui', async () => {
  const { default: FrappeUI } = await import(
    '../../node_modules/frappe-ui/src/utils/plugin.ts'
  )
  return {
    FrappeUI,
    setConfig: vi.fn(),
    frappeRequest: mocks.frappeRequest,
    getCachedResource: vi.fn(),
    getCachedListResource: vi.fn(),
    ...Object.fromEntries(
      [
        'Button',
        'Input',
        'TextInput',
        'FormControl',
        'ErrorMessage',
        'Dialog',
        'Alert',
        'Badge',
        'FeatherIcon',
      ].map((name) => [name, {}]),
    ),
  }
})
vi.mock('@/App.vue', () => ({ default: {} }))
vi.mock('@/router', () => ({ default: { install() {} } }))
vi.mock('@/translation', () => ({ default: { install() {} } }))
vi.mock('@/utils/dialogs', () => ({ createDialog: vi.fn() }))
vi.mock('frappe-ui/frappe', () => ({ telemetryPlugin: { install() {} } }))
vi.mock('frappe-ui/icons', () => ({ spritePlugin: { install() {} } }))

describe('application realtime startup', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    window.site_name = 'crm.test'
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    delete window.site_name
  })

  it('opens only the CRM socket in production', async () => {
    vi.stubEnv('DEV', false)
    await import('@/main')
    expect(mocks.io).toHaveBeenCalledTimes(1)
    expect(mocks.io.mock.calls[0][1].reconnectionAttempts).toBe(5)
    expect(mocks.io.mock.results[0].value.on).toHaveBeenCalledWith(
      'refetch_resource',
      expect.any(Function),
    )
    expect(mocks.mount).toHaveBeenCalledWith('#app')
  })

  it('waits for development context before opening the CRM socket', async () => {
    vi.stubEnv('DEV', true)
    let resolveContext
    mocks.frappeRequest.mockReturnValue(
      new Promise((resolve) => {
        resolveContext = resolve
      }),
    )
    await import('@/main')
    expect(mocks.io).not.toHaveBeenCalled()
    resolveContext({ site_name: 'development.test' })
    await Promise.resolve()
    expect(mocks.io).toHaveBeenCalledTimes(1)
    expect(mocks.io.mock.calls[0][0]).toContain('/development.test')
    expect(mocks.mount).toHaveBeenCalledWith('#app')
  })
})
