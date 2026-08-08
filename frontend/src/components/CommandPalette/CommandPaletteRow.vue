<template>
  <li
    :id="optionId"
    role="option"
    :aria-selected="active"
    class="flex h-9 cursor-pointer items-center gap-3 rounded-md px-3 text-base"
    :class="active ? 'bg-surface-gray-2 text-ink-gray-9' : 'text-ink-gray-7'"
    @click="$emit('select')"
    @mousemove="$emit('activate')"
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

defineProps({
  command: { type: Object, required: true },
  active: { type: Boolean, default: false },
  optionId: { type: String, required: true },
})

defineEmits(['activate', 'select'])
</script>
