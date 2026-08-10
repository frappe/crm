<template>
  <VueFlow
    :id="flowId"
    :nodes="flowNodes"
    :edges="edges"
    class="workflow-flow"
    :fit-view-on-init="true"
    :fit-view-options="fitViewOptions"
    :nodes-draggable="!readonly"
    :nodes-connectable="false"
    :elements-selectable="!readonly"
    :pan-on-drag="true"
    @nodes-initialized="refitFlow"
    @node-drag-stop="rememberPosition"
    @node-click="selectNode($event.node.id)"
    @pane-click="selectNode('trigger')"
  >
    <Background pattern-color="#7e7e7e" :gap="24" :size="1.5" />
    <Panel position="bottom-center">
      <div class="workflow-controls">
        <button
          class="workflow-control"
          :title="__('Zoom out')"
          :aria-label="__('Zoom out')"
          @click="zoomOut({ duration: 150 })"
        >
          <ZoomOutIcon class="size-4" />
        </button>
        <span class="workflow-zoom">{{ zoomPercent }}</span>
        <button
          class="workflow-control"
          :title="__('Zoom in')"
          :aria-label="__('Zoom in')"
          @click="zoomIn({ duration: 150 })"
        >
          <PlusIcon class="size-4" />
        </button>
        <span class="workflow-controls-divider" />
        <button
          class="workflow-control"
          :title="__('Fit entire flow')"
          :aria-label="__('Fit entire flow')"
          @click="refitFlow"
        >
          <FitIcon class="size-4" />
        </button>
      </div>
    </Panel>
    <template #node-automation="{ id, data }">
      <div class="workflow-node-shell">
        <div
          class="workflow-kicker"
          :class="{ 'workflow-kicker-on': isOn(id) }"
        >
          {{ data.kicker }}
        </div>
        <div class="flex items-center">
          <component
            :is="picksTrigger(data) ? PickerMenu : 'div'"
            v-bind="picksTrigger(data) ? triggerMenu : {}"
            @select="$emit('pick-trigger', $event.value)"
          >
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
              <Handle
                v-if="!data.isTrigger"
                type="target"
                :position="Position.Top"
              />
              <div class="workflow-node-icon">
                <component
                  :is="data.icon"
                  class="size-[18px] text-ink-gray-6"
                />
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-base-medium text-ink-gray-8">
                  {{ data.label }}
                </div>
                <div
                  v-if="data.detail"
                  class="truncate text-p-sm text-ink-gray-5"
                >
                  {{ data.detail }}
                </div>
              </div>
              <ErrorIcon
                v-if="data.error"
                class="size-4 shrink-0 text-ink-red-4"
              />
              <Handle type="source" :position="Position.Bottom" />
            </div>
          </component>
          <div v-if="showAdd(data)" class="workflow-add nodrag">
            <span class="workflow-add-stem" />
            <PickerMenu
              :groups="blockGroups"
              :placeholder="__('Search blocks')"
              side="right"
              @select="addBlock(data, null, $event)"
            >
              <button class="workflow-add-button" :aria-label="__('Add block')">
                <PlusIcon class="size-4" />
              </button>
            </PickerMenu>
          </div>
        </div>
        <div v-if="data.arms && !readonly" class="workflow-arms nodrag">
          <PickerMenu
            v-for="arm in ['If', 'Else']"
            :key="arm"
            :groups="blockGroups"
            :placeholder="__('Search blocks')"
            @select="addBlock(data, arm, $event)"
          >
            <button class="workflow-arm">
              <PlusIcon class="size-3" />
              {{ data.arms[arm] }}
            </button>
          </PickerMenu>
        </div>
      </div>
    </template>
  </VueFlow>
</template>

<script setup>
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import PickerMenu from './WorkflowPickerMenu.vue'
import { Handle, Panel, Position, VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import ErrorIcon from '~icons/lucide/circle-alert'
import FitIcon from '~icons/lucide/maximize'
import PlusIcon from '~icons/lucide/plus'
import ZoomOutIcon from '~icons/lucide/minus'
import { computed, nextTick, ref, useId, watch } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  blockGroups: { type: Array, default: () => [] },
  triggerGroups: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'add-step', 'pick-trigger'])
const flowId = useId()
// Never zoom past 1:1 - a short flow should read at full size, not fill the pane.
const fitViewOptions = {
  padding: 0.25,
  minZoom: 0.3,
  maxZoom: 1,
  duration: 200,
}
const { fitView, viewport, zoomIn, zoomOut } = useVueFlow(flowId)

// Positions a user dragged a node to, so the computed layout stops overriding them.
const moved = ref({})

const flowNodes = computed(() =>
  props.nodes.map((node) => ({
    ...node,
    position: moved.value[node.id] || node.position,
  })),
)

