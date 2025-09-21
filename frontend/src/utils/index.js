import LucideCheck from '~icons/lucide/check'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import { usersStore } from '@/stores/users'
import { gemoji } from 'gemoji'
import { getMeta } from '@/stores/meta'
import { toast, dayjsLocal, dayjs, getConfig, FeatherIcon } from 'frappe-ui'
import { h } from 'vue'

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

export function formatDate(date, format, onlyDate = false, onlyTime = false) {
  if (!date) return ''
  format = getFormat(date, format, onlyDate, onlyTime, false)
  return dayjsLocal(date).format(format)
}

export function getFormat(
  date,
  format,
  onlyDate = false,
  onlyTime = false,
  withDate = true,
) {
  if (!date && withDate) return ''
  let dateFormat =
    window.sysdefaults.date_format
      .replace('mm', 'MM')
      .replace('yyyy', 'YYYY')
      .replace('dd', 'DD') || 'YYYY-MM-DD'
  let timeFormat = window.sysdefaults.time_format || 'HH:mm:ss'
  format = format || 'ddd, MMM D, YYYY h:mm a'

  if (onlyDate) format = dateFormat
  if (onlyTime) format = timeFormat
  if (onlyTime && onlyDate) format = `${dateFormat} ${timeFormat}`

  if (withDate) {
    return dayjs(date).format(format)
  }
  return format
}

export function timeAgo(date) {
  return prettyDate(date)
}

function getBrowserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

export function prettyDate(date, mini = false) {
  if (!date) return ''

  let systemTimezone = getConfig('systemTimezone')
  let localTimezone = getConfig('localTimezone') || getBrowserTimezone()

  if (typeof date == 'string') {
    date = dayjsLocal(date)
  }

  let nowDatetime = dayjs().tz(localTimezone || systemTimezone)
  let diff = nowDatetime.diff(date, 'seconds')

  let dayDiff = diff / 86400

  if (isNaN(dayDiff)) return ''

  if (mini) {
    // Return short format of time difference
    if (dayDiff < 0) {
      if (Math.abs(dayDiff) < 1) {
        if (Math.abs(diff) < 60) {
          return __('now')
        } else if (Math.abs(diff) < 3600) {
          return __('in {0} m', [Math.floor(Math.abs(diff) / 60)])
        } else if (Math.abs(diff) < 86400) {
          return __('in {0} h', [Math.floor(Math.abs(diff) / 3600)])
        }
      }
      if (Math.abs(dayDiff) >= 1 && Math.abs(dayDiff) < 1.5) {
        return __('tomorrow')
      } else if (Math.abs(dayDiff) < 7) {
        return __('in {0} d', [Math.floor(Math.abs(dayDiff))])
      } else if (Math.abs(dayDiff) < 31) {
        return __('in {0} w', [Math.floor(Math.abs(dayDiff) / 7)])
      } else if (Math.abs(dayDiff) < 365) {
        return __('in {0} M', [Math.floor(Math.abs(dayDiff) / 30)])
      } else {
        return __('in {0} y', [Math.floor(Math.abs(dayDiff) / 365)])
      }
    } else if (dayDiff >= 0 && dayDiff < 1) {
      if (diff < 60) {
        return __('now')
      } else if (diff < 3600) {
        return __('{0} m', [Math.floor(diff / 60)])
      } else if (diff < 86400) {
        return __('{0} h', [Math.floor(diff / 3600)])
      }
    } else {
      dayDiff = Math.floor(dayDiff)
      if (dayDiff < 7) {
        return __('{0} d', [dayDiff])
      } else if (dayDiff < 31) {
        return __('{0} w', [Math.floor(dayDiff / 7)])
      } else if (dayDiff < 365) {
        return __('{0} M', [Math.floor(dayDiff / 30)])
      } else {
        return __('{0} y', [Math.floor(dayDiff / 365)])
      }
    }
  } else {
    // Return long format of time difference
    if (dayDiff < 0) {
      if (Math.abs(dayDiff) < 1) {
        if (Math.abs(diff) < 60) {
          return __('just now')
        } else if (Math.abs(diff) < 120) {
          return __('in 1 minute')
        } else if (Math.abs(diff) < 3600) {
          return __('in {0} minutes', [Math.floor(Math.abs(diff) / 60)])
        } else if (Math.abs(diff) < 7200) {
          return __('in 1 hour')
        } else if (Math.abs(diff) < 86400) {
          return __('in {0} hours', [Math.floor(Math.abs(diff) / 3600)])
        }
      }
      if (Math.abs(dayDiff) >= 1 && Math.abs(dayDiff) < 1.5) {
        return __('tomorrow')
      } else if (Math.abs(dayDiff) < 7) {
        return __('in {0} days', [Math.floor(Math.abs(dayDiff))])
      } else if (Math.abs(dayDiff) < 31) {
        return __('in {0} weeks', [Math.floor(Math.abs(dayDiff) / 7)])
      } else if (Math.abs(dayDiff) < 365) {
        return __('in {0} months', [Math.floor(Math.abs(dayDiff) / 30)])
      } else if (Math.abs(dayDiff) < 730) {
        return __('in 1 year')
      } else {
        return __('in {0} years', [Math.floor(Math.abs(dayDiff) / 365)])
      }
    } else if (dayDiff >= 0 && dayDiff < 1) {
      if (diff < 60) {
        return __('just now')
      } else if (diff < 120) {
        return __('1 minute ago')
      } else if (diff < 3600) {
        return __('{0} minutes ago', [Math.floor(diff / 60)])
      } else if (diff < 7200) {
        return __('1 hour ago')
      } else if (diff < 86400) {
        return __('{0} hours ago', [Math.floor(diff / 3600)])
      }
    } else {
      dayDiff = Math.floor(dayDiff)
      if (dayDiff == 1) {
        return __('yesterday')
      } else if (dayDiff < 7) {
        return __('{0} days ago', [dayDiff])
      } else if (dayDiff < 14) {
        return __('1 week ago')
      } else if (dayDiff < 31) {
        return __('{0} weeks ago', [Math.floor(dayDiff / 7)])
      } else if (dayDiff < 62) {
        return __('1 month ago')
      } else if (dayDiff < 365) {
        return __('{0} months ago', [Math.floor(dayDiff / 30)])
      } else if (dayDiff < 730) {
        return __('1 year ago')
      } else {
        return __('{0} years ago', [Math.floor(dayDiff / 365)])
      }
    }
  }
}

