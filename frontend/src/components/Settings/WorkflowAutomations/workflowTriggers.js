import CancelIcon from '~icons/lucide/circle-slash'
import ChangedIcon from '~icons/lucide/pencil-line'
import CreatedIcon from '~icons/lucide/list-plus'
import DeletedIcon from '~icons/lucide/trash-2'
import EventIcon from '~icons/lucide/webhook'
import ManualIcon from '~icons/lucide/hand'
import ScheduleIcon from '~icons/lucide/clock'
import SubmitIcon from '~icons/lucide/send'
import UpdatedIcon from '~icons/lucide/refresh-cw'

export const documentTriggers = [
  {
    value: 'Doc Created',
    icon: CreatedIcon,
    label: __('Record is created'),
    description: __('Start a run whenever a new record is created.'),
  },
  {
    value: 'Doc Updated',
    icon: UpdatedIcon,
    label: __('Record is updated'),
    description: __('Start a run whenever an existing record is saved.'),
  },
  {
    value: 'Field Value Changed',
    icon: ChangedIcon,
    label: __('Field value changes'),
    description: __('Watch one field and run when it moves to a new value.'),
  },
  {
    value: 'Doc Deleted',
    icon: DeletedIcon,
    label: __('Record is deleted'),
    description: __('Start a run just after a record is deleted.'),
  },
  {
    value: 'Doc Submitted',
    icon: SubmitIcon,
    label: __('Record is submitted'),
    description: __('Start a run when a submittable record is submitted.'),
  },
  {
    value: 'Doc Cancelled',
    icon: CancelIcon,
    label: __('Record is cancelled'),
    description: __('Start a run when a submitted record is cancelled.'),
  },
]

export const otherTriggers = [
  {
    value: 'Manual',
    icon: ManualIcon,
    label: __('Launch manually'),
    description: __('Run only when someone starts it from a record.'),
  },
  {
    value: 'Scheduled',
    icon: ScheduleIcon,
    label: __('On a schedule'),
    description: __('Run on a repeating schedule you define with cron.'),
  },
  {
    value: 'Date Based',
    icon: ScheduleIcon,
    label: __('On a date'),
    description: __('Run before or after a date stored on the record.'),
  },
  {
    value: 'Custom Event',
    icon: EventIcon,
    label: __('Custom event'),
    description: __('Run when the app raises a named event you pick.'),
  },
]

/** Grouped for the canvas picker; the inspector renders the two lists directly. */
export function triggerGroups() {
  return [
    { label: __('Records'), options: documentTriggers },
    { label: __('Others'), options: otherTriggers },
  ]
}

export function triggerDefinition(value) {
  return [...documentTriggers, ...otherTriggers].find(
    (trigger) => trigger.value === value,
  )
}
