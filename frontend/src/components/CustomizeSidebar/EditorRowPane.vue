<!-- The selected row: what it opens, its label and icon, where it sits, and Hide or Delete. -->
<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 pt-5">
    <template v-if="row">
      <EditorPaneHeading
        :icon="isSection ? 'folder-open' : iconOf(row)"
        :title="titleOf(row)"
        :origin="originOf(row)"
      />
      <p v-if="!own" class="-mt-3 mb-5 text-p-sm text-ink-gray-5">
        {{ inheritedNote }}
      </p>

      <div class="flex flex-col gap-3">
        <Alert
          v-if="row.no_access"
          theme="amber"
          :title="__('You cannot read {0}', [row.link_to])"
          :description="
            __(
              'It does not show in your sidebar. People who can read it still see it.',
            )
          "
        />
        <DoctypePicker
          v-if="own && row.link_type === 'DocType'"
          :model-value="row.link_to"
          :label="__('Opens')"
          :error="editor.opensRefusal"
          @update:model-value="changeDoctype"
        />
        <FormControl
          v-else-if="!isSection"
          :model-value="opens"
          :label="__('Opens')"
          :description="
            __('To open something else, hide this row and add another.')
          "
          disabled
        />
        <FormControl
          type="text"
          :model-value="row.label"
          :label="__('Label')"
          :placeholder="belowRow?.label || row.link_to"
          :description="defaultNote"
          @update:model-value="(label) => update({ label })"
        />
        <div v-if="!isSection" class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-6">{{ __('Icon') }}</span>
          <IconPicker
            :model-value="row.icon || null"
            :max-icons="1000"
            :placeholder="__('Default icon')"
            @update:model-value="(icon) => update({ icon: icon || '' })"
          />
        </div>
        <Select
          v-if="!isSection"
          :model-value="row.parent_key || MAIN_LIST"
          :options="parents"
          :label="__('Place under')"
          @update:model-value="
            (value) => nest(value === MAIN_LIST ? null : value)
          "
        />
        <template v-if="isSection">
          <Checkbox
            v-if="!fillsItself(row)"
            :model-value="Boolean(row.collapsible)"
            :label="__('Can collapse')"
            @update:model-value="
              (value) => update({ collapsible: value ? 1 : 0 })
            "
          />
          <Checkbox
            :model-value="Boolean(row.keep_closed)"
            :disabled="!row.collapsible"
            :label="__('Starts closed')"
            @update:model-value="
              (value) => update({ keep_closed: value ? 1 : 0 })
            "
          />
        </template>
        <p v-if="editor.refusal" class="text-p-sm text-ink-red-5" role="alert">
          {{ editor.refusal }}
        </p>
      </div>

      <div
        class="mt-auto flex h-[49px] shrink-0 items-center gap-2 border-t border-outline-gray-1"
      >
        <Button
          v-if="!own"
          class="-ml-2"
          variant="ghost"
          :icon-left="row.hidden ? 'lucide-eye' : 'lucide-eye-off'"
          :label="row.hidden ? __('Show') : __('Hide')"
          @click="toggleHidden"
        />
        <template v-else>
          <span v-if="isSection && childCount" class="text-sm text-ink-gray-5">
            {{
              childCount === 1
                ? __('Deleting it moves its row to the main list.')
                : __('Deleting it moves its {0} rows to the main list.', [
                    childCount,
                  ])
            }}
          </span>
          <Button
            class="-mr-2 ml-auto"
            variant="ghost"
            theme="red"
            icon-left="lucide-trash-2"
            :label="__('Delete')"
            @click="remove"
          />
        </template>
      </div>
    </template>
    <p v-else class="m-auto text-sm text-ink-gray-5">
      {{ __('Pick a row to change it.') }}
    </p>
  </div>
</template>

<script setup>
import DoctypePicker from './DoctypePicker.vue'
import EditorPaneHeading from './EditorPaneHeading.vue'
import { fillsItself, iconOf, originOf, titleOf } from './display'
import {
  changeDoctype,
  current,
  editor,
  nest,
  remove,
  toggleHidden,
  update,
} from './editor'
import { find, isCustomSection, isOwn } from './rows'
import { Alert, Checkbox, FormControl, Select } from 'frappe-ui'
import { IconPicker } from 'frappe-ui/experimental'
import { computed } from 'vue'

const MAIN_LIST = 'main-list'

const row = computed(() => current.value)
const own = computed(() => isOwn(row.value.key, editor.scope))
const isSection = computed(() => row.value.type === 'Section')
const belowRow = computed(() => find(editor.below, row.value.key))

const inheritedNote = computed(() => {
  if (fillsItself(row.value)) {
    return __(
      'It fills itself from saved views. You can rename it, hide it, move it or keep it closed. Nothing can be added to it.',
    )
  }
  if (isSection.value) return __('You can rename it, hide it or move it.')
  return __('You can rename it, change its icon, hide it or move it.')
})

const opens = computed(() =>
  row.value.link_type === 'DocType'
    ? __('DocType · {0}', [row.value.link_to])
    : __('Page · {0}', [__(row.value.link_to)]),
)

const defaultNote = computed(() => {
  const base = belowRow.value?.label
  if (own.value || !base || base === row.value.label) return undefined
  return __('Default: {0}', [__(base)])
})

const parents = computed(() => [
  { label: __('Main list'), value: MAIN_LIST },
  ...editor.rows
    .filter(isCustomSection)
    .map((section) => ({ label: titleOf(section), value: section.key })),
])

const childCount = computed(
  () =>
    editor.rows.filter((entry) => entry.parent_key === row.value.key).length,
)
</script>
