import { describe, expect, it } from 'vitest'
import {
  EVENT_MATCHED,
  layoutSteps,
  newStep,
  toRows,
  toTree,
} from '../../src/components/Settings/WorkflowAutomations/workflowSteps'

describe('workflow layout', () => {
  it('places sequential steps left to right on one row', () => {
    const positions = layoutSteps([newStep(), newStep()]).map(
      ({ position }) => position,
    )

    expect(positions.map(({ y }) => y)).toEqual([0, 0])
    expect(positions[1].x).toBeGreaterThan(positions[0].x)
  })

  it('splits condition arms above and below the trunk', () => {
    const condition = newStep({ step_type: 'If' })
    condition.children.If.push(newStep())
    condition.children.Else.push(newStep())

    const [branch, ifArm, elseArm] = layoutSteps([condition]).map(
      ({ position }) => position,
    )

    expect(branch.y).toBe(0)
    expect(ifArm.y).toBeLessThan(0)
    expect(elseArm.y).toBeGreaterThan(0)
    expect(ifArm.x).toBe(elseArm.x)
    expect(ifArm.x).toBeGreaterThan(branch.x)
  })

  it('gives a wait-for-event step the same two arms', () => {
    const wait = newStep({ step_type: 'WaitForEvent' })
    wait.children.If.push(newStep())
    wait.children.Else.push(newStep())

    const [, ifArm, elseArm] = layoutSteps([wait]).map(
      ({ position }) => position,
    )

    expect(ifArm.y).toBeLessThan(elseArm.y)
  })
})

describe('wait-for-event arms', () => {
  const wait = () =>
    newStep({ step_type: 'WaitForEvent', step_key: 'wait_for_reply' })

  it('writes the outcome condition the engine expects', () => {
    const node = wait()
    node.children.If.push(newStep({ step_key: 'hot' }))
    node.children.Else.push(newStep({ step_key: 'cold' }))

    const rows = toRows([node])

    expect(
      rows.map((row) => [row.idx, row.step_type, row.parent_step, row.branch]),
    ).toEqual([
      [1, 'WaitForEvent', 0, ''],
      [2, 'If', 0, ''],
      [3, 'Action', 2, 'If'],
      [4, 'Action', 2, 'Else'],
    ])
    expect(rows[1].step_condition).toBe(EVENT_MATCHED)
  })

  it('folds that condition back into the wait when reading', () => {
    const tree = toTree([
      { idx: 1, step_type: 'WaitForEvent', step_key: 'wait_for_reply' },
      {
        idx: 2,
        step_type: 'If',
        step_key: 'did_reply',
        step_condition: EVENT_MATCHED,
      },
      {
        idx: 3,
        step_type: 'Action',
        step_key: 'hot',
        parent_step: 2,
        branch: 'If',
      },
      {
        idx: 4,
        step_type: 'Action',
        step_key: 'cold',
        parent_step: 2,
        branch: 'Else',
      },
    ])

    expect(tree).toHaveLength(1)
    expect(tree[0].step_type).toBe('WaitForEvent')
    expect(tree[0].children.If.map((n) => n.step_key)).toEqual(['hot'])
    expect(tree[0].children.Else.map((n) => n.step_key)).toEqual(['cold'])
  })

  it('round-trips without renaming the outcome step', () => {
    const rows = [
      { idx: 1, step_type: 'WaitForEvent', step_key: 'wait_for_reply' },
      {
        idx: 2,
        step_type: 'If',
        step_key: 'did_reply',
        step_condition: EVENT_MATCHED,
      },
      {
        idx: 3,
        step_type: 'Action',
        step_key: 'hot',
        parent_step: 2,
        branch: 'If',
      },
    ]

    expect(toRows(toTree(rows)).map((row) => row.step_key)).toEqual([
      'wait_for_reply',
      'did_reply',
      'hot',
    ])
  })

  it('leaves a wait with no arms as a single row', () => {
    expect(toRows([wait()])).toHaveLength(1)
  })

  it('keeps an unrelated If next to a wait untouched', () => {
    const tree = toTree([
      { idx: 1, step_type: 'WaitForEvent', step_key: 'wait_for_reply' },
      {
        idx: 2,
        step_type: 'If',
        step_key: 'other',
        step_condition: 'doc.status == "Open"',
      },
    ])

    expect(tree.map((node) => node.step_type)).toEqual(['WaitForEvent', 'If'])
  })
})

describe('step keys', () => {
  it('names an untitled step after what it does', () => {
    const rows = toRows([
      newStep({ action_type: 'AdjustLeadScore' }),
      newStep({ action_type: 'AdjustLeadScore' }),
      newStep({ step_type: 'If' }),
    ])

    expect(rows.map((row) => row.step_key)).toEqual([
      'adjust_lead_score',
      'adjust_lead_score_2',
      'condition',
    ])
  })

  it('never overwrites a key someone chose', () => {
    expect(
      toRows([newStep({ step_key: 'mine', action_type: 'X' })])[0].step_key,
    ).toBe('mine')
  })
})
