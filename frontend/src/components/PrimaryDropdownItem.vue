<template>
  <div
    class="group flex w-full gap-2 rounded p-1 pl-2 text-base text-ink-gray-8 transition-colors"
    :class="
      editMode
        ? 'items-start'
        : 'items-center cursor-pointer hover:bg-surface-gray-3 active:bg-surface-gray-4'
    "
    @click="selectRow"
  >
    <!-- Prefix reserved on every row so text stays aligned; the primary row
         shows the indicator. Clicking a row makes it primary. -->
    <div class="flex h-7 w-4 shrink-0 items-center justify-center">
      <Tooltip v-if="option.selected" :text="__('Primary')">
        <span class="lucide-check size-4 text-ink-gray-8" aria-hidden="true" />
      </Tooltip>
    </div>

    <div class="min-w-0 flex-1">
      <!-- v-if, not v-show: TextInput has a fragment root when it has no
           label/description/error, and Vue drops directives on such roots -->
      <div v-if="!editMode" class="truncate">{{ localOption.value }}</div>
      <div v-else class="flex max-w-40 flex-col gap-1">
        <TextInput
          ref="inputRef"
          v-model="localOption.value"
          class="w-full"
          :placeholder="placeholder"
          @blur.stop="saveOption"
          @keydown.enter.stop="(e) => e.target.blur()"
        />
        <div v-if="errorMessage" class="text-xs font-medium text-ink-red-6">
          {{ errorMessage }}
        </div>
      </div>
    </div>

    <div v-if="!editMode" class="shrink-0">
      <Dropdown
        :options="menuOptions"
        :side="isMobileView ? 'bottom' : 'right'"
        :align="isMobileView ? 'end' : 'start'"
        offset="2"
      >
        <template #default="{ open }">
          <button
            class="flex cursor-pointer rounded p-1 text-ink-gray-6 transition-colors hover:bg-surface-gray-4"
            :class="open ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
            @click.stop
          >
            <FeatherIcon name="more-vertical" class="size-4" />
          </button>
        </template>
      </Dropdown>
    </div>
    <div v-else class="flex shrink-0 items-center">
      <!-- mousedown.prevent keeps the input from blurring when a button is
           clicked, so Cancel discards instead of the blur-save persisting it -->
      <Button
        variant="ghost"
        :label="__('Save')"
        @mousedown.prevent
        @click="saveOption"
      />
      <Button
        variant="ghost"
        icon="lucide-x"
        :tooltip="__('Cancel')"
        @mousedown.prevent
        @click="cancelEdit"
      />
    </div>
  </div>
</template>

<script setup>
import { Dropdown, TextInput, Tooltip } from 'frappe-ui'
import { isMobileView } from '@/composables/settings'
import { nextTick, ref, onMounted, reactive, watch } from 'vue'

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  placeholder: { type: String, default: '' },
  validate: { type: Function, default: null },
})

const localOption = reactive({ ...props.option })
watch(
  () => props.option,
  (val) => Object.assign(localOption, val),
  { deep: true },
)

const editMode = ref(false)
const isNew = ref(false)
const inputRef = ref(null)
const errorMessage = ref('')
const saving = ref(false)

watch(
  () => localOption.value,
  () => (errorMessage.value = ''),
)

onMounted(() => {
  if (!props.option?.value) {
    editMode.value = true
    isNew.value = true
    nextTick(() => inputRef.value?.el?.focus())
  }
})

const menuOptions = [
  {
    label: __('Edit'),
    icon: 'lucide-square-pen',
    onClick: () => toggleEditMode(),
  },
  {
    label: __('Delete'),
    icon: 'lucide-trash-2',
    theme: 'red',
    onClick: () => props.option.onDelete(props.option, isNew.value),
  },
]

const selectRow = () => {
  if (editMode.value || isNew.value) return
  if (!props.option.selected) props.option.onClick?.()
}

const toggleEditMode = () => {
  editMode.value = !editMode.value
  if (editMode.value) {
    nextTick(() => inputRef.value?.el?.focus())
  }
}

const cancelEdit = () => {
  // Exit edit mode first so a blur fired while the input unmounts is a no-op.
  editMode.value = false
  if (isNew.value) {
    props.option.onDelete(props.option, true)
    return
  }
  localOption.value = props.option.value
}

const saveOption = async () => {
  // Blur and the Save click both fire this; guard so a create/update is
  // issued once, never duplicated. Also bail once edit mode has exited (e.g.
  // Cancel), so an unmount blur can't persist a discarded value.
  if (saving.value || !editMode.value) return

  const value = localOption.value?.trim()
  if (!value) return

  const error = props.validate?.(value)
  if (error) {
    errorMessage.value = error
    nextTick(() => inputRef.value?.el?.focus())
    return
  }

  saving.value = true
  try {
    const saved = await props.option.onSave(
      { ...props.option, value },
      isNew.value,
    )
    // Only leave edit mode once the value is actually persisted; a failed
    // save stays editable instead of showing an unsaved value as saved.
    if (!saved) {
      errorMessage.value = __('Could not save, please try again')
      nextTick(() => inputRef.value?.el?.focus())
      return
    }
    editMode.value = false
    isNew.value = false
  } catch {
    errorMessage.value = __('Could not save, please try again')
    nextTick(() => inputRef.value?.el?.focus())
  } finally {
    saving.value = false
  }
}
</script>
