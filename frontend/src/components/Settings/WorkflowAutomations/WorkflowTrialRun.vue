<template>
  <div class="mx-auto flex h-full min-h-0 max-w-3xl flex-col gap-4">
    <div class="flex items-end gap-2">
      <div class="min-w-0 flex-1 space-y-1.5">
        <Link
          v-if="doc.document_type"
          :model-value="docname"
          :doctype="doc.document_type"
          :label="__('Run against')"
          :placeholder="__('Pick a {0}', [doc.document_type])"
          @update:model-value="pickDocument"
        />
        <p class="text-xs text-ink-gray-5">
          {{
            __(
              'The flow runs for real against this record, then everything it did is undone. Nothing is saved, sent or scheduled.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="playing"
        :label="__('Skip')"
        variant="subtle"
        @click="finishPlayback"
      />
      <Button
        :label="__('Start test run')"
        variant="solid"
        icon-left="play"
        :loading="running"
        :disabled="doc.document_type && !docname"
        @click="run()"
      />
    </div>

    <div v-if="error" class="text-sm text-ink-red-5" role="alert">
      {{ error }}
    </div>

    <div
      v-if="summary"
      class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
    >
      <Badge
        :label="__(playing ? 'Running' : summary.status)"
        :theme="playing ? 'blue' : STATUS_THEMES[summary.status] || 'gray'"
        variant="subtle"
      />
      <span
        v-if="summary.error_summary"
        class="truncate text-sm text-ink-red-5"
      >
        {{ summary.error_summary }}
      </span>
      <span v-else class="text-sm text-ink-gray-6">
        {{ __('{0} of {1} steps ran', [ranCount, stepCount]) }}
      </span>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto pb-4">
      <div
        v-if="!doc.actions?.length"
        class="py-10 text-center text-sm text-ink-gray-5"
      >
        {{ __('This flow has no steps to run.') }}
      </div>
      <div v-else class="space-y-3">
        <div class="flex items-start gap-2">
          <div class="flex w-5 shrink-0 justify-center pt-2.5">
            <span class="mt-1.5 size-1.5 rounded-full bg-surface-gray-4" />
          </div>
          <div
            class="min-w-0 flex-1 rounded-[10px] border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
          >
            <div class="flex items-center gap-2">
              <div
                class="flex size-[26px] shrink-0 items-center justify-center rounded-[6px] border border-outline-gray-2"
              >
                <component :is="trigger.icon" class="size-4 text-ink-gray-7" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-base-medium text-ink-gray-8">
                  {{ trigger.label }}
                </div>
                <div class="truncate text-xs text-ink-gray-5">
                  {{ docname || doc.document_type || __('No document') }}
                </div>
              </div>
              <span class="shrink-0 text-xs text-ink-gray-5">
                {{ __('Trigger') }}
              </span>
            </div>
          </div>
        </div>

        <WorkflowTrialStep
          v-for="step in doc.actions"
          :key="step._id"
          :node="step"
          :outcomes="outcomes"
          :active-key="activeKey"
          :taken="taken"
          :overrides="overrides"
          :row-idx="rowIdx"
          :playing="playing"
          :finished="finished"
          @run-branch="runBranch"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import TriggerIcon from '~icons/lucide/play'
import WorkflowTrialStep from './WorkflowTrialStep.vue'
import { toRows } from './workflowSteps'
import { triggerDefinition } from './workflowTriggers'
import { Badge, Button, call } from 'frappe-ui'
import { computed, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  automationName: { type: String, default: '' },
  doc: { type: Object, required: true },
})

const STATUS_THEMES = {
  Success: 'green',
  Skipped: 'gray',
  Waiting: 'blue',
  Failed: 'red',
  'Partially Failed': 'orange',
}

// A wait is reported instantly by the server; the pause is here so the run reads as a sequence.
const WAIT_HOLD = 5000
const MIN_HOLD = 400
const MAX_HOLD = 1500

const docname = ref('')
const running = ref(false)
const playing = ref(false)
const error = ref('')
const summary = ref(null)
const activeKey = ref('')
const outcomes = reactive({})
const taken = reactive({})
const overrides = reactive({})

let result = null
let playToken = 0

onUnmounted(() => (playToken += 1))

const trigger = computed(() => {
  const definition = triggerDefinition(props.doc)
  return {
    icon: definition?.icon || TriggerIcon,
    label: definition?.label || __('Manual run'),
  }
})

/** Trace entries are keyed by step key; branch arms by the row index of their `If`. */
const rowIdx = computed(() => {
  const map = {}
  toRows(props.doc.actions || []).forEach(
    (row) => (map[row.step_key] = row.idx),
  )
  return map
})

/** Counted over the blocks on screen, not the rows behind them - a wait is one of each. */
const stepCount = computed(() => countNodes(props.doc.actions || []))

const ranCount = computed(
  () => Object.keys(outcomes).filter((key) => nodeFor(key)).length,
)

function countNodes(nodes) {
  return nodes.reduce(
    (total, node) =>
      total +
      1 +
      countNodes(node.children?.If || []) +
      countNodes(node.children?.Else || []),
    0,
  )
}

const finished = computed(() => Boolean(summary.value) && !playing.value)

function pickDocument(value) {
  docname.value = value
  reset()
}

function reset() {
  playToken += 1
  playing.value = false
  activeKey.value = ''
  summary.value = null
  result = null
  Object.keys(outcomes).forEach((key) => delete outcomes[key])
  Object.keys(taken).forEach((key) => delete taken[key])
}

function runBranch({ idx, arm }) {
  overrides[String(idx)] = arm
  run({ keepOverrides: true })
}

async function run({ keepOverrides = false } = {}) {
  reset()
  if (!keepOverrides) clearOverrides()
  running.value = true
  error.value = ''
  try {
    result = await call('frappe.automation_engine.api.trial_run', {
      automation: props.automationName,
      docname: docname.value || null,
      branch_overrides: { ...overrides },
    })
    await playback(result)
  } catch (e) {
    error.value = plainText(e.messages?.join('\n') || e.message)
  } finally {
    running.value = false
  }
}

/** Server messages carry markup - a doc link on the server-scripts error, say. */
function plainText(message) {
  const holder = document.createElement('div')
  holder.innerHTML = String(message || '')
  return holder.textContent.trim()
}

function clearOverrides() {
  Object.keys(overrides).forEach((key) => delete overrides[key])
}

/** Reveal the trace a step at a time, holding each block for as long as it took to run. */
async function playback(run) {
  const token = ++playToken
  summary.value = run
  playing.value = true
  for (const entry of run.steps || []) {
    const node = nodeFor(entry.step_key)
    if (node) {
      activeKey.value = entry.step_key
      await hold(holdFor(entry, node))
      if (token !== playToken) return
    }
    reveal(entry, run)
  }
  activeKey.value = ''
  playing.value = false
}

/** Jump to the end: the trace is already in hand, so nothing is lost by not watching it. */
function finishPlayback() {
  playToken += 1
  ;(result?.steps || []).forEach((entry) => reveal(entry, result))
  activeKey.value = ''
  playing.value = false
}

function reveal(entry, run) {
  outcomes[entry.step_key] = entry
  const branch = run.branches?.[String(entry.step_idx + 1)]
  if (branch) taken[String(entry.step_idx + 1)] = branch
}

function holdFor(entry, node) {
  if (node.step_type === 'Wait' || node.step_type === 'WaitForEvent')
    return WAIT_HOLD
  return Math.min(Math.max(entry.duration_ms || 0, MIN_HOLD), MAX_HOLD)
}

function hold(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function nodeFor(key, nodes = props.doc.actions || []) {
  for (const node of nodes) {
    if (node.step_key === key) return node
    const child =
      nodeFor(key, node.children?.If || []) ||
      nodeFor(key, node.children?.Else || [])
    if (child) return child
  }
  return null
}
</script>
