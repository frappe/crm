import { describe, expect, it, vi } from 'vitest'
import { callState } from '../../../crm/fcrm/frontend/telephony/callState.js'
import { attachCallWindow } from '../../../crm/fcrm/frontend/telephony/attachCallWindow.js'

function attach(media, live = null) {
  const shell = { window: vi.fn().mockReturnValue('handle') }
  const loadWindow = vi.fn().mockResolvedValue({ default: 'CallWindow' })
  const callingMedia = vi
    .fn()
    .mockResolvedValue({ media, default_medium: null, live_exotel_call: live })
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

  it('attaches the window for an Exotel-only user and keeps what the idle request said', async () => {
    const { shell, run } = attach(['Exotel'], { call_sid: 'X1' })
    await run()
    expect(shell.window).toHaveBeenCalled()
    expect(callState.media).toEqual(['Exotel'])
    expect(callState.liveExotel).toEqual({ call_sid: 'X1' })
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
