<template>
  <div class="flex items-center justify-between gap-7">
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
      <Tooltip text="Set As Primary" v-if="!isNew && !option.selected">
        <Button
          variant="ghost"
          size="sm"
          class="opacity-0 hover:bg-gray-300 group-hover:opacity-100"
          @click="option.onClick"
        >
          <SuccessIcon />
        </Button>
      </Tooltip>
      <Tooltip text="Edit">
        <Button
          variant="ghost"
          size="sm"
          class="opacity-0 hover:bg-gray-300 group-hover:opacity-100"
          @click="toggleEditMode"
        >
          <EditIcon />
        </Button>
      </Tooltip>
      <Tooltip text="Delete">
        <Button
          variant="ghost"
          icon="x"
          size="sm"
          class="opacity-0 hover:bg-gray-300 group-hover:opacity-100"
          @click="() => option.onDelete(option, isNew)"
        />
      </Tooltip>
    </div>
  </div>
  <div>
    <FeatherIcon
      v-if="option.selected"
      name="check"
      class="text-primary-500 h-4 w-6"
      size="sm"
    />
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

const saveOption = () => {
  toggleEditMode()
  props.option.onSave(props.option, isNew.value)
  isNew.value = false
}
</script>
