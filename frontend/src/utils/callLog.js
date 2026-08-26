import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { getMeta } from '@/stores/meta'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Call Log')

export function getCallLogDetail(row, log, columns = []) {
  let incoming = log.type === 'Incoming'

  if (row === 'duration') {
    return {
      label: log._duration,
      icon: 'clock',
    }
  } else if (row === 'caller') {
    return {
      name: log.caller,
      label: log._caller?.label,
      image: log._caller?.image,
    }
  } else if (row === 'receiver') {
    return {
      name: log.receiver,
      label: log._receiver?.label,
      image: log._receiver?.image,
    }
  } else if (row === 'type') {
    return {
      label: log.type,
      icon: incoming ? 'phone-incoming' : 'phone-outgoing',
    }
  } else if (row === 'status') {
    return {
      label: getCallStatusLabel(log.status, log.type),
      color: statusColorMap[log.status],
    }
  } else if (['modified', 'creation'].includes(row)) {
    return timestampCell(log[row])
  }

  let fieldType = columns?.find((col) => (col.key || col.value) == row)?.type

  if (fieldType && ['Date', 'Datetime'].includes(fieldType)) {
    return formatDate(log[row], '', true, fieldType == 'Datetime')
  }

  if (fieldType && fieldType == 'Currency') {
    return getFormattedCurrency(row, log)
  }

  if (fieldType && fieldType == 'Float') {
    return getFormattedFloat(row, log)
  }

  if (fieldType && fieldType == 'Percent') {
    return getFormattedPercent(row, log)
  }

  return log[row]
}

export const statusLabelMap = {
  Completed: __('Completed'),
  Initiated: __('Initiated'),
  Busy: __('Declined'),
  Failed: __('Failed'),
  Queued: __('Queued'),
  Canceled: __('Canceled'),
  Ringing: __('Ringing'),
  'No Answer': __('No Answer'),
  'In Progress': __('In Progress'),
}

// 'No Answer' only reads as "Missed Call" for incoming calls — an unanswered
// outgoing call wasn't missed by the CRM user who placed it.
export function getCallStatusLabel(status, type) {
  if (status === 'No Answer' && type === 'Incoming') {
    return __('Missed Call')
  }
  return statusLabelMap[status]
}

export const statusColorMap = {
  Completed: 'green',
  Busy: 'orange',
  Failed: 'red',
  Initiated: 'gray',
  Queued: 'gray',
  Canceled: 'gray',
  Ringing: 'gray',
  'No Answer': 'red',
  'In Progress': 'blue',
}
