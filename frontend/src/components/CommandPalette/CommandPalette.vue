<template>
  <Dialog
    v-model="commandPaletteOpen"
    :options="{ size: 'xl', position: 'top' }"
  >
    <template #body>
      <div>
        <Combobox
          :key="commandPaletteDepth"
          nullable
          @update:model-value="onSelection"
        >
          <div class="relative">
            <div class="pl-4.5 absolute inset-y-0 left-0 flex items-center">
              <LucideSearch class="h-4 w-4" />
            </div>
            <ComboboxInput
              :placeholder="__('Search records or type a command...')"
              class="pl-11.5 pr-4.5 w-full border-none bg-transparent py-3 text-base text-gray-800 placeholder:text-gray-500 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
              autocomplete="off"
              @input="onInput"
              @keydown.backspace="onBackspace"
              @keydown.esc="onEscape"
            />
          </div>
          <ComboboxOptions
            class="max-h-96 overflow-auto border-t border-gray-100"
            static
            :hold="true"
          >
            <div
              v-if="commandPaletteBreadcrumbs.length"
              class="px-4.5 mb-2.5 mt-3 text-base text-gray-600"
            >
              {{ commandPaletteBreadcrumbs.join(' / ') }}
            </div>
            <div v-if="commandPaletteLoading" class="px-4.5 py-10">
              <LoadingIndicator class="mx-auto size-5 text-gray-500" />
            </div>
            <div
              v-else-if="!commandPaletteItems.length"
              class="px-4.5 py-10 text-center text-base text-gray-600"
            >
              {{ __('No commands found') }}
            </div>
            <template v-else>
              <div
                v-for="group in commandPaletteGroups"
                :key="group.title"
                class="mt-4.5 mb-2 first:mt-3"
              >
                <div
                  v-if="group.title"
                  class="px-4.5 mb-2.5 text-base text-gray-600"
                >
                  {{ __(group.title) }}
                </div>
                <ComboboxOption
                  v-for="item in group.items"
                  :key="item.id"
                  v-slot="{ active }"
                  :value="item"
                  class="px-2.5"
                  :disabled="item.disabled"
                >
                  <CommandPaletteRow :command="item" :active="active" />
                </ComboboxOption>
              </div>
            </template>
          </ComboboxOptions>
        </Combobox>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/vue'
import { Dialog } from 'frappe-ui'
import { watch } from 'vue'
import LucideSearch from '~icons/lucide/search'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import CommandPaletteRow from './CommandPaletteRow.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import {
  backCommandPalette,
  closeCommandPalette,
  commandPaletteBreadcrumbs,
  commandPaletteDepth,
  commandPaletteGroups,
  commandPaletteItems,
  commandPaletteLoading,
  commandPaletteOpen,
  commandPaletteQuery,
  openCommandPalette,
  restoreCommandPaletteFocus,
  runCommandPaletteItem,
} from '@/composables/useCommandPalette'
import { useCRMCommands } from './useCRMCommands'

useCRMCommands()

function onInput(event) {
  commandPaletteQuery.value = event.target.value
}

function onSelection(command) {
  if (command) runCommandPaletteItem(command)
}

function onBackspace(event) {
  if (event.currentTarget.value || !commandPaletteDepth.value) return
  event.preventDefault()
  backCommandPalette()
}

function onEscape(event) {
  if (!commandPaletteDepth.value) return
  event.preventDefault()
  event.stopPropagation()
  backCommandPalette()
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

watch(commandPaletteOpen, (open) => {
  if (!open) restoreCommandPaletteFocus()
})
</script>
