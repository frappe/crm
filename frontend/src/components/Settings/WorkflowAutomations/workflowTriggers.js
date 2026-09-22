import AlarmIcon from '~icons/lucide/alarm-clock'
import BadgeCheckIcon from '~icons/lucide/badge-check'
import CancelIcon from '~icons/lucide/circle-slash'
import DealLostIcon from '~icons/lucide/circle-x'
import ChangedIcon from '~icons/lucide/pencil-line'
import CreatedIcon from '~icons/lucide/file-plus-corner'
import DeletedIcon from '~icons/lucide/trash-2'
import DateIcon from '~icons/lucide/calendar-clock'
import EventIcon from '~icons/lucide/webhook'
import HandshakeIcon from '~icons/lucide/handshake'
import InboxIcon from '~icons/lucide/inbox'
import ManualIcon from '~icons/lucide/hand'
import MailIcon from '~icons/lucide/mail'
import ScheduleIcon from '~icons/lucide/clock'
import SubmitIcon from '~icons/lucide/send'
import StageIcon from '~icons/lucide/git-branch'
import TrophyIcon from '~icons/lucide/trophy'
import UpdatedIcon from '~icons/lucide/refresh-cw'
import { capabilitiesFor } from './workflowCapabilities'
import { ICON_TONES } from './workflowIcons'

export const documentTriggers = [
  {
    value: 'Doc Created',
    icon: CreatedIcon,
    ...ICON_TONES.blue,
    label: __('Record is created'),
    description: __('Start a run whenever a new record is created.'),
  },
  {
    value: 'Doc Updated',
    icon: UpdatedIcon,
    ...ICON_TONES.cyan,
    label: __('Record is updated'),
    description: __('Start a run whenever an existing record is saved.'),
  },
  {
    value: 'Field Value Changed',
    icon: ChangedIcon,
    ...ICON_TONES.violet,
    label: __('Field value changes'),
    description: __('Watch one field and run when it moves to a new value.'),
  },
  {
    value: 'Doc Deleted',
    icon: DeletedIcon,
    ...ICON_TONES.red,
    label: __('Record is deleted'),
    description: __('Start a run just after a record is deleted.'),
  },
  {
    value: 'Doc Submitted',
    icon: SubmitIcon,
    ...ICON_TONES.green,
    label: __('Record is submitted'),
    description: __('Start a run when a submittable record is submitted.'),
  },
  {
    value: 'Doc Cancelled',
    icon: CancelIcon,
    ...ICON_TONES.gray,
    label: __('Record is cancelled'),
    description: __('Start a run when a submitted record is cancelled.'),
  },
]

export const otherTriggers = [
  {
    value: 'Manual',
    icon: ManualIcon,
    ...ICON_TONES.teal,
    label: __('Launch manually'),
    description: __('Run only when someone starts it from a record.'),
  },
  {
    value: 'Scheduled',
    icon: ScheduleIcon,
    ...ICON_TONES.amber,
    label: __('On a schedule'),
    description: __('Run on a repeating schedule you define with cron.'),
  },
  {
    value: 'Date Based',
    icon: DateIcon,
    ...ICON_TONES.orange,
    label: __('On a date'),
    description: __('Run before or after a date stored on the record.'),
  },
  {
    value: 'Custom Event',
    icon: EventIcon,
    ...ICON_TONES.pink,
    label: __('Custom event'),
    description: __('Run when the app raises a named event you pick.'),
  },
]

/**
 * Domain events that are *about* this DocType, as triggers in their own right. The flow still
 * stores them as a Custom Event; naming them here just saves picking the event separately.
 * The value carries the event so picker options stay unique.
 */
export function eventTriggers(doctype) {
  return (capabilitiesFor(doctype)?.trigger_events || []).map((event) => ({
    ...eventStyle(event.value),
    value: `Custom Event:${event.value}`,
    label: event.label,
    description: event.description,
  }))
}

const EVENT_STYLES = {
  'crm.prospect_message_sent': { icon: MailIcon, ...ICON_TONES.blue },
  'crm.prospect_message_received': { icon: InboxIcon, ...ICON_TONES.teal },
  'crm.lead_qualified': { icon: BadgeCheckIcon, ...ICON_TONES.green },
  'crm.lead_converted': { icon: HandshakeIcon, ...ICON_TONES.purple },
  'crm.deal_stage_changed': { icon: StageIcon, ...ICON_TONES.violet },
  'crm.deal_won': { icon: TrophyIcon, ...ICON_TONES.green },
  'crm.deal_lost': { icon: DealLostIcon, ...ICON_TONES.red },
  'crm.task_overdue': { icon: AlarmIcon, ...ICON_TONES.amber },
}

function eventStyle(eventName) {
  return EVENT_STYLES[eventName] || { icon: EventIcon, ...ICON_TONES.pink }
}

/** The picker value a flow currently sits on. */
export function triggerValue(doc) {
  if (doc?.trigger_type === 'Custom Event' && doc.custom_event)
    return `Custom Event:${doc.custom_event}`
  return doc?.trigger_type || ''
}

/** Split a picker value back into the stored trigger type and event. */
export function triggerFromValue(value) {
  const [type, event = ''] = String(value || '').split(/:(.*)/)
  return { trigger_type: type, custom_event: event }
}

/** Combobox-shaped for the canvas picker; the inspector renders the lists directly. */
export function triggerGroups(doctype) {
  const events = eventTriggers(doctype)
  return [
    { group: __('Records'), options: documentTriggers },
    ...(events.length ? [{ group: __('Activity'), options: events }] : []),
    { group: __('Others'), options: otherTriggers },
  ]
}

/** A Custom Event flow is named by its event, so the trigger node reads as the happening. */
export function triggerDefinition(doc) {
  const value = triggerValue(doc)
  return [
    ...documentTriggers,
    ...otherTriggers,
    ...eventTriggers(doc?.document_type),
  ].find((trigger) => trigger.value === value)
}
