import { afterEach, describe, expect, it } from 'vitest'
import { hasFlowLauncher } from '@/utils/flowLauncher'

function addScript(src) {
  const script = document.createElement('script')
  script.src = src
  document.body.append(script)
}

describe('hasFlowLauncher', () => {
  afterEach(() =>
    document.querySelectorAll('script').forEach((s) => s.remove()),
  )

  it('is true when Frappe added the launcher to the page', () => {
    addScript('/assets/frappe/dist/js/flow_launcher.bundle.ABC123.js')
    expect(hasFlowLauncher()).toBe(true)
  })

  it('is false for users Frappe gave no launcher', () => {
    addScript('/assets/crm/frontend/assets/index.js')
    expect(hasFlowLauncher()).toBe(false)
  })
})
