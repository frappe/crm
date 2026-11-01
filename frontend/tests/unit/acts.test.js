import { describe, expect, it, vi } from 'vitest'

const { default: acts } = await import('../../../crm/fcrm/frontend/acts.js')

const act = (name) => acts.find((item) => item.name === name)

describe('Form Scripts to rewrite', () => {
  const formScripts = act('form_scripts_to_rewrite')

  it('is offered only to a reader who can write Client Scripts', () => {
    expect(formScripts.right).toEqual({
      doctype: 'Client Script',
      ptype: 'create',
    })
  })

  it('opens the CRM Form Script list', () => {
    const shell = { router: { push: vi.fn() } }

    formScripts.run(shell)

    expect(shell.router.push).toHaveBeenCalledWith({
      doctype: 'CRM Form Script',
    })
  })
})