const zoomPercent = computed(() => `${Math.round(viewport.value.zoom * 100)}%`)

watch(() => props.nodes.map((node) => node.id).join('|'), refitFlow, {
  flush: 'post',
})

async function refitFlow() {
  await nextTick()
  await fitView(fitViewOptions)
}

function rememberPosition({ node }) {
  moved.value = { ...moved.value, [node.id]: { ...node.position } }
}

function selectNode(id) {
  if (!props.readonly) emit('select', id)
}

/** Until a trigger is chosen the start block is the picker itself, as in the empty state. */
function picksTrigger(data) {
  return Boolean(data.empty) && !props.readonly
}

const triggerMenu = computed(() => ({
  groups: props.triggerGroups,
  placeholder: __('Search triggers'),
  hint: true,
}))

function isOn(id) {
  return !props.readonly && props.selectedId === id
}

function nodeClasses(id, data) {
  return {
    'workflow-node-selected': isOn(id),
    'workflow-node-error': Boolean(data.error),
    'workflow-node-empty': Boolean(data.empty),
    // Dragging swallows the click that opens the picker, and a lone start block
    // has nothing to arrange itself around anyway.
    nodrag: picksTrigger(data),
  }
}

/** A branching node grows through its arms, so it gets no "after" button of its own. */
function showAdd(data) {
  if (props.readonly || data.arms) return false
  return !data.isTrigger || props.nodes.length === 1
}

function addBlock(data, branch, block) {
  emit('add-step', { after: data.step || null, branch, values: block.values })
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

.workflow-flow .vue-flow__pane:active {
  cursor: grabbing;
}

.workflow-flow .vue-flow__node {
  cursor: grab;
}

.workflow-flow .vue-flow__node.dragging {
  cursor: grabbing;
}

.workflow-controls {
  display: flex;
  align-items: center;
  gap: 2px;
  border: 1px solid var(--outline-gray-2);
  border-radius: 10px;
  background: var(--surface-modal);
  padding: 4px;
  box-shadow: 0 4px 16px rgb(0 0 0 / 12%);
}

.workflow-control {
  display: flex;
  height: 28px;
  width: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--ink-gray-7);
}

.workflow-control:hover {
  background: var(--surface-gray-2);
}

.workflow-zoom {
  min-width: 44px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-gray-7);
  font-variant-numeric: tabular-nums;
}

.workflow-controls-divider {
  margin: 0 2px;
  height: 16px;
  width: 1px;
  background: var(--outline-gray-2);
}

.workflow-node-shell {
  position: relative;
}

/* The kicker rides above the card as a pill, so the card itself stays a clean two-line block. */
.workflow-kicker {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  border-radius: 5px;
  background: var(--surface-gray-2);
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 500;
  color: var(--ink-gray-6);
}

.workflow-kicker-on {
  background: var(--surface-blue-2);
  color: var(--ink-blue-3);
}

.workflow-node {
  position: relative;
  display: flex;
  width: 260px;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--outline-gray-2);
  border-radius: 10px;
  background: var(--surface-modal);
  padding: 10px 12px;
  box-shadow: 0 1px 2px rgb(0 0 0 / 6%);
}

.workflow-node:hover {
  border-color: var(--outline-gray-3);
}

.workflow-node-icon {
  display: flex;
  height: 32px;
  width: 32px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  background: var(--surface-gray-2);
}

.workflow-node-selected {
  border-color: var(--outline-blue-2);
  box-shadow: 0 0 0 1px var(--outline-blue-2);
  background: var(--surface-blue-1);
}

.workflow-node-error {
  border-color: var(--surface-red-6);
}

.workflow-node-empty {
  border-style: dashed;
  background: transparent;
  box-shadow: none;
}

.workflow-add {
  display: flex;
  align-items: center;
}

.workflow-add-stem {
  height: 1px;
  width: 20px;
  background: var(--outline-gray-3);
}

.workflow-add-button {
  display: flex;
  height: 24px;
  width: 24px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--outline-gray-2);
  border-radius: 6px;
  background: var(--surface-modal);
  color: var(--ink-gray-7);
  box-shadow: 0 1px 2px rgb(0 0 0 / 6%);
}

.workflow-add-button:hover {
  background: var(--surface-gray-2);
}

.workflow-arms {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  z-index: 2;
  display: flex;
  gap: 6px;
  transform: translateX(-50%);
}

.workflow-arm {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--outline-gray-2);
  border-radius: 6px;
  background: var(--surface-modal);
  padding: 3px 8px;
  font-size: 11px;
  color: var(--ink-gray-7);
  white-space: nowrap;
  box-shadow: 0 1px 2px rgb(0 0 0 / 6%);
}

.workflow-arm:hover {
  background: var(--surface-gray-2);
}
</style>
