<template>
  <li
    :id="optionId"
    role="option"
    :aria-selected="active"
    :aria-disabled="command.disabled || undefined"
    class="flex h-9 items-center gap-3 rounded-md px-3 text-base"
    :class="rowClasses"
    @click="!command.disabled && $emit('select')"
    @mousemove="!command.disabled && $emit('activate')"
  >
    <Icon v-if="command.icon" :icon="command.icon" class="size-4 shrink-0" />
    <span class="flex-1 truncate">
      {{ command.translate === false ? command.title : __(command.title) }}
    </span>
    <span v-if="command.subtitle" class="truncate text-sm text-ink-gray-5">
      {{ command.subtitle }}
    </span>
    <span v-if="command.children" class="lucide-chevron-right size-4" />
    <span v-if="command.checked" class="lucide-check size-4" />
    <KeyboardShortcut v-if="command.hint" :combo="command.hint" bg />
  </li>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { KeyboardShortcut } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  command: { type: Object, required: true },
  active: { type: Boolean, default: false },
  optionId: { type: String, required: true },
})

defineEmits(['activate', 'select'])

const rowClasses = computed(() => {
  if (props.command.disabled) return 'cursor-not-allowed text-ink-gray-4'
  if (props.active) return 'cursor-pointer bg-surface-gray-2 text-ink-gray-9'
  return 'cursor-pointer text-ink-gray-7'
})
</script>
