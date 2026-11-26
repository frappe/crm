<!-- Settings › App menu: order, hide and add the items of the menu under the app logo. -->
<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex items-start justify-between gap-6">
      <div class="flex flex-col gap-1">
        <div class="flex h-5 items-center gap-2">
          <h2 class="text-2xl-semibold leading-none">{{ __('App menu') }}</h2>
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="amber"
          />
        </div>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Choose what shows in the menu under the CRM logo. Drag rows to reorder.',
            )
          }}
        </p>
      </div>
      <div v-if="isDirty" class="flex shrink-0 gap-2">
        <Button :label="__('Discard')" @click="discard" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="settings.setValue.loading"
          @click="save"
        />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 gap-10">
      <div class="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
        <Draggable
          v-model="tree"
          tag="ul"
          item-key="name"
          handle=".drag-handle"
          v-bind="dragOptions"
          :group="{ name: 'app-menu', put: acceptsAtTop }"
          :aria-label="__('Menu items')"
          class="min-h-0 select-none overflow-y-auto rounded-6 border border-outline-gray-2 p-1"
          :data-dragging="dragging || undefined"
          @start="dragging = true"
          @end="dragging = false"
        >
          <template #item="{ element }">
            <li :data-link="isLink(element)">
              <AppMenuRow
                :item="element"
                :links="element.children"
                @toggle-hidden="toggleHidden(element)"
                @edit="editRow(element)"
                @remove="removeRow(element)"
              />
              <div v-if="element.children" class="relative">
                <Draggable
                  v-model="element.children"
                  tag="ul"
                  item-key="name"
                  handle=".drag-handle"
                  v-bind="dragOptions"
                  :group="{ name: 'app-menu', put: acceptsLink }"
                  data-links
                  :aria-label="__('Links in {0}', [__(element.label)])"
                  :class="{ 'min-h-10': dragging && !element.children.length }"
                  @start="dragging = true"
                  @end="dragging = false"
                >
                  <template #item="{ element: link }">
                    <li
                      :data-link="isLink(link)"
                      :data-built-in="Boolean(link.is_standard)"
                    >
                      <AppMenuRow
                        :item="link"
                        @toggle-hidden="toggleHidden(link)"
                        @edit="editRow(link)"
                      />
                    </li>
                  </template>
                </Draggable>
                <div
                  v-if="dragging && !element.children.length"
                  class="app-menu-drop-hint pointer-events-none absolute inset-y-1 left-16 right-20 flex items-center rounded-4 border border-dashed border-outline-gray-3 px-2.5 text-sm text-ink-gray-5"
                >
                  {{ __('Drop a link here') }}
                </div>
              </div>
            </li>
          </template>
        </Draggable>
        <div class="flex shrink-0 gap-2">
          <Button
            :label="__('Add link')"
            icon-left="lucide-plus"
            @click="addItem('Route')"
          />
          <Button
            variant="ghost"
            :label="__('Add submenu')"
            @click="addItem('Submenu')"
          />
          <Button
            variant="ghost"
            :label="__('Add divider')"
            @click="addDivider"
          />
        </div>
        <ErrorMessage :message="error" />
      </div>
      <AppMenuPreview :items="rows" />
    </div>

    <AppMenuItemDialog
      v-model:open="showDialog"
      :item="editingRow"
      :type="newType"
      :parent-submenu="editingRow ? parentOf(editingRow) : ''"
      :submenus="submenus"
      :link-count="editingRow?.children?.length || 0"
      @save="saveItem"
      @delete="removeRow(editingRow)"
    />
  </div>
</template>

<script setup>
import AppMenuRow from '@/components/Settings/AppMenu/AppMenuRow.vue'
import AppMenuPreview from '@/components/Settings/AppMenu/AppMenuPreview.vue'
import AppMenuItemDialog from '@/components/Settings/AppMenu/AppMenuItemDialog.vue'
import { holdsLinks } from '@/composables/appMenu'
import { getSettings } from '@/stores/settings'
import { getRandom } from '@/utils'
import Draggable from 'vuedraggable'
import { Badge, ErrorMessage } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { _settings: settings, settings: liveSettings } = getSettings()

// The unsaved menu as top-level rows; a row that holds links keeps them in `children`.
const tree = ref([])
const dragging = ref(false)
const error = ref('')
const showDialog = ref(false)
const editingRow = ref(null)
const newType = ref('Route')

// The row's own slot shows where it will land, indented inside a submenu.
const dragOptions = { ghostClass: 'app-menu-drop-slot' }

const savedRows = computed(() => settings.doc?.dropdown_items || [])

watch(savedRows, discard, { immediate: true })

