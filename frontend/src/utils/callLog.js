import {
  secondsToDuration,
  dateFormat,
  dateTooltipFormat,
  timeAgo,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'

const { getUser } = usersStore()
const { getContact, getLeadContact } = contactsStore()

export function getCallLogDetail(row, log) {
  let incoming = log.type === 'Incoming'

  if (row === 'caller') {
    return {
      label: incoming
        ? getContact(log.from)?.full_name ||
          getLeadContact(log.from)?.full_name ||
          'Unknown'
        : getUser(log.caller).full_name,
      image: incoming
        ? getContact(log.from)?.image || getLeadContact(log.from)?.image
        : getUser(log.caller).user_image,
    }
  } else if (row === 'receiver') {
    return {
      label: incoming
        ? getUser(log.receiver).full_name
        : getContact(log.to)?.full_name ||
          getLeadContact(log.to)?.full_name ||
          'Unknown',
      image: incoming
        ? getUser(log.receiver).user_image
        : getContact(log.to)?.image || getLeadContact(log.to)?.image,
    }
  } else if (row === 'duration') {
    return {
      label: secondsToDuration(log.duration),
      icon: 'clock',
    }
  } else if (row === 'type') {
    return {
      label: log.type,
      icon: incoming ? 'phone-incoming' : 'phone-outgoing',
    }
  } else if (row === 'status') {
    return {
      label: statusLabelMap[log.status],
      color: statusColorMap[log.status],
    }
  } else if (['modified', 'creation'].includes(row)) {
    return {
      label: dateFormat(log[row], dateTooltipFormat),
      timeAgo: __(timeAgo(log[row])),
    }
  }
  return log[row]
}

export const statusLabelMap = {
  Completed: 'Completed',
  Initiated: 'Initiated',
  Busy: 'Declined',
  Failed: 'Failed',
  Queued: 'Queued',
  Cancelled: 'Cancelled',
  Ringing: 'Ringing',
  'No Answer': 'Missed Call',
  'In Progress': 'In Progress',
}

export const statusColorMap = {
  Completed: 'green',
  Busy: 'orange',
  Failed: 'red',
  Initiated: 'gray',
  Queued: 'gray',
  Cancelled: 'gray',
  Ringing: 'gray',
  'No Answer': 'red',
  'In Progress': 'blue',
}
