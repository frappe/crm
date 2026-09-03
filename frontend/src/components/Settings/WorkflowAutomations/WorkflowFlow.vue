<template>
  <VueFlow
    :id="flowId"
    ref="flowRoot"
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
    <Background color="var(--surface-gray-4)" :gap="40" :size="5" />
    <Panel position="bottom-left">
      <div
        class="flex items-center gap-0.5 rounded-[10px] border border-outline-gray-2 bg-surface-gray-1 p-1 shadow-md"
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
        <div class="flex items-center">
          <div class="relative w-[212px] shrink-0">
            <Handle
              v-if="!data.isTrigger"
              id="input"
              class="workflow-port"
              type="target"
              :position="Position.Left"
            />
            <Combobox
              :options="triggerGroups"
              :disabled="!picksTrigger(data)"
              trigger="button"
              :placeholder="__('Search triggers')"
              @update:model-value="$emit('pick-trigger', $event)"
            >
              <template #item-prefix />
              <template #item-label="{ item }">
                <WorkflowComboboxOption :item="item" />
              </template>
              <template #trigger>
                <div
                  class="workflow-node relative flex h-[87px] w-[212px] flex-col overflow-hidden rounded-[10px] border bg-surface-base shadow-sm transition-all"
                  :class="[
                    nodeClasses(id, data),
                    { 'opacity-40': data.dimmed },
                  ]"
                  :tabindex="readonly ? -1 : 0"
                  :role="readonly ? undefined : 'button'"
                  :aria-label="`${data.kicker}: ${data.label}`"
                  @click.stop="selectNode(id)"
                  @keydown.enter="selectNode(id)"
                  @keydown.space.prevent="selectNode(id)"
                >
                  <div
                    class="flex h-[47px] shrink-0 items-center gap-1.5 border-b border-outline-gray-3 px-2"
                  >
                    <div
                      v-if="!data.empty"
                      class="flex size-[30px] shrink-0 items-center justify-center rounded-[6px] border"
                      :class="iconChipClasses(data)"
                    >
                      <component
                        :is="data.icon"
                        class="workflow-node-icon size-5"
                        :class="iconClasses(data)"
                      />
                    </div>
                    <div
                      class="min-w-0 flex-1 truncate text-[11px] font-medium leading-[13px] text-ink-gray-9"
                      :class="{ 'text-center': data.empty }"
                    >
                      {{ data.label }}
                    </div>
                    <Badge
                      v-if="data.forced"
                      :label="__('Forced')"
                      theme="orange"
                      variant="subtle"
                    />
                    <Spinner
                      v-if="data.status === 'running'"
                      size="sm"
                      class="shrink-0 text-ink-gray-7"
                    />
                    <component
                      :is="RUN_ICONS[data.status]"
                      v-else-if="RUN_ICONS[data.status]"
                      class="size-4 shrink-0"
                      :class="RUN_COLORS[data.status]"
                    />
                    <ErrorIcon
                      v-else-if="data.error"
                      class="size-4 shrink-0 text-ink-red-4"
                    />
                  </div>
                  <div
                    class="flex min-h-0 flex-1 items-end gap-2 px-2 py-[7px]"
                  >
                    <div
                      class="line-clamp-2 min-w-0 flex-1 text-[10px] leading-3 text-ink-gray-7"
                    >
                      <template v-if="data.detail">
                        {{ data.detail }}
                      </template>
                    </div>
                    <div
                      class="shrink-0 text-[10px] font-medium leading-3 text-ink-gray-8"
                    >
                      {{ data.kicker }}
                    </div>
                  </div>
                </div>
              </template>
            </Combobox>
            <Handle
              v-if="hasOutgoing(id)"
              id="output"
              class="workflow-port"
              type="source"
              :position="Position.Right"
            />
          </div>
          <div
            v-if="showAdd(data)"
            class="workflow-add-control nodrag flex items-center"
            @click.stop
          >
            <span class="h-px w-5 bg-outline-gray-3" />
            <Combobox
              :options="blockGroups"
              trigger="button"
              side="right"
              :placeholder="__('Search blocks')"
              @update:model-value="addBlock(data, null, $event)"
            >
              <template #item-prefix />
              <template #item-label="{ item }">
                <WorkflowComboboxOption :item="item" />
              </template>
              <template #trigger>
                <Button
                  icon="lucide-plus"
                  variant="ghost"
                  :aria-label="__('Add block')"
                />
              </template>
            </Combobox>
          </div>
        </div>
        <div
          v-if="data.retryArms?.length"
          class="workflow-add-control nodrag absolute left-0 top-[calc(100%+8px)] flex gap-1.5"
          @click.stop
        >
          <Button
            v-for="arm in data.retryArms"
            :key="arm.branch"
            size="sm"
            icon-left="lucide-play"
            @click="$emit('run-branch', arm)"
          >
            {{ __('Run {0}', [arm.label]) }}
          </Button>
        </div>
        <div
          v-if="(data.arms?.length || data.canContinue) && !readonly"
          class="workflow-add-control nodrag absolute left-[calc(100%+12px)] top-1/2 flex -translate-y-1/2 flex-col gap-1.5"
          @click.stop
        >
          <Combobox
            v-for="arm in data.arms"
            :key="arm.branch"
            :options="blockGroups"
            trigger="button"
            side="right"
            :placeholder="__('Search blocks')"
            @update:model-value="addBlock(data, arm.branch, $event)"
          >
            <template #item-prefix />
            <template #item-label="{ item }">
              <WorkflowComboboxOption :item="item" />
            </template>
            <template #trigger>
              <Button icon-left="lucide-plus" size="sm">
                {{ arm.label }}
              </Button>
            </template>
          </Combobox>
          <Combobox
            v-if="data.canContinue"
            :options="blockGroups"
            trigger="button"
            side="right"
            :placeholder="__('Search blocks')"
            @update:model-value="addBlock(data, null, $event)"
          >
            <template #item-prefix />
            <template #item-label="{ item }">
              <WorkflowComboboxOption :item="item" />
            </template>
            <template #trigger>
              <Button icon-left="lucide-plus" size="sm" class="ml-6">
                {{ __('After branches') }}
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
import { Background } from '@vue-flow/background'
import { Handle, Panel, Position, VueFlow, useVueFlow } from '@vue-flow/core'
import ErrorIcon from '~icons/lucide/circle-alert'
import FailedIcon from '~icons/lucide/circle-x'
import SkippedIcon from '~icons/lucide/circle-minus'
import SuccessIcon from '~icons/lucide/circle-check'
import WaitingIcon from '~icons/lucide/clock'
import WorkflowComboboxOption from './WorkflowComboboxOption.vue'
import { Badge, Button, Combobox, Spinner } from 'frappe-ui'
import { computed, nextTick, ref, useId, watch } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  blockGroups: { type: Array, default: () => [] },
  triggerGroups: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  inspectorOpen: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'add-step', 'pick-trigger', 'run-branch'])