export function taskStatusOptions(action, data) {
  let options = ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled']
  let statusMeta = getMeta('CRM Task')
    .getFields()
    ?.find((field) => field.fieldname == 'status')
  if (statusMeta) {
    options = statusMeta.options
      .map((option) => option.value)
      .filter((option) => option)
  }
  return options.map((status) => {
    return {
      icon: () => h(TaskStatusIcon, { status }),
      label: status,
      onClick: () => action && action(status, data),
    }
  })
}

export function taskPriorityOptions(action, data) {
  let options = ['Low', 'Medium', 'High']
  let priorityMeta = getMeta('CRM Task')
    .getFields()
    ?.find((field) => field.fieldname == 'priority')
  if (priorityMeta) {
    options = priorityMeta.options
      .map((option) => option.value)
      .filter((option) => option)
  }

  return options.map((priority) => {
    return {
      label: priority,
      icon: () => h(TaskPriorityIcon, { priority }),
      onClick: () => action && action(priority, data),
    }
  })
}

export function openWebsite(url) {
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url
  }
  window.open(url, '_blank')
}

export function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}

export function htmlToText(html) {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

export function startCase(str) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

export function validateEmail(email) {
  let regExp =
    /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return regExp.test(email)
}

export function parseAssignees(assignees) {
  let { getUser } = usersStore()
  return assignees.map((user) => ({
    name: user,
    image: getUser(user).user_image,
    label: getUser(user).full_name,
  }))
}

async function getFormScript(script, obj) {
  if (!script.includes('setupForm(')) return {}
  let scriptFn = new Function(script + '\nreturn setupForm')()
  let formScript = await scriptFn(obj)
  return formScript || {}
}

export async function setupCustomizations(scripts, obj) {
  if (!scripts) return []

  let statuses = []
  let actions = []
  if (Array.isArray(scripts)) {
    for (let s of scripts) {
      let _script = await getFormScript(s.script, obj)
      actions = actions.concat(_script?.actions || [])
      statuses = statuses.concat(_script?.statuses || [])
    }
  }
  return { statuses, actions }
}

async function getListScript(script, obj) {
  let scriptFn = new Function(script + '\nreturn setupList')()
  let listScript = await scriptFn(obj)
  return listScript || {}
}

export async function setupListCustomizations(data, obj = {}) {
  if (!data.list_script) return []

  let actions = []
  let bulkActions = []

  if (Array.isArray(data.list_script)) {
    for (let script of data.list_script) {
      let _script = await getListScript(script, obj)
      actions = actions.concat(_script?.actions || [])
      bulkActions = bulkActions.concat(_script?.bulk_actions || [])
    }
  } else {
    let _script = await getListScript(data.list_script, obj)
    actions = _script?.actions || []
    bulkActions = _script?.bulk_actions || []
  }

  data.listActions = actions
  data.bulkActions = bulkActions
  return { actions, bulkActions }
}

export function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(showSuccessAlert)
  } else {
    let input = document.createElement('textarea')
    document.body.appendChild(input)
    input.value = text
    input.select()
    document.execCommand('copy')
    showSuccessAlert()
    document.body.removeChild(input)
  }
  function showSuccessAlert() {
    toast.success(__('Copied to clipboard'))
  }
}

