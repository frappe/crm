<template>
  <div
    class="cursor-grab group flex items-center gap-2 p-1 text-base hover:bg-surface-gray-2 hover:rounded-sm select-none border-b"
    :class="rowClass"
    :draggable="true"
    @dragstart="handlers.onDragStart($event, node)"
    @dragend="handlers.onDragEnd(node)"
    @dragover.prevent="handlers.onDragOver($event, node)"
    @dragleave="handlers.onDragLeave(node)"
    @drop.prevent="handlers.onDrop(node)"
    @click="hasChildren && emit('toggle', $event)"
  >
    <FeatherIcon
      v-if="hasChildren"
      :name="isCollapsed ? 'chevron-right' : 'chevron-down'"
      class="size-4 text-ink-gray-5 shrink-0 cursor-pointer"
    />
    <span v-else class="size-4 shrink-0" />

    <Avatar :image="node.user_image" :label="node.full_name" size="sm" />
    <span class="text-ink-gray-8 truncate">
      {{ node.full_name }}
    </span>
    <span class="text-ink-gray-4">{{ node.role_label }}</span>
    <Badge
      v-if="!node.enabled"
      :label="__('disabled')"
      theme="gray"
      variant="subtle"
      size="sm"
    />

    <div
      class="ml-auto flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
      @click.stop
    >
      <Tooltip :text="__('Add direct report')">
        <Button
          variant="ghost"
          size="sm"
          icon="plus"
          @click="emit('add', node)"
        />
      </Tooltip>
      <Dropdown :options="moreOptions" placement="right">
        <Button variant="ghost" size="sm" icon="more-horizontal" />
      </Dropdown>
    </div>
  </div>
</template>

<script setup>
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  FeatherIcon,
  Tooltip,
} from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  hasChildren: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false },
  rowClass: { type: String, default: '' },
  handlers: { type: Object, required: true },
})

const emit = defineEmits(['toggle', 'add', 'remove', 'move-to-root'])

const moreOptions = computed(() =>
  [
    {
      label: __('Move to root'),
      icon: 'corner-up-left',
      onClick: () => emit('move-to-root', props.node),
      condition: () => !!props.node.reports_to,
    },
    {
      label: __('Remove from hierarchy'),
      icon: 'trash-2',
      onClick: () => emit('remove', props.node),
    },
  ].filter((o) => (o.condition ? o.condition() : true)),
)
</script>