// How a trial run's outcome reads on the node it belongs to.
const RUN_ICONS = {
  Success: SuccessIcon,
  Skipped: SkippedIcon,
  Failed: FailedIcon,
  Waiting: WaitingIcon,
}

const RUN_COLORS = {
  Success: 'text-ink-green-5',
  Skipped: 'text-ink-gray-4',
  Failed: 'text-ink-red-5',
  Waiting: 'text-ink-amber-6',
}
const flowId = useId()
const flowRoot = ref(null)
const EDGE_PADDING = 48

// Fit as tight as the flow allows: a short flow can pass 100%, a long one caps there.
const fitViewOptions = computed(() => ({
  padding: 0.08,
  minZoom: 0.3,
  maxZoom: props.nodes.length <= 3 ? 1.25 : 1,
  duration: 200,
}))
const { fitView, setViewport, viewport, zoomIn, zoomOut } = useVueFlow(flowId)

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

watch(
  [
    () => props.nodes.map((node) => node.id).join('|'),
    () => props.nodes[0]?.data?.empty,
  ],
  refitFlow,
  { flush: 'post' },
)

watch(() => props.inspectorOpen, refitAfterPanelResize, { flush: 'post' })

async function refitAfterPanelResize() {
  await nextTick()
  await nextFrame()
  await nextFrame()
  return refitFlow()
}

async function refitFlow() {
  await nextTick()
  await nextFrame()
  await fitView({ ...fitViewOptions.value, duration: 0 })
  if (props.nodes[0]?.data?.empty) return centerEmptyFlow()
  await alignFlowLeft()
  await nextFrame()
  await keepAddControlsVisible()
}

function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(resolve))
}

// Refitting reads back the result a frame later, so it settles instantly.
function alignFlowLeft(zoom = viewport.value.zoom) {
  const leftmost = Math.min(...flowNodes.value.map((node) => node.position.x))
  return setViewport(
    { ...viewport.value, zoom, x: EDGE_PADDING - leftmost * zoom },
    { duration: 0 },
  )
}

