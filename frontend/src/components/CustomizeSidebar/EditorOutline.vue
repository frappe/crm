<!-- The rows of one layer, in the order the sidebar draws them. Drag, or Alt + Up/Down, to move. -->
<template>
  <div v-if="editor.loading" class="flex justify-center py-8">
    <LoadingIndicator class="size-5 text-ink-gray-5" />
  </div>
  <ul
    v-else
    role="listbox"
    :aria-label="__('Sidebar rows')"
    class="flex flex-col gap-0.5"
    @keydown="onKey"
  >
    <li
      v-for="{ row, depth } in list"
      :id="`editor-row-${row.key}`"
      :key="row.key"
      role="option"
      :aria-selected="row.key === editor.selected"
      :tabindex="row.key === active ? 0 : -1"
      draggable="true"
      :class="[
        'group/row relative flex h-7 shrink-0 cursor-pointer items-center rounded-4 px-2 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-outline-gray-3',
        row.key === editor.selected
          ? 'bg-surface-elevation-3 text-ink-gray-8 shadow-sm'
          : 'text-ink-gray-7 hover:bg-surface-gray-2',
        over === row.key && dropsInto(row) ? 'ring-2 ring-outline-gray-5' : '',
        row.type === 'Section' ? 'mt-2' : '',
      ]"
      @click="choose(row.key)"
      @dragstart="onDragStart($event, row.key)"
      @dragend="dragging = over = null"
      @dragover.prevent="over = row.key"
      @dragleave="over = null"
      @drop.prevent="onDrop(row.key)"
    >
      <span
        v-if="over === row.key && !dropsInto(row)"
        class="pointer-events-none absolute inset-x-2 -top-0.5 h-0.5 rounded-full bg-surface-gray-7"
      />
      <span v-if="depth" class="flex h-full w-4 shrink-0 justify-center">
        <span class="h-full border-l border-outline-gray-2" />
      </span>
      <span
        v-if="row.type === 'Section'"
        :class="[
          'lucide-chevron-right size-4 shrink-0',
          row.collapsible && row.keep_closed ? '' : 'rotate-90',
          row.hidden ? 'text-ink-gray-4' : 'text-ink-gray-6',
        ]"
        aria-hidden="true"
      />
      <Icon
        v-else
        :icon="iconOf(row)"
        :class="[
          'size-4 shrink-0',
          row.hidden || row.no_access ? 'text-ink-gray-4' : 'text-ink-gray-6',
        ]"
      />
      <span
        :title="titleOf(row)"
        :class="[
          'ml-2 min-w-0 flex-1 truncate',
          row.hidden ? 'text-ink-gray-5' : '',
          row.type === 'Section' ? 'font-medium text-ink-gray-8' : '',
        ]"
      >
        {{ titleOf(row) }}
      </span>
      <Badge
        v-if="badgeOf(row)"
        :label="badgeOf(row).label"
        :theme="badgeOf(row).theme"
        variant="subtle"
        size="sm"
        class="ml-2 shrink-0"
      />
      <span
        class="lucide-grip-vertical ml-1 size-3.5 shrink-0 cursor-grab text-ink-gray-4 opacity-0 group-hover/row:opacity-100"
        aria-hidden="true"
      />
    </li>
  </ul>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { iconOf, titleOf } from './display'
import { choose, drop, editor, moveBy } from './editor'
import { isCustomSection, isListed, isOwn } from './rows'
import { Badge, LoadingIndicator } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'

const list = computed(() => {
  const listed = editor.rows.filter((row) =>
    isListed(editor.rows, row, editor.showHidden),
  )
  return listed.map((row) => ({ row, depth: row.parent_key ? 1 : 0 }))
})

const active = computed(() =>
  list.value.some(({ row }) => row.key === editor.selected)
    ? editor.selected
    : list.value[0]?.row.key,
)

function badgeOf(row) {
  if (row.no_access) return { label: __('No access'), theme: 'red' }
  if (row.hidden && row.hidden_by === 'site' && editor.scope === 'user') {
    return { label: __('Hidden for everyone'), theme: 'gray' }
  }
  if (row.hidden) return { label: __('Hidden'), theme: 'gray' }
  if (isOwn(row.key, editor.scope)) return { label: __('Added'), theme: 'gray' }
  return null
}

const dragging = ref(null)
const over = ref(null)

function onDragStart(event, key) {
  event.dataTransfer?.setData('text/plain', key)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  dragging.value = key
}

function onDrop(key) {
  if (dragging.value) drop(dragging.value, key)
  dragging.value = over.value = null
}

/** A dragged item lands inside a custom section rather than before it. */
function dropsInto(row) {
  const dragged = editor.rows.find((entry) => entry.key === dragging.value)
  return isCustomSection(row) && dragged && dragged.type !== 'Section'
}

function onKey(event) {
  const by = { ArrowDown: 1, ArrowUp: -1 }[event.key]
  const at = list.value.findIndex(({ row }) => row.key === active.value)
  if (!by || at < 0) return
  event.preventDefault()
  const key = event.altKey
    ? list.value[at].row.key
    : list.value[at + by]?.row.key
  if (!key) return
  if (event.altKey) moveBy(key, by)
  else choose(key)
  nextTick(() => document.getElementById(`editor-row-${key}`)?.focus())
}
</script>
