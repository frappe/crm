<template>
  <div>
    <!-- Tabbable so the popover focuses the row on open, not the first action
         button, which would pop its tooltip open -->
    <ItemListRow
      class="group"
      size="sm"
      :class="editMode ? '' : 'cursor-pointer hover:bg-surface-gray-2'"
      :selected="localOption.selected"
      :tabindex="editMode ? -1 : 0"
      @click="selectRow"
      @keydown="selectRowOnKey"
    >
      <!-- Reserved on every row so labels stay aligned -->
      <template #prefix>
        <Tooltip v-if="localOption.selected" :text="__('Primary')">
          <span
            class="lucide-check size-4 text-ink-gray-8"
            aria-hidden="true"
          />
        </Tooltip>
        <span v-else class="size-4" aria-hidden="true" />
      </template>

      <!-- v-if, not v-show: Vue drops directives on TextInput's fragment root -->
      <div v-if="!editMode" class="truncate">
        {{ localOption.value }}
      </div>
      <!-- -mx-2 -my-1 cancel the input's own box so it sits where the read-mode
           text does, inside the row's padding; the forms base layer gives the
           input a white background until it is cleared -->
      <TextInput
        v-else
        ref="inputRef"
        v-model="localOption.value"
        size="sm"
        variant="ghost"
        class="-mx-2 -my-1 [&_input]:bg-transparent"
        :placeholder="placeholder"
        @blur.stop="saveOption"
        @keydown.enter.stop="(e) => e.target.blur()"
      />

      <template #suffix>
        <!-- Left visible on touch, which has no hover to reveal them -->
        <div
          v-if="!editMode"
          class="-my-1 flex items-center gap-1 transition-opacity [&:has(:focus-visible)]:opacity-100 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100"
        >
          <Button
            variant="ghost"
            icon="lucide-square-pen"
            :tooltip="__('Edit')"
            @click.stop="toggleEditMode"
          />
          <Button
            variant="ghost"
            theme="red"
            icon="lucide-trash-2"
            :tooltip="__('Delete')"
            @click.stop="option.onDelete(option, isNew)"
          />
        </div>
        <!-- mousedown.prevent stops the blur-save, so Cancel can discard -->
        <div v-else class="-my-1 flex items-center gap-1">
          <Button
            variant="outline"
            icon="lucide-check"
            size="sm"
            :label="__('Save')"
            @mousedown.prevent
            @click.stop="saveOption"
          />
          <Button
            variant="outline"
            icon="lucide-x"
            :tooltip="__('Cancel')"
            @mousedown.prevent
            @click.stop="cancelEdit"
          />
        </div>
      </template>
    </ItemListRow>

    <!-- pl-8 = the row's px-2 + prefix + gap, so it lines up with the label -->
    <ErrorMessage
      v-if="errorMessage"
      class="pl-8 pr-2 pt-1"
      :message="errorMessage"
    />
  </div>
</template>

<script setup>
import { ErrorMessage, ItemListRow, TextInput, Tooltip } from 'frappe-ui'
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

const selectRow = () => {
  if (editMode.value || isNew.value) return
  if (!props.option.selected) props.option.onClick?.()
}

const selectRowOnKey = (e) => {
  if (editMode.value || (e.key !== 'Enter' && e.key !== ' ')) return
  e.preventDefault()
  selectRow()
}

const toggleEditMode = () => {
  editMode.value = !editMode.value
  if (editMode.value) {
    nextTick(() => inputRef.value?.el?.focus())
  }
}

const cancelEdit = () => {
  // Exit first so the blur fired while the input unmounts is a no-op
  editMode.value = false
  if (isNew.value) {
    props.option.onDelete(props.option, true)
    return
  }
  localOption.value = props.option.value
}

const saveOption = async () => {
  // Blur and the Save click both fire this: save once, and never after edit
  // mode has exited, so an unmount blur can't persist a discarded value
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
    // A failed save stays editable instead of showing the value as saved
    if (!saved) {
      errorMessage.value = __('Could not save, try again')
      nextTick(() => inputRef.value?.el?.focus())
      return
    }
    editMode.value = false
    isNew.value = false
  } catch {
    errorMessage.value = __('Could not save, try again')
    nextTick(() => inputRef.value?.el?.focus())
  } finally {
    saving.value = false
  }
}
</script>
