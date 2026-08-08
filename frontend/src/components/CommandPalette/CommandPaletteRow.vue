<template>
  <div
    class="flex h-9 w-full min-w-0 items-center rounded px-2 text-sm"
    :class="[
      active ? 'bg-surface-gray-2' : '',
      command.disabled ? 'text-ink-gray-4' : 'text-ink-gray-8',
    ]"
  >
    <Icon
      v-if="command.icon"
      :icon="command.icon"
      class="me-2.5 size-3.5 shrink-0"
      :class="active ? 'text-ink-gray-7' : 'text-ink-gray-5'"
    />
    <span
      class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap"
    >
      {{ command.translate === false ? command.title : __(command.title) }}
    </span>
    <span v-if="command.subtitle" class="ms-3 shrink-0 text-xs text-ink-gray-4">
      {{ command.subtitle }}
    </span>
    <LucideCheck
      v-if="command.checked"
      class="ms-3 size-3.5 shrink-0 text-ink-gray-7"
    />
    <LucideChevronRight
      v-if="command.children"
      class="ms-2 size-3.5 shrink-0 text-ink-gray-4"
    />
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import LucideCheck from '~icons/lucide/check'
import LucideChevronRight from '~icons/lucide/chevron-right'

defineProps({
  command: { type: Object, required: true },
  active: { type: Boolean, required: true },
})
</script>
