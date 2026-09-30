import { Dialog, ErrorMessage } from 'frappe-ui'
import { reactive, ref } from 'vue'

let dialogs = ref([])

export function isDialogOpen() {
  return dialogs.value.some((d) => d.show)
}

export let Dialogs = {
  name: 'Dialogs',
  render() {
    return dialogs.value.map((dialog) => (
      <Dialog
        title={dialog.title}
        size={dialog.size}
        icon={dialog.icon}
        theme={dialog.theme}
        position={dialog.position}
        actions={dialog.actions}
        open={dialog.show}
        onUpdate:open={(val) => (dialog.show = val)}
      >
        {{
          default: () => {
            return [
              dialog.message && (
                <p class="text-p-base text-ink-gray-7">{dialog.message}</p>
              ),
              dialog.html && <div v-html={dialog.html} />,
              <ErrorMessage class="mt-2" message={dialog.error} />,
            ]
          },
        }}
      </Dialog>
    ))
  },
}

export function createDialog(dialogOptions) {
  let dialog = reactive(dialogOptions)
  dialog.actions = withLegacyCloseContext(dialog.actions)
  Object.assign(dialog, withLegacyIcon(dialog))
  dialog.key = 'dialog-' + dialogs.value.length
  dialog.show = false
  setTimeout(() => {
    dialog.show = true
  }, 0)
  dialogs.value.push(dialog)
  return dialog
}

const APPEARANCE_THEMES = {
  warning: 'amber',
  info: 'blue',
  danger: 'red',
  success: 'green',
}

// Saved Form Scripts may still use `onClick(close)`; frappe-ui now passes `{ close }`.
function withLegacyCloseContext(actions) {
  return actions?.map((action) => {
    if (!action.onClick) return action
    return {
      ...action,
      onClick: ({ close }) => {
        const context = () => close()
        context.close = close
        return action.onClick(context)
      },
    }
  })
}

// Saved Form Scripts may still pass the old icon object ({ name, appearance }) or a feather name.
function withLegacyIcon({ icon, theme }) {
  const legacy = isLegacyIconObject(icon) ? icon : {}
  const tone = theme ?? legacy.theme ?? APPEARANCE_THEMES[legacy.appearance]
  return {
    icon: toLucideName(legacy.name ?? icon),
    theme: tone === 'yellow' ? 'amber' : tone,
  }
}

// Icon components such as `~icons/lucide/*` also carry a `name`.
function isLegacyIconObject(icon) {
  return typeof icon?.name === 'string' && !icon.render && !icon.setup
}

function toLucideName(icon) {
  if (typeof icon !== 'string' || icon.startsWith('lucide-')) return icon
  return `lucide-${icon}`
}
