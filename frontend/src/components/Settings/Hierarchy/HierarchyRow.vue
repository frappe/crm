<template>
  <div
    class="group flex items-center gap-2 p-1.5 text-base hover:bg-surface-gray-2 select-none border-b"
    :class="[rowClass, canEdit ? 'cursor-grab' : 'cursor-pointer']"
    :draggable="canEdit"
    @dragstart="canEdit && handlers.onDragStart($event, node)"
    @dragend="canEdit && handlers.onDragEnd(node)"
    @dragover.prevent="canEdit && handlers.onDragOver($event, node)"
    @dragleave="canEdit && handlers.onDragLeave(node)"
    @drop.prevent="canEdit && handlers.onDrop(node)"
    @click="hasChildren && emit('toggle', $event)"
  >
    <FeatherIcon
      v-if="hasChildren"
      :name="isCollapsed ? 'chevron-right' : 'chevron-down'"
      class="size-4 text-ink-gray-5 shrink-0 cursor-pointer"
    />
    <span v-else class="size-4 shrink-0 flex items-center justify-center">
      <span class="size-1.5 rounded-full bg-gray-500" />
    </span>

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
      v-if="canEdit"
      class="ml-auto flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
      @click.stop
    >
      <Popover placement="bottom-end" @close="resetSelection">
        <template #target="{ togglePopover }">
          <Tooltip :text="__('Add direct reports')">
            <Button
              variant="ghost"
              size="sm"
              icon="plus"
              @click="togglePopover()"
            />
          </Tooltip>
        </template>
        <template #body="{ togglePopover }">
          <div
            class="mt-1 rounded-lg bg-surface-white shadow-2xl w-72 border border-outline-gray-2"
          >
            <UserMultiSelect
              v-model="selected"
              :candidates="getCandidates(node)"
            />
            <div class="border-t p-1.5 flex justify-end">
              <Button
                variant="solid"
                :disabled="!selected.length"
                :label="__('Add ({0})', [selected.length])"
                @click="commit(togglePopover)"
              />
            </div>
          </div>
        </template>
      </Popover>
      <Dropdown :options="moreOptions" placement="right">
        <Button
          variant="ghost"
          size="sm"
          icon="more-horizontal"
          @blur="resetConfirms"
        />
      </Dropdown>
    </div>
  </div>
</template>

<script setup>
import UserMultiSelect from './UserMultiSelect.vue'
import { ConfirmDelete } from '@/utils'
import {
  Badge,
  Button,
  Dropdown,
  FeatherIcon,
  Popover,
  Tooltip,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  hasChildren: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false },
  rowClass: { type: String, default: '' },
  handlers: { type: Object, required: true },
  getCandidates: { type: Function, required: true },
  canEdit: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'bulk-add', 'remove', 'move-to-root'])

const selected = ref([])
const confirmRemove = ref(false)
const confirmReassign = ref(false)
const confirmCascade = ref(false)

function commit(togglePopover) {
  if (!selected.value.length) return
  emit('bulk-add', { parent: props.node, userIds: selected.value })
  selected.value = []
  togglePopover()
}

function resetSelection() {
  selected.value = []
}

function resetConfirms() {
  confirmRemove.value = false
  confirmReassign.value = false
  confirmCascade.value = false
}

const moreOptions = computed(() => {
  const opts = []
  if (props.node.reports_to) {
    opts.push({
      label: __('Move to top level'),
      icon: 'corner-up-left',
      onClick: () => emit('move-to-root', props.node),
    })
  }
  if (props.hasChildren) {
    opts.push(
      ...ConfirmDelete({
        onConfirmDelete: () =>
          emit('remove', { node: props.node, mode: 'reassign' }),
        isConfirmingDelete: confirmReassign,
        label: __('Reassign & remove'),
      }),
      ...ConfirmDelete({
        onConfirmDelete: () =>
          emit('remove', { node: props.node, mode: 'cascade' }),
        isConfirmingDelete: confirmCascade,
        label: __('Remove with reports'),
      }),
    )
  } else {
    opts.push(
      ...ConfirmDelete({
        onConfirmDelete: () =>
          emit('remove', { node: props.node, mode: 'simple' }),
        isConfirmingDelete: confirmRemove,
        label: __('Remove'),
      }),
    )
  }
  return opts
})
</script>
