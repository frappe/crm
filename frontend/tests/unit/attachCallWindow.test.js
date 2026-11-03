import { describe, expect, it, vi } from 'vitest'
import { attachCallWindow } from '../../../crm/fcrm/frontend/telephony/attachCallWindow.js'

function attach(media) {
  const shell = { window: vi.fn().mockReturnValue('handle') }
  const loadWindow = vi.fn().mockResolvedValue({ default: 'CallWindow' })
  const callingMedia = vi
    .fn()
    .mockResolvedValue({ media, default_medium: null })
  return {
    shell,
    loadWindow,
    run: () => attachCallWindow(shell, { callingMedia, loadWindow }),
  }
}

describe('attachCallWindow', () => {
  it('draws nothing, and loads no window code, for a user with no medium', async () => {
    const { shell, loadWindow, run } = attach([])
    await run()
    expect(shell.window).not.toHaveBeenCalled()
    expect(loadWindow).not.toHaveBeenCalled()
  })

  it('draws nothing for an Exotel-only user until Exotel is built', async () => {
    const { shell, run } = attach(['Exotel'])
    await run()
    expect(shell.window).not.toHaveBeenCalled()
  })

  it('attaches the 260px phone window for a Twilio user', async () => {
    const { shell, run } = attach(['Twilio', 'Exotel'])
    expect(await run()).toBe('handle')
    expect(shell.window).toHaveBeenCalledWith('CallWindow', {
      icon: 'lucide-phone',
      width: 260,
    })
  })
})
