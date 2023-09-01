import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { useDateFormat, useTimeAgo } from '@vueuse/core'
import { toast } from 'frappe-ui'
import { h } from 'vue'

export function createToast(options) {
  toast({
    position: 'bottom-right',
    ...options,
  })
}

export function dateFormat(date, format) {
  const _format = format || 'DD-MM-YYYY HH:mm:ss'
  return useDateFormat(date, _format).value
}

export function timeAgo(date) {
  return useTimeAgo(date).value
}

export const dateTooltipFormat = 'ddd, MMM D, YYYY h:mm A'

export const leadStatuses = {
  Open: { label: 'Open', color: '!text-gray-600', bgColor: '!bg-gray-200' },
  Contacted: {
    label: 'Contacted',
    color: '!text-orange-600',
    bgColor: '!bg-orange-200',
  },
  Nurture: {
    label: 'Nurture',
    color: '!text-blue-600',
    bgColor: '!bg-blue-200',
  },
  Qualified: {
    label: 'Qualified',
    color: '!text-green-600',
    bgColor: '!bg-green-200',
  },
  Unqualified: {
    label: 'Unqualified',
    color: '!text-red-600',
    bgColor: '!bg-red-200',
  },
  Junk: { label: 'Junk', color: '!text-purple-600', bgColor: '!bg-purple-200' },
}

export const dealStatuses = {
  Qualification: {
    label: 'Qualification',
    color: '!text-gray-600',
    bgColor: '!bg-gray-200',
  },
  'Demo/Making': {
    label: 'Demo/Making',
    color: '!text-orange-600',
    bgColor: '!bg-orange-200',
  },
  'Proposal/Quotation': {
    label: 'Proposal/Quotation',
    color: '!text-blue-600',
    bgColor: '!bg-blue-200',
  },
  Negotiation: {
    label: 'Negotiation',
    color: '!text-yellow-600',
    bgColor: '!bg-yellow-100',
  },
  'Ready to Close': {
    label: 'Ready to Close',
    color: '!text-purple-600',
    bgColor: '!bg-purple-200',
  },
  Won: { label: 'Won', color: '!text-green-600', bgColor: '!bg-green-200' },
  Lost: { label: 'Lost', color: '!text-red-600', bgColor: '!bg-red-200' },
}

export function statusDropdownOptions(data, doctype, action) {
  let statuses = leadStatuses
  if (doctype == 'deal') {
    statuses = dealStatuses
  }
  let options = []
  for (const status in statuses) {
    options.push({
      label: statuses[status].label,
      icon: () => h(IndicatorIcon, { class: statuses[status].color }),
      onClick: () => {
        if (doctype == 'deal') {
          data.deal_status = statuses[status].label
        } else {
          data.status = statuses[status].label
        }
        let field = doctype == 'deal' ? 'deal_status' : 'status'
        action && action(field, statuses[status].label)
      },
    })
  }
  return options
}

export function openWebsite(url) {
  window.open(url, '_blank')
}

export function htmlToText(html) {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

export function secondsToDuration(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const _seconds = Math.floor((seconds % 3600) % 60)

  if (hours == 0 && minutes == 0) {
    return `${_seconds}s`
  } else if (hours == 0) {
    return `${minutes}m ${_seconds}s`
  }
  return `${hours}h ${minutes}m ${_seconds}s`
}

export function formatNumberIntoCurrency(value) {
  if (value) {
    return value.toLocaleString('en-IN', {
      maximumFractionDigits: 2,
      style: 'currency',
      currency: 'INR',
    })
  }
  return ''
}
