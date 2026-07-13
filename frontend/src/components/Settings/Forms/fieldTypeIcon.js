import LucideType from '~icons/lucide/type'
import LucideAlignLeft from '~icons/lucide/align-left'
import LucideMail from '~icons/lucide/mail'
import LucidePhone from '~icons/lucide/phone'
import LucideHash from '~icons/lucide/hash'
import LucideChevronsUpDown from '~icons/lucide/chevrons-up-down'
import LucideCalendar from '~icons/lucide/calendar'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucideLink from '~icons/lucide/link'

// map a field (fieldtype + options) to the lucide icon shown next to its label.
// shared by the field cards and the hidden-fields list so they stay identical.
export function fieldTypeIcon(field) {
  if (field?.options === 'Email') return LucideMail
  switch (field?.fieldtype) {
    case 'Select':
      return LucideChevronsUpDown
    case 'Int':
    case 'Float':
    case 'Currency':
      return LucideHash
    case 'Date':
      return LucideCalendar
    case 'Datetime':
      return LucideCalendarClock
    case 'Check':
      return LucideSquareCheck
    case 'Phone':
      return LucidePhone
    case 'Small Text':
    case 'Text':
    case 'Long Text':
      return LucideAlignLeft
    case 'Link':
      return LucideLink
    default:
      return LucideType
  }
}

export function fieldTypeLabel(field) {
  return field?.options === 'Email' ? 'Email' : field?.fieldtype
}
