<template>
  <Dialog
    v-model:open="commandPaletteOpen"
    bare
    size="2xl"
    position="top"
    padding-top="10vh"
  >
    <Combobox
      as="div"
      class="crm-command-palette"
      nullable
      @update:model-value="onSelection"
    >
      <div class="flex items-center border-b border-outline-gray-1 px-1">
        <LucideSearch class="ms-3 size-4 shrink-0 text-ink-gray-4" />
        <button
          v-if="currentStep"
          type="button"
          class="ms-3 flex shrink-0 items-center gap-2 py-1 text-base font-semibold text-ink-gray-7"
          @click="backCommandPalette"
        >
          {{ __(currentStep) }}
          <LucideChevronRight class="size-3 text-ink-gray-4" />
        </button>
        <ComboboxInput
          ref="inputRef"
          :placeholder="__('Search records or type a command...')"
          class="w-full border-none bg-transparent py-3.5 pe-4 ps-3 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
          autofocus
          autocomplete="off"
          spellcheck="false"
          @input="onInput"
          @keydown.backspace="onBackspace"
          @keydown.esc="onEscape"
        />
      </div>

      <ComboboxOptions
        class="crm-command-palette-list max-h-[380px] min-h-[7rem] overflow-y-auto py-2"
        static
        :hold="true"
      >
        <div
          v-if="commandPaletteLoading || !commandPaletteItems.length"
          class="flex flex-col items-center py-12 text-ink-gray-4"
        >
          <component
            :is="emptyIcon"
            class="mb-2.5 size-8 opacity-40"
            :class="{ 'animate-spin': isBusy }"
          />
          <span class="text-base">{{ emptyMessage }}</span>
        </div>
        <template v-else>
          <div v-for="group in commandPaletteGroups" :key="group.title">
            <div
              v-if="group.title"
              class="px-4 pb-1 pt-2 text-xs font-medium text-ink-gray-4"
            >
              {{ __(group.title) }}
            </div>
            <ComboboxOption
              v-for="(item, index) in group.items"
              :key="item.id"
              v-slot="{ active }"
              :value="item"
              class="cursor-pointer scroll-my-10 px-2"
              :class="{ 'scroll-mt-16': index === 0 }"
              :disabled="item.disabled"
            >
              <CommandPaletteRow :command="item" :active="active" />
            </ComboboxOption>
          </div>
        </template>
      </ComboboxOptions>

      <div
        class="flex items-center gap-4 border-t border-outline-gray-1 px-4 py-2.5 text-xs text-ink-gray-4"
      >
        <span
          v-for="(hint, index) in hints"
          :key="index"
          class="flex items-center gap-1.5"
          :class="{ 'ms-auto': hint.trailing }"
        >
          <kbd
            v-for="key in hint.keys"
            :key="key"
            class="rounded-sm bg-surface-gray-2 px-1 py-0.5 font-sans text-ink-gray-5"
          >
            {{ key }}
          </kbd>
          {{ __(hint.label) }}
        </span>
      </div>
    </Combobox>
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
import { computed, nextTick, ref, watch } from 'vue'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideLoaderCircle from '~icons/lucide/loader-circle'
import LucideSearch from '~icons/lucide/search'
import LucideSearchX from '~icons/lucide/search-x'
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
  commandPaletteSearching,
  openCommandPalette,
  restoreCommandPaletteFocus,
  runCommandPaletteItem,
} from '@/composables/useCommandPalette'
import { useCRMCommands } from './useCRMCommands'

useCRMCommands()

const inputRef = ref(null)

const currentStep = computed(() => commandPaletteBreadcrumbs.value.at(-1))

// Never re-key the Combobox: headlessui selects the active option on blur.
watch([commandPaletteOpen, commandPaletteDepth], () =>
  nextTick(() => {
    const input = inputRef.value?.$el
    if (!input) return
    input.value = commandPaletteQuery.value
    input.focus()
  }),
)

const isBusy = computed(
  () => commandPaletteLoading.value || commandPaletteSearching.value,
)

const emptyIcon = computed(() => {
  if (isBusy.value) return LucideLoaderCircle
  return commandPaletteQuery.value ? LucideSearchX : LucideSearch
})

const hints = computed(() => [
  { keys: ['↑', '↓'], label: 'Navigate' },
  { keys: ['↵'], label: 'Select' },
  ...(currentStep.value ? [{ keys: ['⌫'], label: 'Back' }] : []),
  {
    keys: ['esc'],
    label: currentStep.value ? 'Back' : 'Close',
    trailing: true,
  },
])

const emptyMessage = computed(() => {
  if (commandPaletteLoading.value) return __('Loading...')
  if (commandPaletteSearching.value) return __('Searching...')
  return commandPaletteQuery.value
    ? __('No results for "{0}"', [commandPaletteQuery.value])
    : __('Type to search')
})

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
  if (commandPaletteOpen.value) closeCommandPalette()
  else openCommandPalette()
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

<style>
.dialog-content:has(.crm-command-palette) {
  border-radius: 0.55rem;
  transform-origin: center;
}

.dialog-content[data-state='open']:has(.crm-command-palette) {
  animation: palette-open 180ms cubic-bezier(0.2, 1, 0.4, 1);
}

@keyframes palette-open {
  from {
    opacity: 0;
    transform: scale(0.94);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dialog-content[data-state='open']:has(.crm-command-palette) {
    animation: none;
  }
}

@property --palette-fade-top {
  syntax: '<length>';
  inherits: false;
  initial-value: 0px;
}

@property --palette-fade-bottom {
  syntax: '<length>';
  inherits: false;
  initial-value: 0px;
}

/* Scroll-driven edge fade; no fade at either end or when nothing scrolls. */
.crm-command-palette-list {
  mask-image: linear-gradient(
    to bottom,
    transparent,
    #000 var(--palette-fade-top),
    #000 calc(100% - var(--palette-fade-bottom)),
    transparent
  );
  animation:
    palette-fade-top linear both,
    palette-fade-bottom linear both;
  animation-timeline: scroll(self), scroll(self);
  animation-range:
    0 2rem,
    calc(100% - 2rem) 100%;
}

@keyframes palette-fade-top {
  to {
    --palette-fade-top: 2.5rem;
  }
}

@keyframes palette-fade-bottom {
  from {
    --palette-fade-bottom: 2.5rem;
  }
  to {
    --palette-fade-bottom: 0px;
  }
}
</style>