export const colors = [
  'gray',
  'blue',
  'green',
  'red',
  'pink',
  'orange',
  'amber',
  'yellow',
  'cyan',
  'teal',
  'violet',
  'purple',
  'black',
]

export function parseColor(color) {
  let textColor = `!text-${color}-600`
  if (color == 'black') {
    textColor = '!text-ink-gray-9'
  } else if (['gray', 'green'].includes(color)) {
    textColor = `!text-${color}-700`
  }

  return textColor
}

export function isEmoji(str) {
  const emojiList = gemoji.map((emoji) => emoji.emoji)
  return emojiList.includes(str)
}

export function isTouchScreenDevice() {
  return 'ontouchstart' in document.documentElement
}

export function convertArrayToString(array) {
  return array.map((item) => item).join(',')
}

export function _eval(code, context = {}) {
  let variable_names = Object.keys(context)
  let variables = Object.values(context)
  code = `let out = ${code}; return out`
  try {
    let expression_function = new Function(...variable_names, code)
    return expression_function(...variables)
  } catch (error) {
    console.log('Error evaluating the following expression:')
    console.error(code)
    throw error
  }
}

export function evaluateDependsOnValue(expression, doc) {
  if (!expression) return true
  if (!doc) return true

  let out = null

  if (typeof expression === 'boolean') {
    out = expression
  } else if (typeof expression === 'function') {
    out = expression(doc)
  } else if (expression.substr(0, 5) == 'eval:') {
    try {
      out = _eval(expression.substr(5), { doc })
    } catch (e) {
      out = true
    }
  } else {
    let value = doc[expression]
    if (Array.isArray(value)) {
      out = !!value.length
    } else {
      out = !!value
    }
  }

  return out
}

export function convertSize(size) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let unitIndex = 0
  while (size > 1024) {
    size /= 1024
    unitIndex++
  }
  return `${size?.toFixed(2)} ${units[unitIndex]}`
}

export function isImage(extention) {
  if (!extention) return false
  return ['png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'webp'].includes(
    extention.toLowerCase(),
  )
}

export function validateIsImageFile(file) {
  const extn = file.name.split('.').pop().toLowerCase()
  if (!isImage(extn)) {
    return __('Only image files are allowed')
  }
}

export function getRandom(len = 4) {
  let text = ''
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

  Array.from({ length: len }).forEach(() => {
    text += possible.charAt(Math.floor(Math.random() * possible.length))
  })

  return text
}

export function runSequentially(functions) {
  return functions.reduce((promise, fn) => {
    return promise.then(() => fn())
  }, Promise.resolve())
}

export function DropdownOption({ option, icon, selected }) {
  return h(
    'button',
    {
      class:
        'group flex w-full text-ink-gray-8 justify-between items-center rounded-md px-2 py-2 text-sm hover:bg-surface-gray-2',
    },
    [
      h('div', { class: 'flex gap-2' }, [
        icon
          ? h(FeatherIcon, {
              name: icon,
              class: ['h-4 w-4 shrink-0'],
              'aria-hidden': true,
            })
          : null,
        h('span', { class: 'whitespace-nowrap' }, option),
      ]),
      selected
        ? h(LucideCheck, {
            class: ['h-4 w-4 shrink-0 text-ink-gray-7'],
            'aria-hidden': true,
          })
        : null,
    ],
  )
}

export function copy(obj) {
  if (!obj) return obj
  return JSON.parse(JSON.stringify(obj))
}

