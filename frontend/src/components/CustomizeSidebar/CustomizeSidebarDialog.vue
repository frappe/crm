<!-- Customize sidebar: the outline of one layer on the left, the selected row on the right. -->
<template>
  <Dialog v-model:open="open" bare size="4xl" :dismissible="!changed">
    <div class="flex h-[660px] flex-col">
      <header
        class="flex items-center justify-between gap-4 border-b border-outline-gray-1 px-6 pb-4 pt-5"
      >
        <div class="min-w-0">
          <h2 class="text-xl-semibold text-ink-gray-9">
            {{ __('Customize sidebar') }}
          </h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ levelNote }}</p>
        </div>
        <Tooltip
          v-if="editor.canEditSite"
          :text="__('Save or discard your changes first.')"
          :disabled="!changed"
        >
          <div class="shrink-0">
            <TabButtons
              :model-value="editor.scope"
              :options="levels"
              @update:model-value="switchTo"
            />
          </div>
        </Tooltip>
      </header>

      <div class="grid min-h-0 flex-1 grid-cols-[300px_1fr]">
        <div class="flex min-h-0 flex-col border-r border-outline-gray-1">
          <div
            class="flex h-12 shrink-0 items-center justify-between gap-2 pl-6 pr-4 pt-2"
          >
            <span class="flex items-baseline gap-1.5">
              <span class="text-base-medium text-ink-gray-8">
                {{ __('Items') }}
              </span>
              <span class="text-sm tabular-nums text-ink-gray-5">
                {{ itemCount }}
              </span>
            </span>
            <Dropdown :options="addOptions" align="end" side="bottom">
              <Button
                variant="subtle"
                size="sm"
                icon-left="lucide-plus"
                icon-right="lucide-chevron-down"
                :label="__('Add')"
              />
            </Dropdown>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto px-4 pb-2 pt-1">
            <EditorOutline />
          </div>
          <div
            class="flex items-center justify-between gap-3 border-t border-outline-gray-1 px-6 py-3"
          >
            <Checkbox
              v-model="editor.showHidden"
              class="shrink-0 whitespace-nowrap"
              :label="__('Show hidden')"
            />
            <span
              class="truncate text-xs text-ink-gray-5"
              :title="__('Drag a row, or press Alt + ↑ ↓, to move it')"
            >
              {{ __('Drag or Alt + ↑ ↓') }}
            </span>
          </div>
        </div>
        <EditorRowForm
          v-if="editor.adding"
          :key="editor.adding.id"
          :type="editor.adding.type"
        />
        <EditorRowPane v-else />
      </div>

      <div
        v-if="editor.error"
        class="flex items-center gap-2 border-t border-outline-gray-1 bg-surface-red-1 px-6 py-2"
      >
        <span
          class="lucide-circle-alert size-4 shrink-0 text-ink-red-5"
          aria-hidden="true"
        />
        <p class="flex-1 text-p-sm text-ink-red-6">{{ editor.error }}</p>
        <Button
          v-if="editor.stale"
          variant="subtle"
          :label="__('Reload')"
          @click="reload"
        />
      </div>
      <div
        v-else-if="editor.resetNote"
        class="flex items-center gap-2 border-t border-outline-gray-1 px-6 py-2"
      >
        <span
          class="lucide-rotate-ccw size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
        <p class="flex-1 text-p-sm text-ink-gray-6">
          {{
            editor.scope === 'site'
              ? __(
                  "Back to the default sidebar. Save to drop this layer's changes.",
                )
              : __(
                  "Back to the sidebar everyone sees. Save to drop this layer's changes.",
                )
          }}
        </p>
      </div>

      <footer
        class="flex items-center gap-2 border-t border-outline-gray-1 px-6 py-4"
      >
        <Button
          v-if="changed"
          class="-ml-2"
          variant="ghost"
          :label="__('Discard changes')"
          @click="discard"
        />
        <Button
          v-else-if="editor.modified"
          class="-ml-2"
          variant="ghost"
          :label="__('Reset to default')"
          @click="resetToDefault"
        />
        <Button
          class="ml-auto"
          variant="subtle"
          :label="__('Cancel')"
          @click="cancel"
        />
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="!changed"
          :loading="editor.saving"
          @click="save"
        />
      </footer>
    </div>
  </Dialog>
</template>

<script setup>
import EditorOutline from './EditorOutline.vue'
import EditorRowForm from './EditorRowForm.vue'
import EditorRowPane from './EditorRowPane.vue'
import {
  cancel,
  changed,
  discard,
  editor,
  reload,
  resetToDefault,
  save,
  startAdding,
  switchTo,
} from './editor'
import { isListed } from './rows'
import { doctypeItemsOpen } from '@/utils/navigation'
import {
  Badge,
  Checkbox,
  Dialog,
  Dropdown,
  TabButtons,
  Tooltip,
} from 'frappe-ui'
import { computed, h } from 'vue'

const open = computed({
  get: () => editor.open,
  set: (value) => (value ? (editor.open = true) : cancel()),
})

const levels = computed(() => [
  { label: __('Just me'), value: 'user', disabled: changed.value },
  { label: __('Everyone'), value: 'site', disabled: changed.value },
])

const levelNote = computed(() => {
  if (editor.scope === 'site')
    return __('Changes apply to everyone on this site')
  if (!editor.modified && !changed.value) {
    return __('You have no changes of your own yet')
  }
  return __('Changes apply to you only')
})

const itemCount = computed(
  () =>
    editor.rows.filter(
      (row) =>
        row.type !== 'Section' && isListed(editor.rows, row, editor.showHidden),
    ).length,
)

const comingSoon = () =>
  h(Badge, {
    label: __('Coming soon'),
    theme: 'gray',
    variant: 'subtle',
    size: 'sm',
  })

const addOptions = computed(() => [
  {
    label: __('DocType'),
    icon: 'lucide-table',
    disabled: !doctypeItemsOpen,
    slots: doctypeItemsOpen ? undefined : { suffix: comingSoon },
    onClick: () => startAdding('DocType'),
  },
  {
    label: __('Section'),
    icon: 'lucide-folder-open',
    onClick: () => startAdding('Section'),
  },
])
</script>
