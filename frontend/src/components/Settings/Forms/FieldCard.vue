<template>
  <div
    class="rounded border bg-surface-elevation-2 text-ink-gray-8"
    :class="expanded ? 'border-outline-gray-3' : 'border-outline-gray-2'"
  >
    <!-- compact header: grip · type icon · label (inline editable) · required · expand · delete -->
    <div class="flex items-center gap-2 px-2.5 py-2">
      <DragVerticalIcon
        class="drag-handle h-3.5 shrink-0 cursor-grab text-ink-gray-4"
      />
      <component
        :is="typeIcon"
        class="h-4 w-4 shrink-0 text-ink-gray-5"
        :title="typeLabel"
      />
      <input
        v-if="editingLabel"
        ref="labelInput"
        v-model="field.label"
        :placeholder="field.fieldname"
        class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
        @blur="editingLabel = false"
        @keydown.enter="editingLabel = false"
        @input="$emit('dirty')"
      />
      <div
        v-else
        class="flex min-w-0 flex-1 cursor-text items-center gap-0.5"
        @click="beginEdit"
      >
        <span
          class="truncate text-base"
          :class="field.label ? 'text-ink-gray-8' : 'text-ink-gray-4'"
        >
          {{ field.label || field.fieldname }}
        </span>
        <span v-if="field.reqd" class="shrink-0 text-ink-red-5">*</span>
        <LucideLock
          v-if="locked"
          class="h-3 w-3 shrink-0 text-ink-gray-4"
          :title="__('Required by the record')"
        />
      </div>
      <Button
        variant="ghost"
        :tooltip="expanded ? __('Collapse') : __('Edit field')"
        @click="$emit('toggle')"
      >
        <template #icon>
          <LucideChevronDown
            class="h-4 w-4 text-ink-gray-5 transition-transform"
            :class="expanded ? 'rotate-180' : ''"
          />
        </template>
      </Button>
      <Button variant="ghost" :tooltip="__('Remove')" @click="$emit('remove')">
        <template #icon><LucideX class="h-4 w-4 text-ink-gray-5" /></template>
      </Button>
    </div>

    <!-- inline editor (revealed when selected) -->
    <div
      v-if="expanded"
      class="space-y-3 border-t border-outline-gray-2 px-2.5 py-2.5"
    >
      <div class="flex items-center justify-between">
        <span class="text-base text-ink-gray-5">{{ __('Required') }}</span>
        <Tooltip
          v-if="locked"
          :text="
            __(
              &quot;This field is required by the record and can't be made optional. Remove it to move it to hidden fields.&quot;,
            )
          "
        >
          <!-- shown on + non-interactive (disabled would grey it out, reading as off) -->
          <div class="inline-flex cursor-not-allowed">
            <Switch :modelValue="true" size="sm" class="pointer-events-none" />
          </div>
        </Tooltip>
        <Switch
          v-else
          v-model="field.reqd"
          size="sm"
          @update:modelValue="$emit('dirty')"
        />
      </div>
      <FormControl
        v-model="field.placeholder"
        type="text"
        size="sm"
        :label="__('Placeholder')"
        :placeholder="__('Optional')"
        @input="$emit('dirty')"
      />
      <FormControl
        v-model="field.field_description"
        type="text"
        size="sm"
        :label="__('Description')"
        :placeholder="__('Helper text under the field (optional)')"
        @input="$emit('dirty')"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { Switch, Button, FormControl, Tooltip } from 'frappe-ui'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import LucideX from '~icons/lucide/x'
import LucideLock from '~icons/lucide/lock'
import LucideChevronDown from '~icons/lucide/chevron-down'
import { fieldTypeIcon, fieldTypeLabel } from './fieldTypeIcon'

const props = defineProps({
  field: { type: Object, required: true },
  expanded: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'toggle', 'remove', 'dirty'])

const editingLabel = ref(false)
const labelInput = ref(null)

async function beginEdit() {
  editingLabel.value = true
  emit('open')
  await nextTick()
  labelInput.value?.focus()
}

// map the field's type to a lucide icon shown next to the label
const typeIcon = computed(() => fieldTypeIcon(props.field))
const typeLabel = computed(() => fieldTypeLabel(props.field))
</script>