export const convertToConditions = ({ conditions, fieldPrefix }) => {
  if (!conditions || conditions.length === 0) {
    return ''
  }

  const processCondition = (condition) => {
    if (typeof condition === 'string') {
      return condition.toLowerCase()
    }

    if (Array.isArray(condition)) {
      // Nested condition group
      if (Array.isArray(condition[0])) {
        const nestedStr = convertToConditions({
          conditions: condition,
          fieldPrefix,
        })
        return `(${nestedStr})`
      }

      // Simple condition: [fieldname, operator, value]
      const [field, operator, value] = condition
      const fieldAccess = fieldPrefix ? `${fieldPrefix}.${field}` : field

      const operatorMap = {
        equals: '==',
        '=': '==',
        '==': '==',
        '!=': '!=',
        'not equals': '!=',
        '<': '<',
        '<=': '<=',
        '>': '>',
        '>=': '>=',
        in: 'in',
        'not in': 'not in',
        like: 'like',
        'not like': 'not like',
        is: 'is',
        'is not': 'is not',
        between: 'between',
      }

      let op = operatorMap[operator.toLowerCase()] || operator

      if (
        (op === '==' || op === '!=') &&
        (String(value).toLowerCase() === 'yes' ||
          String(value).toLowerCase() === 'no')
      ) {
        let checkVal = String(value).toLowerCase() === 'yes'
        if (op === '!=') {
          checkVal = !checkVal
        }
        return checkVal ? fieldAccess : `not ${fieldAccess}`
      }

      if (op === 'is' && String(value).toLowerCase() === 'set') {
        return fieldAccess
      }
      if (
        (op === 'is' && String(value).toLowerCase() === 'not set') ||
        (op === 'is not' && String(value).toLowerCase() === 'set')
      ) {
        return `not ${fieldAccess}`
      }

      if (op === 'like') {
        return `(${fieldAccess} and "${value}" in ${fieldAccess})`
      }
      if (op === 'not like') {
        return `(${fieldAccess} and "${value}" not in ${fieldAccess})`
      }

      if (
        op === 'between' &&
        typeof value === 'string' &&
        value.includes(',')
      ) {
        const [start, end] = value.split(',').map((v) => v.trim())
        return `(${fieldAccess} >= "${start}" and ${fieldAccess} <= "${end}")`
      }

      let valueStr = ''
      if (op === 'in' || op === 'not in') {
        let items
        if (Array.isArray(value)) {
          items = value.map((v) => `"${String(v).trim()}"`)
        } else if (typeof value === 'string') {
          items = value.split(',').map((v) => `"${v.trim()}"`)
        } else {
          items = [`"${String(value).trim()}"`]
        }
        valueStr = `[${items.join(', ')}]`
        return `(${fieldAccess} and ${fieldAccess} ${op} ${valueStr})`
      }

      if (typeof value === 'string') {
        valueStr = `"${value.replace(/"/g, '\\"')}"`
      } else if (typeof value === 'number' || typeof value === 'boolean') {
        valueStr = String(value)
      } else if (value === null || value === undefined) {
        return op === '==' || op === 'is' ? `not ${fieldAccess}` : fieldAccess
      } else {
        valueStr = `"${String(value).replace(/"/g, '\\"')}"`
      }

      return `${fieldAccess} ${op} ${valueStr}`
    }

    return ''
  }

  const parts = conditions.map(processCondition)
  return parts.join(' ')
}

export function validateConditions(conditions) {
  if (!Array.isArray(conditions)) return false

  // Handle simple condition [field, operator, value]
  if (
    conditions.length === 3 &&
    typeof conditions[0] === 'string' &&
    typeof conditions[1] === 'string'
  ) {
    return conditions[0] !== '' && conditions[1] !== '' && conditions[2] !== ''
  }

  // Iterate through conditions and logical operators
  for (let i = 0; i < conditions.length; i++) {
    const item = conditions[i]

    // Skip logical operators (they will be validated by their position)
    if (item === 'and' || item === 'or') {
      // Ensure logical operators are not at start/end and not consecutive
      if (
        i === 0 ||
        i === conditions.length - 1 ||
        conditions[i - 1] === 'and' ||
        conditions[i - 1] === 'or'
      ) {
        return false
      }
      continue
    }

    // Handle nested conditions (arrays)
    if (Array.isArray(item)) {
      if (!validateConditions(item)) {
        return false
      }
    } else if (item !== undefined && item !== null) {
      return false
    }
  }

  return conditions.length > 0
}

// sameArrayContents: returns true if both arrays have exactly the same elements
// (including duplicate counts) irrespective of order.
// Non-arrays or arrays of different length return false.
export function sameArrayContents(a, b) {
  if (a === b) return true
  if (!Array.isArray(a) || !Array.isArray(b)) return false
  if (a.length !== b.length) return false
  if (a.length === 0) return true
  const counts = new Map()
  for (const v of a) {
    counts.set(v, (counts.get(v) || 0) + 1)
  }
  for (const v of b) {
    const c = counts.get(v)
    if (!c) return false
    if (c === 1) counts.delete(v)
    else counts.set(v, c - 1)
  }
  return counts.size === 0
}

// orderSensitiveEqual: returns true only if arrays are strictly equal index-wise
export function orderSensitiveEqual(a, b) {
  if (a === b) return true
  if (!Array.isArray(a) || !Array.isArray(b)) return false
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false
  return true
}
