<template>
  <Editor
    v-model="content"
    :extensions="extensions"
    :placeholder="placeholder"
    :editable="!disabled"
    :upload-function="(file) => uploadFile(file)"
    @change="onContentChange"
    @blur="onBlur"
  >
    <EditorFixedMenu
      v-if="fixedMenu && !disabled"
      :items="fullToolbar"
      class="w-full overflow-x-auto rounded-t-lg border border-outline-gray-2 p-1"
    />
    <EditorBubbleMenu v-if="bubbleMenu" :items="bubbleToolbar" />
    <EditorContent :class="editorClasses" />
  </Editor>
</template>

<script setup>
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  EditorBubbleMenu,
} from 'frappe-ui/editor'
import {
  buildEditorExtensions,
  fullToolbar,
  bubbleToolbar,
  uploadFile,
} from '@/components/editor/config'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  value: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  editorClass: { type: String, default: '' },
  variant: {
    type: String,
    default: 'subtle',
    validator: (v) => ['outline', 'subtle', 'ghost'].includes(v),
  },
  size: {
    type: String,
    default: 'sm',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  fixedMenu: { type: Boolean, default: true },
  bubbleMenu: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])

const editorClasses = computed(() => {
  const defaultClass = 'max-h-[40vh] overflow-y-auto min-w-full'

  const variantMap = {
    outline: props.disabled
      ? 'border border-t rounded-lg bg-surface-base'
      : 'border border-t-0 rounded-b-lg bg-surface-base',
    subtle: props.disabled
      ? 'border border-t rounded-lg bg-surface-gray-2'
      : 'border border-t-0 rounded-b-lg bg-surface-gray-2',
    ghost: 'bg-transparent',
  }
  const variantClass = variantMap[props.variant]

  const sizeMap = {
    sm: props.disabled
      ? 'prose-sm min-h-[4rem] p-2'
      : 'prose-sm min-h-[8rem] p-2',
    md: props.disabled
      ? 'prose-base min-h-[4rem] p-3'
      : 'prose-base min-h-[10rem] p-3',
    lg: props.disabled
      ? 'prose-lg min-h-[4rem] p-4'
      : 'prose-lg min-h-[12rem] p-4',
  }
  const sizeClasess = sizeMap[props.size]

  const disableClass = props.disabled ? 'opacity-60' : ''

  return [
    variantClass,
    sizeClasess,
    defaultClass,
    disableClass,
    props.editorClass,
  ]
})

const extensions = buildEditorExtensions()

const content = ref(props.value ?? '')
const isDirty = ref(false)

watch(
  () => props.value,
  (val) => {
    content.value = val ?? ''
  },
)

function onContentChange(val) {
  if (val !== (props.value ?? '')) isDirty.value = true
}

function onBlur() {
  if (!isDirty.value) return
  isDirty.value = false
  emit('change', content.value)
}
</script>
