import { formatDate, timeAgo } from '@/utils'
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
      label: log._caller?.label,
      image: log._caller?.image,
    }
  } else if (row === 'receiver') {
    return {
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
      label: statusLabelMap[log.status],
      color: statusColorMap[log.status],
    }
  } else if (['modified', 'creation'].includes(row)) {
    return {
      label: formatDate(log[row]),
      timeAgo: __(timeAgo(log[row])),
    }
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
  Completed: 'Completed',
  Initiated: 'Initiated',
  Busy: 'Declined',
  Failed: 'Failed',
  Queued: 'Queued',
  Canceled: 'Canceled',
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
  Canceled: 'gray',
  Ringing: 'gray',
  'No Answer': 'red',
  'In Progress': 'blue',
}
