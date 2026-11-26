<!-- One row of the App menu editor: a built-in item, a link, a submenu or a divider. -->
<template>
  <div
    class="flex h-10 items-center gap-1 rounded-4 pl-1 pr-2 hover:bg-surface-gray-1 [[data-dragging]_&]:hover:bg-transparent"
  >
    <span
      class="drag-handle grid w-6 shrink-0 cursor-grab place-items-center text-ink-gray-4 hover:text-ink-gray-6"
      :aria-label="__('Drag to reorder')"
    >
      <span class="lucide-grip-vertical size-4" aria-hidden="true" />
    </span>
    <!-- Indented, with a guide down from the submenu's icon, inside a submenu's
         list; CSS decides, so a row indents while it is dragged in. -->
    <span
      class="relative hidden w-7 shrink-0 self-stretch before:absolute before:inset-y-0 before:left-[7.5px] before:border-l before:border-outline-gray-2 [[data-links]_&]:block"
      aria-hidden="true"
    />

    <template v-if="isDivider">
      <span
        class="grid w-7 shrink-0 place-items-start"
        :class="item.hidden ? 'text-ink-gray-4' : 'text-ink-gray-5'"
      >
        <span class="lucide-separator-horizontal size-4" aria-hidden="true" />
      </span>
      <span
        class="flex-1 text-base"
        :class="item.hidden ? 'text-ink-gray-4' : 'text-ink-gray-5'"
      >
        {{ __('Divider') }}
        <template v-if="item.hidden"> · {{ __('Hidden') }}</template>
      </span>
    </template>
    <template v-else>
      <span class="grid w-7 shrink-0 place-items-start" :class="iconColor">
        <component :is="icon" class="size-4" />
      </span>
      <span
        class="shrink-0 truncate text-base"
        :class="[
          'w-44 [[data-links]_&]:w-36',
          isSubmenu && 'font-medium',
          isMuted ? 'text-ink-gray-5' : 'text-ink-gray-9',
        ]"
      >
        {{ __(item.label) }}
      </span>
      <span
        class="flex min-w-0 flex-1 items-center gap-1 text-sm"
        :class="isMuted ? 'text-ink-gray-5' : 'text-ink-gray-6'"
      >
        <span class="truncate" :title="note">{{ note }}</span>
        <span
          v-if="isLink && item.open_in_new_window"
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
  </div>
</template>

<script setup>
import { menuItemIcon } from '@/composables/appMenu'
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  /** Links of a submenu row, to count them. */
  links: { type: Array, default: () => [] },
})
const emit = defineEmits(['toggle-hidden', 'edit', 'remove'])

const isDivider = computed(() => props.item.type === 'Separator')
const isSubmenu = computed(() => props.item.type === 'Submenu')
const isLink = computed(
  () => props.item.type === 'Route' && !props.item.is_standard,
)
const isEmptySubmenu = computed(() => isSubmenu.value && !props.links.length)
const isMuted = computed(() => props.item.hidden || isEmptySubmenu.value)
const icon = computed(() => menuItemIcon(props.item))

const iconColor = computed(() => {
  if (props.item.hidden) return 'text-ink-gray-4'
  return isEmptySubmenu.value ? 'text-ink-gray-5' : 'text-ink-gray-7'
})

const note = computed(() => {
  const parts = []
  if (props.item.hidden) parts.push(__('Hidden'))
  if (props.item.is_standard) parts.push(__('Built-in'))
  else if (isSubmenu.value) parts.push(submenuNote())
  else parts.push((props.item.route || '').replace(/^https?:\/\//, ''))
  return parts.join(' · ')
})

function submenuNote() {
  const count = props.links.length
  if (!count) return __('Empty, so not shown')
  return count === 1 ? __('1 link') : __('{0} links', [count])
}
</script>
