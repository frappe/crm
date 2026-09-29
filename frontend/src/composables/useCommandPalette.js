import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { checkedFirst, groupCommands } from '@/utils/commandPalette'
import { toast } from 'frappe-ui'

export const commandPaletteOpen = ref(false)
export const commandPaletteQuery = ref('')

const commandProvider = shallowRef(() => [])
const contextualProvider = shallowRef(() => [])
const stack = shallowRef([])
export const commandPaletteLoading = ref(false)
export const commandPaletteSearching = ref(false)
let previousFocus = null

export const commandPaletteDepth = computed(() => stack.value.length)
export const commandPaletteBreadcrumbs = computed(() =>
  stack.value.map((level) => level.title),
)

const currentCommands = computed(() => {
  return stack.value.at(-1)?.commands || commandProvider.value()
})

export const commandPaletteGroups = computed(() => {
  return groupCommands(currentCommands.value, commandPaletteQuery.value)
})

export const commandPaletteItems = computed(() => {
  return commandPaletteGroups.value.flatMap((group) => group.items)
})

export function setCommandPaletteProvider(provider) {
  commandProvider.value = provider
}

export function setCommandPaletteContext(provider) {
  contextualProvider.value = provider || (() => [])
}

export function getCommandPaletteContext() {
  // A half-loaded page must not take the whole palette down with it.
  try {
    return contextualProvider.value() || []
  } catch (error) {
    console.error('Command palette context failed', error)
    return []
  }
}

export function useCommandPaletteContext(provider) {
  setCommandPaletteContext(provider)
  onBeforeUnmount(() => {
    if (contextualProvider.value === provider) setCommandPaletteContext()
  })
}

export function openCommandPalette() {
  previousFocus = document.activeElement
  stack.value = []
  commandPaletteQuery.value = ''
  commandPaletteOpen.value = true
}

export function closeCommandPalette() {
  commandPaletteOpen.value = false
}

export function restoreCommandPaletteFocus() {
  requestAnimationFrame(() => {
    if (document.activeElement === document.body) previousFocus?.focus?.()
    previousFocus = null
  })
}

export function backCommandPalette() {
  if (!stack.value.length) return false
  stack.value = stack.value.slice(0, -1)
  commandPaletteQuery.value = ''
  return true
}

export async function runCommandPaletteItem(command) {
  if (!command || command.disabled || commandPaletteLoading.value) return
  // Closing blurs the input, and headlessui re-emits the active option on blur.
  if (!commandPaletteOpen.value) return
  if (command.children) return openChildren(command)
  closeCommandPalette()
  try {
    await command.perform?.()
  } catch (error) {
    showCommandError(error)
  }
}

async function openChildren(command) {
  commandPaletteLoading.value = true
  try {
    const commands = checkedFirst(await command.children())
    stack.value = [...stack.value, { title: command.title, commands }]
    commandPaletteQuery.value = ''
  } catch (error) {
    showCommandError(error)
  } finally {
    commandPaletteLoading.value = false
  }
}

function showCommandError(error) {
  console.error('Command palette action failed', error)
  toast.error(error?.messages?.[0] || __('Unable to run command'))
}

export function useCommandPalette() {
  return {
    backCommandPalette,
    closeCommandPalette,
    commandPaletteBreadcrumbs,
    commandPaletteGroups,
    commandPaletteItems,
    commandPaletteLoading,
    commandPaletteOpen,
    commandPaletteQuery,
    openCommandPalette,
    runCommandPaletteItem,
  }
}
