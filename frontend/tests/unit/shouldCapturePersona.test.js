import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// `call` must be mocked before importing the module under test, since
// router.js reads it at module-eval time via the `import { call } from
// 'frappe-ui'` at the top of the file.
const callMock = vi.fn()
vi.mock('frappe-ui', () => ({ call: (...args) => callMock(...args) }))

// createRouter/createWebHistory run at module scope in router.js (outside
// shouldCapturePersona), so they need a working implementation too, not a
// bare mock — otherwise importing the module throws before any test runs.
vi.mock('vue-router', () => ({
  createRouter: () => ({ beforeEach: vi.fn() }),
  createWebHistory: () => ({}),
}))
vi.mock('@/stores/users', () => ({ usersStore: vi.fn() }))
vi.mock('@/stores/session', () => ({ sessionStore: vi.fn() }))
vi.mock('@/stores/views', () => ({ viewsStore: vi.fn() }))

const { shouldCapturePersona, PERSONA_DONE_KEY } = await import('../../src/router.js')

describe('shouldCapturePersona', () => {
  beforeEach(() => {
    callMock.mockReset()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns false without calling the server when already captured locally', async () => {
    localStorage.setItem(PERSONA_DONE_KEY, '1')
    expect(await shouldCapturePersona()).toBe(false)
    expect(callMock).not.toHaveBeenCalled()
  })

  it('returns false when persona_captured is already set server-side', async () => {
    callMock.mockResolvedValueOnce(true) // get_single_value
    expect(await shouldCapturePersona()).toBe(false)
    expect(callMock).toHaveBeenCalledTimes(1)
  })

  it('returns true when boot_config resolves enabled', async () => {
    callMock
      .mockResolvedValueOnce(false) // persona_captured
      .mockResolvedValueOnce({ enabled: true }) // boot_config
    expect(await shouldCapturePersona()).toBe(true)
  })

  it('returns false when boot_config resolves disabled', async () => {
    callMock
      .mockResolvedValueOnce(false)
      .mockResolvedValueOnce({ enabled: false })
    expect(await shouldCapturePersona()).toBe(false)
  })

  /**
   * The regression case: boot_config isn't whitelisted on every Frappe
   * version CRM supports (see the comment in router.js), so the call
   * rejects. Before this fix, that rejection propagated out of
   * shouldCapturePersona uncaught.
   */
  it('returns false, without throwing, when boot_config is not available', async () => {
    callMock
      .mockResolvedValueOnce(false) // persona_captured
      .mockRejectedValueOnce(
        new Error(
          "ValidationError: Failed to get method for command frappe.utils.telemetry.pulse.client.boot_config",
        ),
      )
    await expect(shouldCapturePersona()).resolves.toBe(false)
  })
})
