import type { ResolvedStep, StepItem, StepState, StepValue } from './types'

interface ResolveOptions {
  current?: StepValue | null
  completed?: boolean
  failed?: boolean
}

type Position = 'before' | 'at' | 'after'

/**
 * Walks the steps depth-first (a step, then its sub-steps) and returns the
 * order-sensitive list of leaves: steps without sub-steps, and sub-steps.
 * Only the first level of `children` counts.
 */
function leavesOf(steps: StepItem[]): StepItem[] {
  return steps.flatMap((step) =>
    step.children?.length ? step.children : [step],
  )
}

/**
 * Index of the current leaf. Naming a parent makes its first sub-step current.
 * Returns -1 when nothing matches, `leaves.length` when everything is done.
 */
function currentIndex(steps: StepItem[], opts: ResolveOptions): number {
  const leaves = leavesOf(steps)
  if (opts.completed) return leaves.length
  if (opts.current == null) return -1
  const parent = steps.find(
    (s) => s.value === opts.current && s.children?.length,
  )
  const target = parent ? parent.children![0].value : opts.current
  return leaves.findIndex((leaf) => leaf.value === target)
}

function leafState(
  item: StepItem,
  position: Position,
  failed?: boolean,
): StepState {
  if (position === 'at') return failed ? 'failed' : 'current'
  if (position === 'after') return 'upcoming'
  return item.skipped ? 'skipped' : 'complete'
}

/** A parent's state follows its sub-steps. */
function parentState(item: StepItem, children: ResolvedStep[]): StepState {
  const states = children.map((c) => c.state)
  if (states.some((s) => s === 'current' || s === 'failed')) {
    return states.includes('failed') ? 'failed' : 'current'
  }
  if (states.every((s) => s === 'complete' || s === 'skipped')) {
    return item.skipped ? 'skipped' : 'complete'
  }
  return 'upcoming'
}

/** Derives every step's state from the current value. Never mutates `steps`. */
export function resolveSteps(
  steps: StepItem[],
  opts: ResolveOptions,
): ResolvedStep[] {
  const current = currentIndex(steps, opts)
  let cursor = 0
  const positionOf = (): Position => {
    const i = cursor++
    if (current === -1 || i > current) return 'after'
    return i === current ? 'at' : 'before'
  }
  const leaf = (item: StepItem, index: number): ResolvedStep => ({
    item,
    index,
    state: leafState(item, positionOf(), opts.failed),
    children: [],
  })
  return steps.map((item, index) => {
    if (!item.children?.length) return leaf(item, index)
    const children = item.children.map(leaf)
    return { item, index, state: parentState(item, children), children }
  })
}

/** Done or skipped: progress has moved past it. */
export function isPassed(state: StepState): boolean {
  return state === 'complete' || state === 'skipped'
}
