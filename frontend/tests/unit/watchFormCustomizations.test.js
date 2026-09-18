import { afterEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, reactive } from 'vue'
import { watchFormCustomizations } from '@/composables/watchFormCustomizations'

let scope

afterEach(() => scope?.stop())

function setup(doc = null, data = null) {
  const document = reactive({ doc })
  const scripts = reactive({ data })
  const apply = vi.fn(() => {
    // Match the page's decision to apply scripts or leave an empty result.
    document._actions = scripts.data?.map((script) => script.name) || []
  })
  scope = effectScope()
  scope.run(() => watchFormCustomizations(document, scripts, apply))
  return { document, scripts, apply }
}

describe('form customization readiness', () => {
  it.each(['document', 'scripts'])(
    'waits for both resources when %s arrives first',
    async (first) => {
      const { document, scripts, apply } = setup()
      if (first === 'document') document.doc = { name: 'LEAD-1' }
      else scripts.data = [{ name: 'custom-action' }]
      await nextTick()
      expect(apply).not.toHaveBeenCalled()
      if (first === 'document') scripts.data = [{ name: 'custom-action' }]
      else document.doc = { name: 'LEAD-1' }
      await nextTick()
      expect(apply).toHaveBeenCalledTimes(1)
      expect(apply.mock.calls[0][0]).toBe(document.doc)
      expect(document._actions).toEqual(['custom-action'])
    },
  )

  it('initializes already cached document and scripts', () => {
    const { document, apply } = setup({ name: 'LEAD-1' }, [
      { name: 'cached-action' },
    ])
    expect(apply).toHaveBeenCalledTimes(1)
    expect(document._actions).toEqual(['cached-action'])
  })

  it('treats an empty script response as loaded', async () => {
    const { document, scripts, apply } = setup()
    document.doc = { name: 'DEAL-1' }
    await nextTick()
    expect(apply).not.toHaveBeenCalled()
    scripts.data = []
    await nextTick()
    expect(apply).toHaveBeenCalledTimes(1)
    expect(document._actions).toEqual([])
  })

  it('does not repeat customization after resource refreshes', async () => {
    const { document, scripts, apply } = setup()
    document.doc = { name: 'LEAD-1' }
    scripts.data = [{ name: 'first-action' }]
    await nextTick()
    document.doc = { name: 'LEAD-1', status: 'Updated' }
    scripts.data = [{ name: 'changed-action' }]
    await nextTick()
    expect(apply).toHaveBeenCalledTimes(1)
    expect(document._actions).toEqual(['first-action'])
  })

  it('does not initialize after its component scope is disposed', async () => {
    const { document, scripts, apply } = setup()
    scope.stop()
    document.doc = { name: 'LEAD-1' }
    scripts.data = [{ name: 'late-action' }]
    await nextTick()
    expect(apply).not.toHaveBeenCalled()
  })
})