/** The rows to save: each submenu's links follow it, and know its key. */
const rows = computed(() => flatten(tree.value))

const isDirty = computed(
  () =>
    fingerprint(rows.value) !== fingerprint(flatten(toTree(savedRows.value))),
)

const submenus = computed(() =>
  tree.value
    .filter(holdsLinks)
    .map((row) => ({ label: __(row.label), value: row.name1 })),
)

/** A copy of the saved rows as a tree. A link whose submenu is gone goes to the top level. */
function toTree(items) {
  const copy = JSON.parse(JSON.stringify(items))
  const keys = new Set(copy.filter(holdsLinks).map((row) => row.name1))
  const top = copy.filter((row) => !keys.has(row.parent_submenu))
  for (const row of top.filter(holdsLinks)) {
    row.children = copy.filter((link) => link.parent_submenu === row.name1)
  }
  return top
}

function flatten(top) {
  return top
    .flatMap(({ children, ...row }) => [
      { ...row, parent_submenu: '' },
      ...(children || []).map((link) => ({
        ...link,
        parent_submenu: row.name1,
      })),
    ])
    .map((row, index) => ({ ...row, idx: index + 1 }))
}

function fingerprint(items) {
  return JSON.stringify(
    items.map((row) => [
      row.name,
      row.type,
      row.label,
      row.icon,
      row.route,
      row.parent_submenu,
      Boolean(row.hidden),
      Boolean(row.open_in_new_window),
    ]),
  )
}

function discard() {
  tree.value = toTree(savedRows.value)
  error.value = ''
}

function isLink(row) {
  return row.type === 'Route' && !row.is_standard
}

// Only custom links can be dropped inside a submenu.
function acceptsLink(to, from, dragged) {
  return dragged.dataset.link === 'true'
}

// Built-ins inside Help, such as About, stay in Help.
function acceptsAtTop(to, from, dragged) {
  return dragged.dataset.builtIn !== 'true'
}

function listOf(row) {
  if (tree.value.includes(row)) return tree.value
  return tree.value.find((top) => top.children?.includes(row))?.children
}

function parentOf(row) {
  return tree.value.find((top) => top.children?.includes(row))?.name1 || ''
}

function newRow(values) {
  return {
    name: getRandom(10),
    __islocal: true,
    doctype: 'CRM Dropdown Item',
    parenttype: 'FCRM Settings',
    parentfield: 'dropdown_items',
    is_standard: 0,
    hidden: 0,
    ...values,
  }
}

function addDivider() {
  tree.value.push(newRow({ type: 'Separator', label: '' }))
}

function addItem(type) {
  editingRow.value = null
  newType.value = type
  showDialog.value = true
}

function editRow(row) {
  editingRow.value = row
  showDialog.value = true
}

function toggleHidden(row) {
  row.hidden = row.hidden ? 0 : 1
}

function saveItem({ parent_submenu: target = '', ...values }) {
  const row = editingRow.value
  if (row) {
    Object.assign(row, values)
    if (row.type === 'Route') moveLink(row, target)
  } else if (newType.value === 'Submenu') {
    const name1 = `submenu-${getRandom(10).toLowerCase()}`
    tree.value.push(newRow({ ...values, type: 'Submenu', name1, children: [] }))
  } else {
    moveLink(newRow({ ...values, type: 'Route' }), target)
  }
}

/** Puts the link at the end of the submenu `target`, or of the top level; it stays put if already there. */
function moveLink(row, target) {
  const from = listOf(row)
  const to = target
    ? tree.value.find((top) => top.name1 === target).children
    : tree.value
  if (from === to) return
  from?.splice(from.indexOf(row), 1)
  to.push(row)
}

// A deleted submenu leaves its links where it was.
function removeRow(row) {
  const list = listOf(row)
  list.splice(list.indexOf(row), 1, ...(row.children || []))
}

function save() {
  error.value = ''
  settings.setValue.submit(
    { dropdown_items: rows.value },
    {
      onSuccess: () => (liveSettings.value = settings.doc),
      onError: (err) => (error.value = err.messages?.join('\n') || err.message),
    },
  )
}
</script>

<style>
.app-menu-drop-slot > div:first-child {
  background: var(--surface-blue-1);
  box-shadow: inset 0 0 0 1px var(--outline-blue-2);
}
.app-menu-drop-slot > div:first-child > * {
  opacity: 0.5;
}
/* The hint gives way once the dragged row's slot is in the empty submenu. */
[data-links]:has(> .app-menu-drop-slot) + .app-menu-drop-hint {
  display: none;
}
/* The submenu a dragged row will land in. */
li:has(> div > [data-links] > .app-menu-drop-slot) {
  border-radius: 8px;
  background: var(--surface-gray-1);
}
</style>
