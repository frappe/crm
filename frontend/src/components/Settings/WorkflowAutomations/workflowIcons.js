import ActionIcon from '~icons/lucide/zap'
import AssignIcon from '~icons/lucide/user-plus'
import BranchIcon from '~icons/lucide/git-branch'
import ConvertIcon from '~icons/lucide/handshake'
import CreateIcon from '~icons/lucide/file-plus'
import EmailIcon from '~icons/lucide/mail'
import EventIcon from '~icons/lucide/webhook'
import IncrementIcon from '~icons/lucide/trending-up'
import NotifyIcon from '~icons/lucide/bell-ring'
import ScoreIcon from '~icons/lucide/gauge'
import ScriptIcon from '~icons/lucide/code'
import SetFieldIcon from '~icons/lucide/pencil-line'
import TemperatureIcon from '~icons/lucide/thermometer'
import TriggerIcon from '~icons/lucide/play'
import WaitIcon from '~icons/lucide/timer'
import WebhookIcon from '~icons/lucide/webhook'

/** `tone` colours a bare glyph in a list; `chip` is the tile it sits in on a node card. */
const TONES = {
  blue: {
    tone: 'text-ink-blue-7',
    chip: 'bg-surface-blue-3 border-outline-blue-7',
  },
  green: {
    tone: 'text-ink-green-7',
    chip: 'bg-surface-green-3 border-outline-green-7',
  },
  teal: {
    tone: 'text-ink-teal-7',
    chip: 'bg-surface-teal-3 border-outline-teal-7',
  },
  amber: {
    tone: 'text-ink-amber-7',
    chip: 'bg-surface-amber-3 border-outline-amber-7',
  },
  violet: {
    tone: 'text-ink-violet-7',
    chip: 'bg-surface-violet-3 border-outline-violet-7',
  },
  cyan: {
    tone: 'text-ink-cyan-7',
    chip: 'bg-surface-cyan-3 border-outline-cyan-7',
  },
  orange: {
    tone: 'text-ink-orange-7',
    chip: 'bg-surface-orange-3 border-outline-orange-7',
  },
  pink: {
    tone: 'text-ink-pink-7',
    chip: 'bg-surface-pink-3 border-outline-pink-7',
  },
  red: {
    tone: 'text-ink-red-6',
    chip: 'bg-surface-red-3 border-outline-red-6',
  },
  gray: {
    tone: 'text-ink-gray-7',
    chip: 'bg-surface-gray-3 border-outline-gray-4',
  },
  purple: {
    tone: 'text-ink-purple-7',
    chip: 'bg-surface-purple-3 border-outline-purple-7',
  },
}

/** One icon and tone per action, so a list of them is scannable rather than eleven zaps. */
const ACTION_STYLES = {
  SetFieldValue: { icon: SetFieldIcon, ...TONES.blue },
  IncrementFieldValue: { icon: IncrementIcon, ...TONES.cyan },
  CreateDocument: { icon: CreateIcon, ...TONES.green },
  SendNotification: { icon: NotifyIcon, ...TONES.teal },
  AssignToUser: { icon: AssignIcon, ...TONES.violet },
  CallWebhook: { icon: WebhookIcon, ...TONES.pink },
  RunScript: { icon: ScriptIcon, ...TONES.gray },
  AdjustLeadScore: { icon: ScoreIcon, ...TONES.orange },
  SetLeadTemperature: { icon: TemperatureIcon, ...TONES.red },
  ConvertLeadToDeal: { icon: ConvertIcon, ...TONES.purple },
  SendCRMEmail: { icon: EmailIcon, ...TONES.violet },
}

const STEP_STYLES = {
  Action: { icon: ActionIcon, ...TONES.blue },
  Wait: { icon: WaitIcon, ...TONES.amber },
  WaitForEvent: { icon: EventIcon, ...TONES.amber },
  If: { icon: BranchIcon, ...TONES.green },
}

export const TRIGGER_STYLE = { icon: TriggerIcon, ...TONES.blue }

export function actionIcon(actionType) {
  return ACTION_STYLES[actionType] || STEP_STYLES.Action
}

export function stepTypeIcon(stepType) {
  return STEP_STYLES[stepType] || STEP_STYLES.Action
}

/** An action step wears the icon of the action it runs, not a generic bolt. */
export function stepIcon(step) {
  return step.step_type === 'Action'
    ? actionIcon(step.action_type)
    : stepTypeIcon(step.step_type)
}
