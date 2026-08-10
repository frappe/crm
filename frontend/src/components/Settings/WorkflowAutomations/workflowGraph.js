import ActionIcon from '~icons/lucide/zap'
import BranchIcon from '~icons/lucide/git-branch'
import EventIcon from '~icons/lucide/webhook'
import TriggerIcon from '~icons/lucide/play'
import WaitIcon from '~icons/lucide/timer'
import { layoutSteps } from './workflowSteps'

const STEP_ICONS = {
  Action: ActionIcon,
  Wait: WaitIcon,
  WaitForEvent: EventIcon,
  If: BranchIcon,
}

export function workflowNodes(doc, errors = {}) {
  return [
    triggerNode(doc),
    ...layoutSteps(doc.actions || []).map(({ node, position }) =>
      stepNode(node, position, errors),
    ),
  ]
}

export function workflowEdges(actions = []) {
  const edges = []
  appendEdges(actions, 'trigger', null, edges)
  return edges
}

function triggerNode(doc) {
  return {
    id: 'trigger',
    type: 'automation',
    position: { x: 0, y: 0 },
    data: {
      icon: TriggerIcon,
      isTrigger: true,
      kicker: __('Trigger'),
      label: triggerLabel(doc),
    },
  }
}

function triggerLabel(doc) {
  return doc.trigger_type
    ? doc.trigger_type.replace(/^Doc /, 'Record ')
    : __('Add a Trigger')
}

function stepNode(node, position, errors) {
  return {
    id: node._id,
    type: 'automation',
    position,
    data: {
      step: node,
      icon: STEP_ICONS[node.step_type] || ActionIcon,
      kicker: kickerFor(node),
      label: labelFor(node),
      error: Boolean(errors[node._id]?.length),
    },
  }
}

function kickerFor(node) {
  if (node.step_type === 'If') return __('Condition')
  if (node.step_type === 'WaitForEvent') return __('Wait for event')
  if (node.step_type === 'Wait') return __('Wait')
  return node.target && node.target !== 'trigger'
    ? __('Action on {0}', [node.target])
    : __('Action')
}

function labelFor(node) {
  if (node.step_type === 'If')
    return node.step_condition || __('Set a condition')
  if (node.step_type === 'Wait') return __('Pause the run')
  if (node.step_type === 'WaitForEvent')
    return parseParams(node).event_name || __('Pick an event')
  return node.action_type || __('Configure action')
}

function parseParams(node) {
  try {
    return JSON.parse(node.params || '{}')
  } catch {
    return {}
  }
}

function appendEdges(nodes, sourceId, label, edges) {
  let previous = sourceId
  nodes.forEach((node, index) => {
    edges.push(edge(previous, node._id, index === 0 ? label : null))
    if (node.step_type === 'If') appendBranchEdges(node, edges)
    previous = node._id
  })
}

function appendBranchEdges(node, edges) {
  appendEdges(node.children.If, node._id, __('If'), edges)
  appendEdges(node.children.Else, node._id, __('Else'), edges)
}

function edge(source, target, label) {
  return { id: `${source}->${target}`, source, target, label, animated: true }
}
