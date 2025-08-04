<template>
  <div
    class="group flex w-full items-center justify-between rounded bg-transparent p-1 pl-2 text-base text-ink-gray-8 transition-colors hover:bg-surface-gray-3 active:bg-surface-gray-4"
  >
    <div class="flex flex-1 items-center justify-between gap-7">
      <div v-show="!editMode">{{ option.value }}</div>
      <TextInput
        ref="inputRef"
        v-show="editMode"
        v-model="option.value"
        class="w-full"
        :placeholder="option.placeholder"
        @blur.stop="saveOption"
        @keydown.enter.stop="(e) => e.target.blur()"
      />

      <div class="actions flex items-center justify-center">
        <Button
          v-if="editMode"
          variant="ghost"
          :label="__('Save')"
          size="sm"
          class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
          @click="saveOption"
        />
        <Tooltip text="Set As Primary" v-if="!isNew && !option.selected">
          <div>
            <Button
              variant="ghost"
              size="sm"
              class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
              @click="option.onClick"
            >
              <template #icon>
                <SuccessIcon />
              </template>
            </Button>
          </div>
        </Tooltip>
        <Tooltip v-if="!editMode" text="Edit">
          <div>
            <Button
              variant="ghost"
              size="sm"
              class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
              @click="toggleEditMode"
            >
              <template #icon>
                <EditIcon />
              </template>
            </Button>
          </div>
        </Tooltip>
        <Tooltip text="Delete">
          <div>
            <Button
              variant="ghost"
              icon="x"
              size="sm"
              class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
              @click="() => option.onDelete(option, isNew)"
            />
          </div>
        </Tooltip>
      </div>
    </div>
    <div v-if="option.selected">
      <FeatherIcon name="check" class="text-ink-gray-5 h-4 w-6" size="sm" />
    </div>
  </div>
</template>

<script setup>
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { TextInput, Tooltip } from 'frappe-ui'
import { nextTick, ref, onMounted } from 'vue'

const props = defineProps({
  option: {
    type: Object,
    default: () => {},
  },
})

const editMode = ref(false)
const isNew = ref(false)
const inputRef = ref(null)

onMounted(() => {
  if (!props.option?.value) {
    editMode.value = true
    isNew.value = true
    nextTick(() => inputRef.value.el.focus())
  }
})

const toggleEditMode = () => {
  editMode.value = !editMode.value
  editMode.value && nextTick(() => inputRef.value.el.focus())
}

const saveOption = (e) => {
  if (!e.target.value) return
  toggleEditMode()
  props.option.onSave(props.option, isNew.value)
  isNew.value = false
}
</script>
