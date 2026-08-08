<template>
  <Dialog v-model:open="commandPaletteOpen" size="xl" bare>
    <Dialog.Title as-child>
      <h2 class="sr-only">{{ __('Command palette') }}</h2>
    </Dialog.Title>

    <div class="flex flex-col" @keydown.capture="onKeydown">
      <div v-if="commandPaletteBreadcrumbs.length" class="px-4 pt-3 text-sm text-ink-gray-5">
        {{ commandPaletteBreadcrumbs.join(' / ') }}
      </div>
      <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4">
        <span class="lucide-search size-4 shrink-0 text-ink-gray-5" />
        <input
          ref="input"
          v-model="commandPaletteQuery"
          role="combobox"
          aria-autocomplete="list"
          aria-controls="command-palette-list"
          :aria-expanded="commandPaletteOpen"
          :aria-activedescendant="activeOptionId"
          :placeholder="__('Search records or type a command...')"
          class="h-12 w-full bg-transparent text-base text-ink-gray-9 outline-none placeholder:text-ink-gray-4"
        />
      </div>

      <div id="command-palette-results" class="sr-only" aria-live="polite">
        {{ __('{0} results', [commandPaletteItems.length]) }}
      </div>
      <ul
        id="command-palette-list"
        role="listbox"
        :aria-busy="commandPaletteLoading"
        class="max-h-80 overflow-y-auto p-2"
      >
        <li v-if="commandPaletteLoading" class="px-3 py-10 text-center">
          <LoadingIndicator class="mx-auto size-5 text-ink-gray-5" />
        </li>
        <li
          v-else-if="!commandPaletteItems.length"
          class="px-3 py-10 text-center text-sm text-ink-gray-5"
        >
          {{ __('No commands found') }}
        </li>
        <template v-for="group in indexedGroups" :key="group.title">
          <li
            v-if="group.title"
            role="presentation"
            class="px-3 pb-1 pt-2 text-xs-medium text-ink-gray-5"
          >
            {{ __(group.title) }}
          </li>
          <CommandPaletteRow
            v-for="item in group.items"
            :key="item.command.id"
            :ref="(element) => setRowRef(element, item.index)"
            :command="item.command"
            :active="item.index === activeIndex"
            :option-id="optionId(item.index)"
            @activate="activeIndex = item.index"
            @select="run(item.command)"
          />
        </template>
      </ul>

      <div class="flex items-center gap-4 border-t border-outline-gray-1 px-4 py-2 text-xs text-ink-gray-5">
        <span>{{ __('↑↓ Navigate') }}</span>
        <span>{{ __('↵ Select') }}</span>
        <span class="ml-auto">{{ __('Esc Back') }}</span>
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import CommandPaletteRow from './CommandPaletteRow.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { Dialog } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { computed, nextTick, ref, watch } from 'vue'
import {
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
} from '@/composables/useCommandPalette'

const input = ref(null)
const rowRefs = ref([])
const activeIndex = ref(0)

const indexedGroups = computed(() => {
  let index = 0
  return commandPaletteGroups.value.map((group) => ({
    ...group,
    items: group.items.map((command) => ({ command, index: index++ })),
  }))
})

const activeOptionId = computed(() => {
  return commandPaletteItems.value.length ? optionId(activeIndex.value) : undefined
})

function optionId(index) {
  return `command-palette-option-${index}`
}

function setRowRef(element, index) {
  if (element) rowRefs.value[index] = element
}

function moveActive(delta) {
  const length = commandPaletteItems.value.length
  if (!length) return
  activeIndex.value = (activeIndex.value + delta + length) % length
}

function run(command) {
  runCommandPaletteItem(command)
}

function handleEscape() {
  if (commandPaletteQuery.value) return (commandPaletteQuery.value = '')
  if (!backCommandPalette()) closeCommandPalette()
}

function onKeydown(event) {
  if (event.ctrlKey && ['n', 'p'].includes(event.key)) {
    event.preventDefault()
    return moveActive(event.key === 'n' ? 1 : -1)
  }
  const handlers = keyHandlers()
  if (!handlers[event.key]) return
  event.preventDefault()
  event.stopPropagation()
  handlers[event.key]()
}

function keyHandlers() {
  return {
    ArrowDown: () => moveActive(1),
    ArrowUp: () => moveActive(-1),
    Home: () => (activeIndex.value = 0),
    End: () => setLastActive(),
    Enter: () => run(commandPaletteItems.value[activeIndex.value]),
    Escape: handleEscape,
    Backspace: () => !commandPaletteQuery.value && backCommandPalette(),
  }
}

function setLastActive() {
  if (commandPaletteItems.value.length) {
    activeIndex.value = commandPaletteItems.value.length - 1
  }
}

function togglePalette() {
  commandPaletteOpen.value ? closeCommandPalette() : openCommandPalette()
}

useKeyboardShortcuts({
  ignoreTyping: false,
  skipWhenDialogOpen: false,
  shortcuts: [
    {
      match: (event) =>
        (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k',
      guard: (event) => !event.target?.closest?.('.ProseMirror'),
      action: togglePalette,
    },
  ],
})

watch([commandPaletteQuery, commandPaletteGroups], () => {
  activeIndex.value = 0
  rowRefs.value = []
})

watch(activeIndex, async (index) => {
  await nextTick()
  rowRefs.value[index]?.$el?.scrollIntoView({ block: 'nearest' })
})

watch(commandPaletteOpen, async (open) => {
  if (!open) return
  await nextTick()
  input.value?.focus()
})
</script>
