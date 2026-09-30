<template>
  <div
    class="rounded-4 border bg-surface-elevation-2 text-ink-gray-8"
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
        v-model="labelModel"
        :placeholder="field.fieldname"
        class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
        @blur="editingLabel = false"
        @keydown.enter="editingLabel = false"
      />
      <div
        v-else
        class="group/label flex min-w-0 flex-1 cursor-text items-center"
        :title="__('Click to rename')"
        @click="beginEdit"
      >
        <span
          class="-ml-1 inline-flex min-w-0 max-w-full items-center gap-1 rounded-4 px-1 py-0.5 transition-colors group-hover/label:bg-surface-gray-3"
        >
          <span
            class="min-w-0 truncate text-base"
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
          <LucidePencil
            class="h-3 w-3 shrink-0 text-ink-gray-4 opacity-0 transition-opacity group-hover/label:opacity-100"
          />
        </span>
      </div>
      <Tooltip
        v-if="guestSelectMissing"
        :text="
          __('Guests can\'t see {0} records yet. Open to grant access.', [
            field.options,
          ])
        "
      >
        <LucideTriangleAlert class="h-3.5 w-3.5 shrink-0 text-ink-amber-6" />
      </Tooltip>
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
              'This field is required by the record and can\'t be made optional. Remove it to move it to hidden fields.',
            )
          "
        >
          <!-- shown on + non-interactive (disabled would grey it out, reading as off) -->
          <div class="inline-flex cursor-not-allowed">
            <Switch :modelValue="true" size="sm" class="pointer-events-none" />
          </div>
        </Tooltip>
        <Switch v-else v-model="reqdModel" size="sm" />
      </div>
      <FormControl
        v-model="placeholderModel"
        type="text"
        size="sm"
        :label="__('Placeholder')"
        :placeholder="__('Optional')"
      />
      <FormControl
        v-model="descriptionModel"
        type="text"
        size="sm"
        :label="__('Description')"
        :placeholder="__('Helper text under the field (optional)')"
      />
      <!-- conditional logic: show / require / lock this field based on other answers -->
      <div class="space-y-3 border-t border-outline-gray-2 pt-3">
        <div class="flex items-center gap-1.5">
          <span class="text-base text-ink-gray-5">{{
            __('Conditional logic')
          }}</span>
          <Tooltip
            :text="
              __(
                'Frappe expression referencing other fields as doc.<fieldname>, e.g. eval:doc.country == \'India\'. Leave blank for no condition.',
              )
            "
          >
            <LucideInfo class="h-3.5 w-3.5 text-ink-gray-4" />
          </Tooltip>
        </div>
        <FormControl
          v-model="dependsOnModel"
          type="text"
          size="sm"
          :label="__('Visible if')"
          :placeholder="rulePlaceholder"
        />
        <FormControl
          v-model="mandatoryDependsOnModel"
          type="text"
          size="sm"
          :label="__('Mandatory if')"
          :placeholder="rulePlaceholder"
        />
        <FormControl
          v-model="readOnlyDependsOnModel"
          type="text"
          size="sm"
          :label="__('Read-only if')"
          :placeholder="rulePlaceholder"
        />
      </div>
      <!-- Link field whose target isn't guest-visible: the public dropdown will be
           empty until the author deliberately exposes those records to visitors -->
      <div
        v-if="guestSelectMissing"
        class="flex items-start gap-2 rounded-4 border border-outline-amber-2 bg-surface-amber-2 p-2.5"
      >
        <LucideTriangleAlert
          class="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-amber-6"
        />
        <div class="flex min-w-0 flex-col items-start gap-2">
          <p class="text-p-sm text-ink-gray-7">
            {{
              __(
                "Guests can't see {0} records. Grant select access to list them publicly.",
                [field.options],
              )
            }}
          </p>
          <Button
            size="sm"
            variant="outline"
            :loading="granting"
            :label="__('Grant Access')"
            @click="$emit('grant-guest')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { Switch, Button, FormControl, Tooltip } from 'frappe-ui'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import LucideX from '~icons/lucide/x'
import LucideLock from '~icons/lucide/lock'
import LucidePencil from '~icons/lucide/pencil'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import LucideInfo from '~icons/lucide/info'
import { fieldTypeIcon, fieldTypeLabel } from './fieldTypeIcon'

const props = defineProps({
  field: { type: Object, required: true },
  expanded: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
  guestSelectMissing: { type: Boolean, default: false },
  granting: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'toggle', 'remove', 'update', 'grant-guest'])

// writable proxies: never mutate the `field` prop directly — emit a patch the
// parent applies to its own model (keeps one-way data flow / lint happy)
function fieldModel(key) {
  return computed({
    get: () => props.field[key],
    set: (value) => emit('update', { [key]: value }),
  })
}
const labelModel = fieldModel('label')
const reqdModel = fieldModel('reqd')
const placeholderModel = fieldModel('placeholder')
const descriptionModel = fieldModel('field_description')
const dependsOnModel = fieldModel('depends_on')
const mandatoryDependsOnModel = fieldModel('mandatory_depends_on')
const readOnlyDependsOnModel = fieldModel('read_only_depends_on')
const rulePlaceholder = 'eval:doc.fieldname == "value"'

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
