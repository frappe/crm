<template>
  <VueFlow
    :nodes="nodes"
    :edges="edges"
    class="workflow-flow"
    :fit-view-on-init="true"
    :fit-view-options="{ padding: 0.2, maxZoom: 0.85 }"
    :nodes-draggable="false"
    :nodes-connectable="false"
    :elements-selectable="!readonly"
    @node-click="selectNode($event.node.id)"
    @pane-click="selectNode('trigger')"
  >
    <Background pattern-color="#7e7e7e" :gap="24" :size="1.5" />
    <template #node-automation="{ id, data }">
      <div
        class="workflow-node"
        :class="nodeClasses(id, data)"
        :tabindex="readonly ? -1 : 0"
        :role="readonly ? undefined : 'button'"
        :aria-label="`${data.kicker}: ${data.label}`"
        @click.stop="selectNode(id)"
        @keydown.enter="selectNode(id)"
        @keydown.space.prevent="selectNode(id)"
      >
        <Handle v-if="!data.isTrigger" type="target" :position="Position.Top" />
        <div
          class="flex size-10 shrink-0 items-center justify-center rounded bg-surface-gray-2"
        >
          <component :is="data.icon" class="size-5 text-ink-gray-6" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-xs-semibold text-ink-gray-5">{{ data.kicker }}</div>
          <div class="truncate text-base-medium text-ink-gray-8">
            {{ data.label }}
          </div>
        </div>
        <ErrorIcon v-if="data.error" class="size-4 shrink-0 text-ink-red-4" />
        <Handle type="source" :position="Position.Bottom" />
        <div v-if="!readonly" class="workflow-node-actions">
          <Button
            v-for="slot in addSlots(data)"
            :key="slot.key"
            :label="slot.label"
            icon-left="lucide-plus"
            size="sm"
            @click.stop="$emit('add-step', data.step, slot.branch)"
          />
        </div>
      </div>
    </template>
  </VueFlow>
</template>

<script setup>
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { Handle, Position, VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import ErrorIcon from '~icons/lucide/circle-alert'
import { Button } from 'frappe-ui'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'add-step'])

function selectNode(id) {
  if (!props.readonly) emit('select', id)
}

function nodeClasses(id, data) {
  return {
    'workflow-node-selected': !props.readonly && props.selectedId === id,
    'workflow-node-error': Boolean(data.error),
  }
}

function addSlots(data) {
  if (data.isTrigger)
    return props.nodes.length > 1
      ? []
      : [{ key: 'first', label: __('Add Step') }]
  if (data.step.step_type !== 'If') return [{ key: 'next', label: __('Step') }]
  return [
    { key: 'if', label: __('If'), branch: 'If' },
    { key: 'else', label: __('Else'), branch: 'Else' },
    { key: 'next', label: __('After') },
  ]
}
</script>

<style>
.workflow-flow {
  height: 100%;
  width: 100%;
}

.workflow-flow .vue-flow__pane {
  cursor: grab;
}

.workflow-node {
  position: relative;
  display: flex;
  min-width: 230px;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--outline-gray-2);
  border-radius: 8px;
  background: var(--surface-gray-1);
  padding: 10px 12px;
  box-shadow: 0 1px 2px rgb(0 0 0 / 8%);
}

.workflow-node-selected {
  border-color: var(--surface-blue-7);
  box-shadow: 0 0 0 1px var(--surface-blue-8);
  background: var(--surface-blue-1);
}

.workflow-node-error {
  border-color: var(--surface-red-6);
}

.workflow-node-actions {
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  z-index: 2;
  display: none;
  gap: 6px;
  transform: translateX(-50%);
}

.workflow-node:hover .workflow-node-actions,
.workflow-node:focus-within .workflow-node-actions {
  display: flex;
}
</style>
