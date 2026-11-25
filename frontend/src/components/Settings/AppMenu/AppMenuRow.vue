<!-- One row of the App menu editor: a built-in item, a link or a divider. -->
<template>
  <li
    class="flex items-center gap-1 border-b border-outline-gray-1 pl-1 pr-2 last:border-b-0"
    :class="isDivider ? 'h-9' : 'h-11'"
  >
    <span
      class="drag-handle grid w-6 shrink-0 cursor-grab place-items-center text-ink-gray-4 hover:text-ink-gray-6"
      :aria-label="__('Drag to reorder')"
    >
      <span class="lucide-grip-vertical size-4" aria-hidden="true" />
    </span>

    <template v-if="isDivider">
      <span class="w-7 shrink-0" />
      <span
        class="flex-1 text-base"
        :class="item.hidden ? 'text-ink-gray-4' : 'text-ink-gray-5'"
      >
        {{ __('Divider') }}
        <template v-if="item.hidden"> · {{ __('Hidden') }}</template>
      </span>
    </template>
    <template v-else>
      <span
        class="grid w-7 shrink-0 place-items-start"
        :class="item.hidden ? 'text-ink-gray-4' : 'text-ink-gray-7'"
      >
        <component :is="icon" class="size-4" />
      </span>
      <span
        class="w-44 shrink-0 truncate text-base"
        :class="item.hidden ? 'text-ink-gray-5' : 'text-ink-gray-9'"
      >
        {{ __(item.label) }}
      </span>
      <span
        class="flex min-w-0 flex-1 items-center gap-1 text-sm"
        :class="item.hidden ? 'text-ink-gray-5' : 'text-ink-gray-6'"
      >
        <span class="truncate">{{ note }}</span>
        <span
          v-if="item.open_in_new_window && !item.is_standard"
          class="lucide-external-link size-3.5 shrink-0"
          :aria-label="__('Opens in a new tab')"
        />
      </span>
    </template>

    <span class="flex w-16 shrink-0 justify-end gap-1">
      <Button
        v-if="!isDivider || item.is_standard"
        variant="ghost"
        :icon="item.hidden ? 'lucide-eye-off' : 'lucide-eye'"
        :label="item.hidden ? __('Show') : __('Hide')"
        :aria-pressed="!item.hidden"
        @click="emit('toggle-hidden')"
      />
      <Button
        v-if="isDivider && !item.is_standard"
        variant="ghost"
        icon="lucide-x"
        :label="__('Remove divider')"
        @click="emit('remove')"
      />
      <Button
        v-else-if="!item.is_standard"
        variant="ghost"
        icon="lucide-pencil"
        :label="__('Edit')"
        @click="emit('edit')"
      />
    </span>
  </li>
</template>

<script setup>
import { menuItemIcon } from '@/composables/appMenu'
import { computed } from 'vue'

const props = defineProps({ item: { type: Object, required: true } })
const emit = defineEmits(['toggle-hidden', 'edit', 'remove'])

const isDivider = computed(() => props.item.type === 'Separator')
const icon = computed(() => menuItemIcon(props.item))

const note = computed(() => {
  const parts = []
  if (props.item.hidden) parts.push(__('Hidden'))
  if (props.item.is_standard) parts.push(__('Built-in'))
  else parts.push((props.item.route || '').replace(/^https?:\/\//, ''))
  return parts.join(' · ')
})
</script>