/** fitView only measures node bounds, so the add controls hanging off the last
 *  node still overflow. Scale down to bring them back rather than panning away
 *  from the left edge. */
function keepAddControlsVisible() {
  const root = flowRoot.value?.$el || flowRoot.value
  const canvas = root?.getBoundingClientRect()
  const controls = root?.querySelectorAll('.workflow-add-control') || []
  if (!canvas || !controls.length) return
  const right = Math.max(
    ...[...controls].map((item) => item.getBoundingClientRect().right),
  )
  const used = right - canvas.left - EDGE_PADDING
  const available = canvas.width - EDGE_PADDING * 2
  if (used <= available || used <= 0) return
  // Controls sit inside the zoomed pane, so widths scale with the zoom exactly.
  const zoom = Math.max(
    viewport.value.zoom * (available / used),
    fitViewOptions.value.minZoom,
  )
  return alignFlowLeft(zoom)
}

function centerEmptyFlow() {
  const root = flowRoot.value?.$el || flowRoot.value
  const canvas = root?.getBoundingClientRect()
  const node = root?.querySelector('.vue-flow__node')?.getBoundingClientRect()
  if (!canvas || !node) return
  const offset = canvas.left + canvas.width / 2 - node.left - node.width / 2
  return setViewport(
    { ...viewport.value, x: viewport.value.x + offset },
    { duration: fitViewOptions.value.duration },
  )
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
  if (data.empty) return 'border-dashed border-[#aeaeae]  shadow-none'
  if (data.status === 'Failed') return 'border-outline-red-2 bg-surface-modal'
  if (data.status === 'running') return 'border-outline-gray-5 shadow-md'
  if (data.error) return 'border-outline-red-2 bg-surface-modal'
  if (isOn(id)) return 'border-outline-gray-5'
  return 'border-outline-gray-2    hover:border-outline-gray-5'
}

function iconChipClasses(data) {
  return iconTone(data).chip
}

function iconClasses(data) {
  return iconTone(data).icon
}

function iconTone(data) {
  if (data.isTrigger) return ICON_TONES.trigger
  return ICON_TONES[data.step?.step_type] || ICON_TONES.Action
}

/**
 * Only the end of a chain offers an add button. Branching nodes use their dedicated arm and
 * shared-continuation controls instead.
 */
function showAdd(data) {
  if (props.readonly || data.branching || data.empty) return false
  return data.isTrigger ? props.nodes.length === 1 : data.last
}

function hasOutgoing(id) {
  return props.edges.some((edge) => edge.source === id)
}

function addBlock(data, branch, value) {
  const block = blocksByValue.value.get(value)
  if (!block) return
  emit('add-step', { after: data.step || null, branch, values: block.values })
}

const ICON_TONES = {
  trigger: {
    chip: 'bg-surface-blue-3 border-outline-blue-7',
    icon: 'text-ink-blue-7',
  },
  Action: {
    chip: 'bg-surface-violet-3 border-outline-violet-7',
    icon: 'text-ink-violet-7',
  },
  Wait: {
    chip: 'bg-surface-amber-3 border-outline-amber-7',
    icon: 'text-ink-amber-7',
  },
  WaitForEvent: {
    chip: 'bg-surface-amber-3 border-outline-amber-7',
    icon: 'text-ink-amber-7',
  },
  If: {
    chip: 'bg-surface-green-3 border-outline-green-7',
    icon: 'text-ink-green-7',
  },
}
</script>

<style>
.workflow-flow {
  height: 100%;
  width: 100%;
  background: var(--surface-base);
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

.workflow-flow .workflow-port {
  z-index: 20 !important;
  width: 6px !important;
  min-width: 6px !important;
  height: 6px !important;
  min-height: 6px !important;
  border: 0 !important;
  background: #4e4e4e !important;
  box-shadow: none;
  opacity: 1 !important;
  visibility: visible !important;
}

.workflow-flow .workflow-node-icon {
  stroke-width: 2;
}

.workflow-flow .vue-flow__edge-path {
  stroke: #4e4e4e;
  stroke-width: 1;
}

.workflow-flow .vue-flow__edge-textbg {
  fill: #fff;
  stroke: #aeaeae;
  stroke-width: 1px;
}

.workflow-flow .vue-flow__edge-text {
  fill: #4e4e4e;
  font-size: 10px;
  font-weight: 500;
}
</style>
