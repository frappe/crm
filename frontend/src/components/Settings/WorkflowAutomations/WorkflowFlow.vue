<template>
  <VueFlow
    :id="flowId"
    :nodes="flowNodes"
    :edges="edges"
    class="workflow-flow"
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
      <div
        class="flex items-center gap-0.5 rounded-[10px] border border-outline-gray-2 bg-surface-modal p-1 shadow-lg"
      >
        <Button
          icon="lucide-minus"
          variant="ghost"
          :aria-label="__('Zoom out')"
          @click="zoomOut({ duration: 150 })"
        />
        <span
          class="min-w-11 text-center text-xs font-medium tabular-nums text-ink-gray-7"
        >
          {{ zoomPercent }}
        </span>
        <Button
          icon="lucide-plus"
          variant="ghost"
          :aria-label="__('Zoom in')"
          @click="zoomIn({ duration: 150 })"
        />
        <span class="mx-0.5 h-4 w-px bg-outline-gray-2" />
        <Button
          icon="lucide-maximize"
          variant="ghost"
          :aria-label="__('Fit entire flow')"
          @click="refitFlow"
        />
      </div>
    </Panel>
    <template #node-automation="{ id, data }">
      <div class="relative">
        <div
          class="absolute bottom-[calc(100%+4px)] left-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
          :class="
            isOn(id)
              ? 'bg-surface-blue-3 text-ink-white'
              : 'bg-surface-gray-4 text-ink-gray-8'
          "
        >
          {{ data.kicker }}
        </div>
        <div class="flex items-center">
          <Combobox
            :options="triggerGroups"
            :disabled="!picksTrigger(data)"
            trigger="button"
            :placeholder="__('Search triggers')"
            @update:model-value="$emit('pick-trigger', $event)"
          >
            <template #trigger>
              <div
                class="relative flex w-[260px] items-center gap-2.5 rounded-[10px] border px-3 py-2.5 shadow-sm transition-colors"
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
                  :position="Position.Left"
                />
                <div
                  v-if="!data.empty"
                  class="flex size-8 shrink-0 items-center justify-center rounded-[7px] bg-surface-gray-2"
                >
                  <component
                    :is="data.icon"
                    class="size-[18px] text-ink-gray-6"
                  />
                </div>
                <div
                  class="min-w-0 flex-1"
                  :class="{ 'text-center': data.empty }"
                >
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
                <Handle type="source" :position="Position.Right" />
              </div>
            </template>
          </Combobox>
          <div v-if="showAdd(data)" class="nodrag flex items-center">
            <span class="h-px w-5 bg-outline-gray-3" />
            <Combobox
              :options="blockGroups"
              trigger="button"
              side="right"
              :placeholder="__('Search blocks')"
              @update:model-value="addBlock(data, null, $event)"
            >
              <template #trigger>
                <Button icon="lucide-plus" :aria-label="__('Add block')" />
              </template>
            </Combobox>
          </div>
        </div>
        <div
          v-if="data.arms && !readonly"
          class="nodrag absolute left-[calc(100%+12px)] top-1/2 flex -translate-y-1/2 flex-col gap-1.5"
        >
          <Combobox
            v-for="arm in ['If', 'Else']"
            :key="arm"
            :options="blockGroups"
            trigger="button"
            side="right"
            :placeholder="__('Search blocks')"
            @update:model-value="addBlock(data, arm, $event)"
          >
            <template #trigger>
              <Button icon-left="lucide-plus" size="sm">
                {{ data.arms[arm] }}
              </Button>
            </template>
          </Combobox>
        </div>
      </div>
    </template>
  </VueFlow>
</template>

<script setup>
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { Handle, Panel, Position, VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import ErrorIcon from '~icons/lucide/circle-alert'
import { Button, Combobox } from 'frappe-ui'
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

/** The combobox hands back a value; the step it stands for lives on the option. */
const blocksByValue = computed(
  () =>
    new Map(
      props.blockGroups.flatMap((group) =>
        group.options.map((option) => [option.value, option]),
      ),
    ),
)

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

function isOn(id) {
  return !props.readonly && props.selectedId === id
}

/**
 * One exclusive surface per state - stacking conflicting border utilities would let
 * stylesheet order, not intent, decide which one wins.
 * `nodrag` because dragging swallows the click that opens the picker, and a lone start
 * block has nothing to arrange itself around anyway.
 */
function nodeClasses(id, data) {
  return [picksTrigger(data) ? 'nodrag' : '', nodeSurface(id, data)]
}

function nodeSurface(id, data) {
  if (data.empty) return 'border-dashed border-outline-gray-3 shadow-none'
  if (data.error) return 'border-outline-red-2 bg-surface-modal'
  if (isOn(id))
    return 'border-outline-blue-2 bg-surface-blue-1 ring-1 ring-outline-blue-2'
  return 'border-outline-gray-2 bg-surface-modal hover:border-outline-gray-3'
}

/** A branching node grows through its arms, so it gets no "after" button of its own. */
function showAdd(data) {
  if (props.readonly || data.arms) return false
  return !data.isTrigger || props.nodes.length === 1
}

function addBlock(data, branch, value) {
  const block = blocksByValue.value.get(value)
  if (!block) return
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
</style>
