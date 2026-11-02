<template>
  <div
    class="flex w-full min-w-0 items-center rounded-4 px-2 text-sm"
    :class="[
      command.snippet ? 'py-1.5' : 'h-9',
      active ? 'bg-surface-gray-2' : '',
      command.disabled
        ? 'text-ink-gray-4'
        : active
          ? 'text-ink-gray-9'
          : 'text-ink-gray-6',
    ]"
  >
    <Icon
      v-if="command.icon"
      :icon="command.icon"
      class="me-2.5 size-3.5 shrink-0"
      :class="active ? 'text-ink-gray-7' : 'text-ink-gray-5'"
    />
    <div class="flex min-w-0 flex-1 flex-col gap-0.5">
      <span class="overflow-hidden text-ellipsis whitespace-nowrap">
        {{ command.translate === false ? command.title : __(command.title) }}
      </span>
      <span
        v-if="command.snippet"
        class="overflow-hidden text-ellipsis whitespace-nowrap text-xs text-ink-gray-5"
      >
        <MarkedText :text="command.snippet" />
      </span>
    </div>
    <span v-if="command.subtitle" class="ms-3 shrink-0 text-xs text-ink-gray-4">
      {{ command.subtitle }}
    </span>
    <span
      v-if="command.badge"
      class="ms-2 shrink-0 rounded-4 bg-surface-gray-2 px-1.5 py-0.5 text-xs"
      :class="command.badgeClass || 'text-ink-gray-5'"
    >
      {{ command.badge }}
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
import MarkedText from './MarkedText.vue'

defineProps({
  command: { type: Object, required: true },
  active: { type: Boolean, required: true },
})
</script>
