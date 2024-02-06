import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import { useDateFormat, useTimeAgo } from '@vueuse/core'
import { usersStore } from '@/stores/users'
import { toast } from 'frappe-ui'
import { h } from 'vue'

export function createToast(options) {
  toast({
    position: 'bottom-right',
    ...options,
  })
}

export function formatTime(seconds) {
  const days = Math.floor(seconds / (3600 * 24))
  const hours = Math.floor((seconds % (3600 * 24)) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)

  let formattedTime = ''

  if (days > 0) {
    formattedTime += `${days}d `
  }

  if (hours > 0 || days > 0) {
    formattedTime += `${hours}h `
  }

  if (minutes > 0 || hours > 0 || days > 0) {
    formattedTime += `${minutes}m `
  }

  formattedTime += `${remainingSeconds}s`

  return formattedTime.trim()
}

export function dateFormat(date, format) {
  const _format = format || 'DD-MM-YYYY HH:mm:ss'
  return useDateFormat(date, _format).value
}

export function timeAgo(date) {
  return useTimeAgo(date).value
}

export const dateTooltipFormat = 'ddd, MMM D, YYYY h:mm A'

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

export function validateEmail(email) {
  let regExp =
    /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return regExp.test(email)
}

export function setupAssignees(data) {
  let { getUser } = usersStore()
  let assignees = data._assign || []
  data._assignedTo = assignees.map((user) => ({
    name: user,
    image: getUser(user).user_image,
    label: getUser(user).full_name,
  }))
}

export function setupCustomActions(data, obj) {
  if (!data._form_script) return []
  let script = new Function(data._form_script + '\nreturn setupForm')()
  let formScript = script(obj)
  data._customActions = formScript?.actions || []
}

export function setupBulkActions(data, obj = {}) {
  if (!data.form_script) return []
  let script = new Function(data.form_script + '\nreturn setupForm')()
  let formScript = script(obj)
  data.bulkActions = formScript?.bulk_actions || []
}

export function errorMessage(title, message) {
  createToast({
    title: title || 'Error',
    text: message,
    icon: 'x',
    iconClasses: 'text-red-600',
  })
}
