<template>
  <div
    class="hierarchy-tree-row flex items-center gap-1 mb-1"
    :data-has-children="hasChildren"
  >
    <div
      v-if="hasChildren"
      class="z-10 size-5 shrink-0 flex items-center justify-center rounded-full border border-outline-elevation-2 bg-white text-ink-gray-1 cursor-pointer hover:bg-surface-gray-2"
      @click.stop="emit('toggle', $event)"
    >
      <FeatherIcon
        :name="isCollapsed ? 'chevron-right' : 'chevron-down'"
        class="size-3 stroke-2 stroke-ink-gray-5"
      />
    </div>
    <span v-else class="size-5 shrink-0"></span>

    <div
      class="group relative flex-1 flex items-center gap-2 px-2 py-1.5 text-base rounded-md select-none after:content-[''] after:absolute after:bottom-0 after:left-1 after:right-3 after:border-outline-elevation-2"
      :class="[
        rowClass,
        canEdit ? 'cursor-grab' : 'cursor-pointer',
        isHighlighted ? 'bg-surface-gray-1' : 'hover:bg-surface-gray-1',
        isLast ? 'after:hidden' : '',
      ]"
      :draggable="canEdit"
      @dragstart="canEdit && handlers.onDragStart($event, node)"
      @dragend="canEdit && handlers.onDragEnd(node)"
      @dragover.prevent="canEdit && handlers.onDragOver($event, node)"
      @dragleave="canEdit && handlers.onDragLeave(node)"
      @drop.prevent="canEdit && handlers.onDrop(node)"
      @click="hasChildren && emit('toggle', $event)"
    >
      <Avatar
        :image="node.user_image"
        :label="node.full_name"
        size="lg"
        class="shrink-0"
      />

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
        class="ml-auto flex gap-1 transition-opacity"
        :class="
          isHighlighted ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        "
        @click.stop
      >
        <Popover placement="bottom-end" @update:show="popoverOpen = $event">
          <template #target="{ togglePopover }">
            <Tooltip :text="__('Add direct reports')">
              <Button
                variant="ghost"
                size="sm"
                icon="lucide-plus"
                @click="togglePopover()"
              />
            </Tooltip>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="mt-1 rounded-lg bg-surface-base shadow-2xl w-72 border border-outline-gray-2"
            >
              <UserMultiSelect
                v-model="selected"
                :candidates="getCandidates(node)"
                :loading="candidatesLoading"
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
          <template #default="{ open }">
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-more-horizontal"
              :class="syncDropdown(open)"
            />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import UserMultiSelect from './UserMultiSelect.vue'
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  FeatherIcon,
  Popover,
  Tooltip,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  hasChildren: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false },
  isLast: { type: Boolean, default: false },
  rowClass: { type: String, default: '' },
  handlers: { type: Object, required: true },
  getCandidates: { type: Function, required: true },
  candidatesLoading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'bulk-add', 'remove', 'move-to-root'])

const selected = ref([])
const popoverOpen = ref(false)
const dropdownOpen = ref(false)

const isHighlighted = computed(() => popoverOpen.value || dropdownOpen.value)

function syncDropdown(open) {
  if (dropdownOpen.value !== open) dropdownOpen.value = open
  return ''
}

watch(popoverOpen, (open) => {
  if (!open) selected.value = []
})

function commit(togglePopover) {
  if (!selected.value.length) return
  emit('bulk-add', { parent: props.node, userIds: selected.value })
  selected.value = []
  togglePopover()
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
  opts.push({
    label: __('Delete'),
    icon: 'trash-2',
    onClick: () => emit('remove', props.node),
  })
  return opts
})
</script>

<style>
li:has(> .hierarchy-tree-row) {
  position: relative;
}

li:has(> .hierarchy-tree-row)::before {
  content: '';
  position: absolute;
  left: -18px;
  top: -8px;
  bottom: -4px;
  border-left: 1px solid var(--outline-elevation-2);
}

li:has(> .hierarchy-tree-row)::after {
  content: '';
  position: absolute;
  left: -18px;
  top: 20px;
  width: 42px;
  border-bottom: 1px solid var(--outline-elevation-2);
}

li:has(> [data-has-children='true'])::after {
  width: 16px;
}

li:has(> .hierarchy-tree-row):last-child::before {
  bottom: auto;
  height: 30px;
  width: 16px;
  border-bottom: 1px solid var(--outline-elevation-2);
  border-bottom-left-radius: 6px;
}

li:has(> [data-has-children='false']):last-child::before {
  width: 42px;
}

li:has(> .hierarchy-tree-row):last-child::after {
  display: none;
}
</style>
