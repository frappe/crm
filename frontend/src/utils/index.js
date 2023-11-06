import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import { usersStore } from '@/stores/users'
import { useDateFormat, useTimeAgo } from '@vueuse/core'
import { toast } from 'frappe-ui'
import { h, computed } from 'vue'

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
  Open: { label: 'Open', color: '!text-gray-600' },
  Contacted: {
    label: 'Contacted',
    color: '!text-orange-600',
  },
  Nurture: {
    label: 'Nurture',
    color: '!text-blue-600',
  },
  Qualified: {
    label: 'Qualified',
    color: '!text-green-600',
  },
  Unqualified: {
    label: 'Unqualified',
    color: '!text-red-600',
  },
  Junk: { label: 'Junk', color: '!text-purple-600' },
}

export const dealStatuses = {
  Qualification: {
    label: 'Qualification',
    color: '!text-gray-600',
  },
  'Demo/Making': {
    label: 'Demo/Making',
    color: '!text-orange-600',
  },
  'Proposal/Quotation': {
    label: 'Proposal/Quotation',
    color: '!text-blue-600',
  },
  Negotiation: {
    label: 'Negotiation',
    color: '!text-yellow-600',
  },
  'Ready to Close': {
    label: 'Ready to Close',
    color: '!text-purple-600',
  },
  Won: { label: 'Won', color: '!text-green-600' },
  Lost: { label: 'Lost', color: '!text-red-600' },
}

export function statusDropdownOptions(data, doctype, action) {
  let statuses = doctype == 'deal' ? dealStatuses : leadStatuses
  let options = []
  for (const status in statuses) {
    options.push({
      label: statuses[status].label,
      icon: () => h(IndicatorIcon, { class: statuses[status].color }),
      onClick: () => {
        data.status = statuses[status].label
        action && action('status', statuses[status].label)
      },
    })
  }
  return options
}

export function taskStatusOptions(action, data) {
  return ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled'].map(
    (status) => {
      return {
        icon: () => h(TaskStatusIcon, { status }),
        label: status,
        onClick: () => action && action(status, data),
      }
    }
  )
}

export function taskPriorityOptions(action, data) {
  return ['Low', 'Medium', 'High'].map((priority) => {
    return {
      label: priority,
      icon: () => h(TaskPriorityIcon, { priority }),
      onClick: () => action && action(priority, data),
    }
  })
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

export function startCase(str) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

const { users } = usersStore()

export const activeAgents = computed(() => {
  const nonAgents = ['Administrator', 'admin@example.com', 'Guest']
  return users.data
    .filter((user) => !nonAgents.includes(user.name))
    .sort((a, b) => a.full_name - b.full_name)
    .map((user) => {
      return {
        label: user.full_name,
        value: user.email,
        ...user,
      }
    })
})
