import Icon from '@/components/Icon.vue'
import { toast } from 'frappe-ui'
import { h, isVNode } from 'vue'

// Saved Form Scripts still use the frappe-ui beta toast API: createToast (the
// old create helper, with durations in seconds) and toast({ title, text }).

export function createToast({
  message,
  title,
  text,
  type,
  icon,
  iconClasses,
  duration,
  timeout,
  closable,
  ...options
}) {
  const data = { ...options, description: text }
  const seconds = duration ?? timeout
  if (icon) data.icon = toastIcon(icon, iconClasses)
  if (seconds != null) data.duration = toMs(seconds)
  if (closable != null) {
    Object.assign(data, { closeButton: closable, dismissible: closable })
  }
  if (closable === false) data.duration = Infinity

  const show = toast[type] ?? toast
  return show(message ?? title ?? '', data)
}

export const scriptToast = Object.assign(
  (message, options) =>
    isLegacyObject(message) ? createToast(message) : toast(message, options),
  toast,
)

function isLegacyObject(message) {
  return (
    typeof message === 'object' &&
    message !== null &&
    ('title' in message || 'text' in message || 'message' in message)
  )
}

function toastIcon(icon, iconClasses) {
  if (typeof icon === 'string') {
    return () => h(Icon, { icon, class: ['size-4', iconClasses] })
  }
  return isVNode(icon) ? () => icon : icon
}

// A duration of 0 used to mean "stay open"; the new toast closes at once on 0.
function toMs(seconds) {
  return seconds === 0 ? Infinity : seconds * 1000
}
