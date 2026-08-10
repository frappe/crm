import ActionIcon from '~icons/lucide/zap'
import BranchIcon from '~icons/lucide/git-branch'
import EventIcon from '~icons/lucide/webhook'
import TriggerIcon from '~icons/lucide/play'
import WaitIcon from '~icons/lucide/timer'
import { actionSchema } from './workflowCapabilities'
import { summarizeCondition } from './workflowConditions'
import { armLabels, isBranching, layoutSteps } from './workflowSteps'
import { triggerDefinition } from './workflowTriggers'

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
  const trigger = triggerDefinition(doc.trigger_type)
  return {
    id: 'trigger',
    type: 'automation',
    position: { x: 0, y: 0 },
    data: {
      icon: trigger?.icon || TriggerIcon,
      isTrigger: true,
      empty: !doc.trigger_type,
      kicker: __('Trigger'),
      label: trigger?.label || __('Start from scratch'),
      detail: doc.trigger_type
        ? __('on {0}', [doc.document_type])
        : __('Pick what starts this automation'),
    },
  }
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
      arms: isBranching(node) ? armLabels(node) : null,
      error: Boolean(errors[node._id]?.length),
    },
  }
}

function kickerFor(node) {
  if (node.step_type === 'If') return __('Condition')
  if (node.step_type === 'WaitForEvent') return __('Wait for')
  if (node.step_type === 'Wait') return __('Wait')
  return node.target && node.target !== 'trigger'
    ? __('Action on {0}', [node.target])
    : __('Action')
}

/** Nodes read as sentences, not class names - the canvas is the first thing anyone scans. */
function labelFor(node) {
  if (node.step_type === 'If')
    return node.step_condition
      ? summarizeCondition(node.step_condition)
      : __('Set a condition')
  if (node.step_type === 'Wait') return waitLabel(node)
  if (node.step_type === 'WaitForEvent') return eventLabel(node)
  return actionLabel(node)
}

function waitLabel(node) {
  const { value, unit } = parseParams(node)
  return value
    ? __('Wait {0} {1}', [value, unit || 'Minutes'])
    : __('Pause the run')
}

function eventLabel(node) {
  const { event_name: event } = parseParams(node)
  return event ? prettyEvent(event) : __('Pick an event')
}

/** `crm.prospect_message_received` reads as "Prospect message received". */
function prettyEvent(event) {
  const words = String(event).split('.').pop().replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function actionLabel(node) {
  if (!node.action_type) return __('Configure action')
  const schema = actionSchema(null, node.action_type)
  const detail = paramSummary(schema, parseParams(node))
  const label = schema?.label || node.action_type
  return detail ? `${label}: ${detail}` : label
}

const SUMMARY_FIELDTYPES = [
  'Data',
  'Select',
  'Link',
  'Int',
  'Float',
  'Currency',
  'Percent',
]

/** The first couple of simple params, so "Set Lead Temperature" becomes "…: Warm". */
function paramSummary(schema, params) {
  return (schema?.params_schema || [])
    .filter((field) => SUMMARY_FIELDTYPES.includes(field.fieldtype))
    .map((field) => params[field.fieldname])
    .filter((value) => value !== undefined && value !== null && value !== '')
    .slice(0, 2)
    .join(', ')
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
    if (isBranching(node)) appendBranchEdges(node, edges)
    previous = node._id
  })
}

function appendBranchEdges(node, edges) {
  const arms = armLabels(node)
  appendEdges(node.children.If, node._id, arms.If, edges)
  appendEdges(node.children.Else, node._id, arms.Else, edges)
}

function edge(source, target, label) {
  return { id: `${source}->${target}`, source, target, label, animated: true }
}
