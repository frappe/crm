import { describe, expect, it } from 'vitest'
import { workflowEdges } from '../../src/components/Settings/WorkflowAutomations/workflowEdges'
import { newStep } from '../../src/components/Settings/WorkflowAutomations/workflowSteps'

describe('workflow graph connectors', () => {
  it('converges both condition branches into the following step', () => {
    const condition = newStep({ step_type: 'If' })
    const trueAction = newStep()
    const falseAction = newStep()
    const joinedStep = newStep({ step_type: 'Wait' })
    condition.children.If.push(trueAction)
    condition.children.Else.push(falseAction)

    const edges = workflowEdges([condition, joinedStep])

    expect(
      edges.map(({ source, target, label }) => [source, target, label]),
    ).toEqual([
      ['trigger', condition._id, null],
      [condition._id, trueAction._id, 'True'],
      [condition._id, falseAction._id, 'False'],
      [trueAction._id, joinedStep._id, null],
      [falseAction._id, joinedStep._id, null],
    ])
  })
})
