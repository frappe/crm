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

/** `tone` colours a bare glyph on a node card. */
export const ICON_TONES = {
  blue: { tone: 'text-ink-blue-5' },
  green: { tone: 'text-ink-green-5' },
  teal: { tone: 'text-ink-teal-5' },
  amber: { tone: 'text-ink-amber-5' },
  violet: { tone: 'text-ink-violet-5' },
  cyan: { tone: 'text-ink-cyan-5' },
  orange: { tone: 'text-ink-orange-5' },
  pink: { tone: 'text-ink-pink-5' },
  red: { tone: 'text-ink-red-5' },
  gray: { tone: 'text-ink-gray-6' },
  purple: { tone: 'text-ink-purple-5' },
}

/** One icon and tone per action, so a list of them is scannable rather than eleven zaps. */
const ACTION_STYLES = {
  SetFieldValue: { icon: SetFieldIcon, ...ICON_TONES.blue },
  IncrementFieldValue: { icon: IncrementIcon, ...ICON_TONES.cyan },
  CreateDocument: { icon: CreateIcon, ...ICON_TONES.green },
  SendNotification: { icon: NotifyIcon, ...ICON_TONES.amber },
  SendCRMNotification: { icon: NotifyIcon, ...ICON_TONES.amber },
  AssignToUser: { icon: AssignIcon, ...ICON_TONES.violet },
  CallWebhook: { icon: WebhookIcon, ...ICON_TONES.pink },
  RunScript: { icon: ScriptIcon, ...ICON_TONES.gray },
  AdjustLeadScore: { icon: ScoreIcon, ...ICON_TONES.orange },
  SetLeadTemperature: { icon: TemperatureIcon, ...ICON_TONES.red },
  ConvertLeadToDeal: { icon: ConvertIcon, ...ICON_TONES.purple },
  SendCRMEmail: { icon: EmailIcon, ...ICON_TONES.violet },
}

const STEP_STYLES = {
  Action: { icon: ActionIcon, ...ICON_TONES.blue },
  Wait: { icon: WaitIcon, ...ICON_TONES.amber },
  WaitForEvent: { icon: EventIcon, ...ICON_TONES.amber },
  If: { icon: BranchIcon, ...ICON_TONES.green },
}

export const TRIGGER_STYLE = { icon: TriggerIcon, ...ICON_TONES.blue }

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
