import { describe, expect, it } from 'vitest'
import {
  layoutSteps,
  newStep,
} from '../../src/components/Settings/WorkflowAutomations/workflowSteps'

describe('workflow layout', () => {
  it('places sequential steps from top to bottom', () => {
    const first = newStep()
    const second = newStep()

    expect(
      layoutSteps([first, second]).map(({ position }) => position),
    ).toEqual([
      { x: 0, y: 150 },
      { x: 0, y: 300 },
    ])
  })

  it('splits condition branches horizontally', () => {
    const condition = newStep({ step_type: 'If' })
    condition.children.If.push(newStep())
    condition.children.Else.push(newStep())

    const positions = layoutSteps([condition]).map(({ position }) => position)
    expect(positions).toEqual([
      { x: 0, y: 150 },
      { x: -280, y: 300 },
      { x: 280, y: 300 },
    ])
  })
})
