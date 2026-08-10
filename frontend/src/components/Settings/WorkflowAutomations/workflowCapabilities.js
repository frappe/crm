import { call } from 'frappe-ui'
import { reactive } from 'vue'

/**
 * Registered triggers, relationships, fields and actions, cached per DocType. A step targeting
 * a relationship alias needs the capabilities of that alias' DocType, not the flow's, so the
 * builder loads one entry per target it can reach.
 */
const cache = reactive({})
const pending = new Set()

export function capabilitiesFor(doctype) {
  return doctype ? cache[doctype] || null : null
}

export async function loadCapabilities(doctype) {
  if (!doctype || cache[doctype] || pending.has(doctype)) return
  pending.add(doctype)
  try {
    cache[doctype] = await call(
      'frappe.automation_engine.api.get_automation_capabilities',
      {
        doctype,
      },
    )
  } finally {
    pending.delete(doctype)
  }
}

export function relationshipDefinition(doctype, relationship) {
  return (capabilitiesFor(doctype)?.relationships || []).find(
    (item) => item.name === relationship,
  )
}

export function actionSchema(doctype, actionType) {
  if (!actionType) return null
  const scoped = (capabilitiesFor(doctype)?.actions || []).find(
    (a) => a.action_type === actionType,
  )
  return scoped || anyActionSchema(actionType)
}

/** Action definitions are global; only their availability is scoped to a DocType. */
function anyActionSchema(actionType) {
  for (const capabilities of Object.values(cache)) {
    const match = (capabilities.actions || []).find(
      (a) => a.action_type === actionType,
    )
    if (match) return match
  }
  return null
}

/**
 * Every record alias a step may target: the trigger, the flow's predeclared relationship
 * aliases, and the destination aliases of steps that run earlier.
 */
export function aliasTargets(
  documentType,
  relationships = [],
  earlierSteps = [],
) {
  const targets = [
    { alias: 'trigger', doctype: documentType, label: __('Trigger record') },
  ]
  relationships.forEach((item) => addRelationshipAlias(targets, item))
  earlierSteps.forEach((step) => addOutputAlias(targets, step))
  return targets
}

function addRelationshipAlias(targets, item) {
  if (!item.alias || !item.relationship) return
  const source = targets.find(
    (target) => target.alias === (item.source || 'trigger'),
  )
  const definition = relationshipDefinition(source?.doctype, item.relationship)
  targets.push({
    alias: item.alias,
    doctype: item.target_doctype || definition?.target_doctype || null,
    label: definition?.label || item.relationship,
  })
}

function addOutputAlias(targets, step) {
  if (!step.output_alias) return
  const action = actionSchema(null, step.action_type)
  const declared = action?.output_schema?.destination_reference?.doctype
  targets.push({
    alias: step.output_alias,
    doctype:
      (declared === 'Dynamic' ? stepParams(step).doctype : declared) || null,
    label: __('Output of {0}', [
      step.step_key || action?.label || step.action_type,
    ]),
  })
}

export function stepParams(step) {
  try {
    return JSON.parse(step.params || '{}')
  } catch {
    return {}
  }
}
