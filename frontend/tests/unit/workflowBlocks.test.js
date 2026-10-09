import { describe, expect, it, vi } from 'vitest'

// workflowCapabilities reaches frappe-ui's resource plugin, which the node test env cannot load.
vi.mock(
  '../../src/components/Settings/WorkflowAutomations/workflowCapabilities',
  () => ({ capabilitiesFor: () => ({ actions: [] }) }),
)

import { blockGroups } from '../../src/components/Settings/WorkflowAutomations/workflowBlocks'
import { newStep } from '../../src/components/Settings/WorkflowAutomations/workflowSteps'

const block = (value) =>
  blockGroups('CRM Lead')
    .flatMap((group) => group.options)
    .find((option) => option.value === value)

describe('wait blocks carry the unit they display', () => {
  it('saves a wait-for-event step with the Days it shows by default', () => {
    const step = newStep(block('WaitForEvent').values)

    expect(JSON.parse(step.params).timeout_unit).toBe('Days')
  })

  it('saves a wait step with the Minutes it shows by default', () => {
    const step = newStep(block('Wait').values)

    expect(JSON.parse(step.params).unit).toBe('Minutes')
  })
})
