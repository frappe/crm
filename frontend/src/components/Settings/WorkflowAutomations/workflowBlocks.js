import BranchIcon from '~icons/lucide/git-branch'
import EventIcon from '~icons/lucide/webhook'
import WaitIcon from '~icons/lucide/timer'
import { actionIcon } from './workflowIcons'
import { capabilitiesFor } from './workflowCapabilities'

const flowBlocks = [
  {
    value: 'If',
    icon: BranchIcon,
    tone: 'text-ink-green-7',
    label: __('If / Else'),
    description: __('Split the run into two arms on a condition.'),
    values: { step_type: 'If' },
  },
  {
    value: 'Wait',
    icon: WaitIcon,
    tone: 'text-ink-amber-7',
    label: __('Wait'),
    description: __('Pause the run for a fixed amount of time.'),
    // Seeded, not just shown as a placeholder: the editor's fallback is display-only, so a
    // step the user never opens would save without the unit it appears to have.
    values: { step_type: 'Wait', params: JSON.stringify({ unit: 'Minutes' }) },
  },
  {
    value: 'WaitForEvent',
    icon: EventIcon,
    tone: 'text-ink-amber-7',
    label: __('Wait for event'),
    description: __('Pause until an event is raised for this record.'),
    values: {
      step_type: 'WaitForEvent',
      params: JSON.stringify({ timeout_unit: 'Days' }),
    },
  },
]

/** Flow control first, then every action the trigger DocType registers. */
export function blockGroups(doctype) {
  const actions = (capabilitiesFor(doctype)?.actions || []).map(actionBlock)
  return [
    { group: __('Flow'), options: flowBlocks },
    { group: __('Actions'), options: actions },
  ].filter((group) => group.options.length)
}

function actionBlock(action) {
  return {
    value: action.action_type,
    ...actionIcon(action.action_type),
    label: action.label || action.action_type,
    description: action.description || '',
    values: { step_type: 'Action', action_type: action.action_type },
  }
}
