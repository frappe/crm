<!-- One row of the Sidebar editor: a built-in page or a DocType. -->
<template>
  <div
    class="flex h-10 items-center gap-1 rounded-4 pl-1 pr-2 hover:bg-surface-gray-1"
  >
    <span
      class="drag-handle grid w-6 shrink-0 cursor-grab place-items-center text-ink-gray-4 hover:text-ink-gray-6"
      :aria-label="__('Drag to reorder')"
    >
      <span class="lucide-grip-vertical size-4" aria-hidden="true" />
    </span>
    <span
      class="grid w-7 shrink-0 place-items-start"
      :class="item.hidden ? 'text-ink-gray-4' : 'text-ink-gray-7'"
    >
      <Icon :icon="sidebarItemIcon(item)" class="size-4" />
    </span>
    <span
      class="w-44 shrink-0 truncate text-base"
      :class="item.hidden ? 'text-ink-gray-5' : 'text-ink-gray-9'"
    >
      {{ __(item.label) }}
    </span>
    <span
      class="min-w-0 flex-1 truncate text-sm"
      :class="item.hidden ? 'text-ink-gray-5' : 'text-ink-gray-6'"
      :title="note"
    >
      {{ note }}
    </span>
    <span class="flex w-16 shrink-0 justify-end gap-1">
      <Button
        variant="ghost"
        :icon="item.hidden ? 'lucide-eye-off' : 'lucide-eye'"
        :label="item.hidden ? __('Show') : __('Hide')"
        :aria-pressed="!item.hidden"
        @click="emit('toggle-hidden')"
      />
      <Button
        variant="ghost"
        icon="lucide-pencil"
        :label="__('Edit')"
        @click="emit('edit')"
      />
    </span>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { sidebarItemIcon } from '@/utils/navigation'
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})
const emit = defineEmits(['toggle-hidden', 'edit'])

const note = computed(() => {
  const parts = []
  if (props.item.hidden) parts.push(__('Hidden'))
  parts.push(props.item.is_standard ? __('Built-in') : props.item.dt)
  return parts.join(' · ')
})
</script>
