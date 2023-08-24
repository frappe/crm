import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { useDateFormat, useTimeAgo } from '@vueuse/core'
import { h } from 'vue'

export function dateFormat(date, format) {
  const _format = format || 'DD-MM-YYYY HH:mm:ss'
  return useDateFormat(date, _format).value
}

export function timeAgo(date) {
  return useTimeAgo(date).value
}

export const dateTooltipFormat = 'ddd, MMM D, YYYY h:mm A'

export const leadStatuses = {
  Open: { label: 'Open', color: '!text-gray-600' },
  Contacted: { label: 'Contacted', color: '!text-orange-600' },
  Nurture: { label: 'Nurture', color: '!text-blue-600' },
  Qualified: { label: 'Qualified', color: '!text-green-600' },
  Unqualified: { label: 'Unqualified', color: '!text-red-600' },
  Junk: { label: 'Junk', color: '!text-purple-600' },
}

export const dealStatuses = {
  Qualification: { label: 'Qualification', color: '!text-gray-600' },
  'Demo/Making': { label: 'Demo/Making', color: '!text-orange-600' },
  'Proposal/Quotation': {
    label: 'Proposal/Quotation',
    color: '!text-blue-600',
  },
  Negotiation: { label: 'Negotiation', color: '!text-yellow-600' },
  'Ready to Close': { label: 'Ready to Close', color: '!text-purple-600' },
  Won: { label: 'Won', color: '!text-green-600' },
  Lost: { label: 'Lost', color: '!text-red-600' },
}

export function statusDropdownOptions(data, doctype) {
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
      },
    })
  }
  return options
}
