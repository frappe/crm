<template>
  <div class="flex h-full min-h-0 flex-col bg-surface-elevation-2">
    <div
      class="flex h-14 shrink-0 items-center justify-between border-b border-outline-gray-2 px-4"
    >
      <div class="flex min-w-0 items-center gap-2">
        <FormControl
          :model-value="doc.title"
          :aria-label="__('Automation title')"
          :placeholder="__('Untitled automation')"
          class="w-[min(28rem,50vw)] min-w-0"
          @focus="$event.target.select()"
          @update:model-value="setTitle"
        />
        <Badge
          v-if="!doc.enabled"
          :label="__('Draft')"
          theme="orange"
          variant="subtle"
        />
        <Badge
          v-if="dirty"
          :label="__('Unsaved')"
          theme="gray"
          variant="subtle"
        />
      </div>
      <div class="flex items-center gap-2">
        <Button
          :label="__('See Runs')"
          icon-left="lucide-history"
          :disabled="!automationName"
          @click="showRuns = true"
        />
        <Button
          :label="__('Save')"
          variant="solid"
          :loading="saving"
          @click="saveAutomation"
        />
        <Button
          icon="lucide-x"
          variant="ghost"
          :aria-label="__('Close')"
          @click="$emit('close')"
        />
      </div>
    </div>
    <div
      ref="panes"
      class="grid min-h-0 flex-1"
      :style="{ gridTemplateColumns: `1fr 6px ${inspectorWidth}px` }"
    >
      <div class="relative min-h-0">
        <WorkflowFlow
          :nodes="nodes"
          :edges="edges"
          :selected-id="selectedId"
          @select="selectedId = $event"
          @add-step="addStep"
        />
        <Button
          v-if="!doc.actions.length"
          class="absolute bottom-4 left-1/2 -translate-x-1/2"
          icon-left="lucide-plus"
          :label="__('Add Step')"
          @click="addStep(null)"
        />
      </div>
      <div
        class="cursor-col-resize bg-surface-gray-2 transition-colors hover:bg-surface-gray-4"
        role="separator"
        aria-orientation="vertical"
        :aria-label="__('Resize panel')"
        tabindex="0"
        @mousedown.prevent="startResize"
        @keydown.left.prevent="nudgeResize(24)"
        @keydown.right.prevent="nudgeResize(-24)"
      />
      <div
        class="min-h-0 border-l border-outline-gray-2 bg-surface-elevation-1"
      >
        <AutomationInspector
          :doc="doc"
          :selected-step="selectedStep"
          :targets="targetsFor(selectedStep)"
          :errors="errors[selectedId] || []"
          :loading="loading"
          @remove-step="removeSelectedStep"
        />
      </div>
    </div>
    <Dialog v-model:open="showRuns" :title="__('Automation Runs')">
      <template #default>
        <AutomationRuns :automation-name="automationName" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import AutomationInspector from './WorkflowAutomationInspector.vue'
import AutomationRuns from './WorkflowAutomationRuns.vue'
import WorkflowFlow from './WorkflowFlow.vue'
import { aliasTargets, loadCapabilities } from './workflowCapabilities'
import { workflowEdges, workflowNodes } from './workflowGraph'
import {
  insertAfter,
  layoutSteps,
  newStep,
  removeStep,
  stepsBefore,
  toRows,
  toTree,
} from './workflowSteps'
import { Badge, Button, Dialog, FormControl, call, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  automationName: { type: String, default: '' },
})

const emit = defineEmits(['close', 'saved', 'update:dirty'])

const INSPECTOR_WIDTH_KEY = 'crm:automation-inspector-width'
const MIN_INSPECTOR_WIDTH = 280
const MAX_INSPECTOR_WIDTH = 720

const loading = ref(false)
const saving = ref(false)
const inspectorWidth = ref(storedInspectorWidth())
const panes = ref(null)
const showRuns = ref(false)
const selectedId = ref('trigger')
const errors = reactive({})
const doc = reactive(defaultDoc())
const savedSnapshot = ref('')

const placed = computed(() => layoutSteps(doc.actions))

const selectedStep = computed(() => {
  return (
    placed.value.find((item) => item.node._id === selectedId.value)?.node ||
    null
  )
})

const nodes = computed(() => workflowNodes(doc, errors))
const edges = computed(() => workflowEdges(doc.actions))

const relationships = computed(() => parseJson(doc.relationships, []))

/** Compared against the last loaded/saved state so closing can warn about unsaved edits. */
const dirty = computed(() => savedSnapshot.value !== JSON.stringify(payload()))

watch(() => doc.document_type, loadTargetCapabilities, { immediate: true })
watch(relationships, loadTargetCapabilities, { deep: true })
watch(dirty, (value) => emit('update:dirty', value), { immediate: true })

loadAutomation()

function storedInspectorWidth() {
  return clampWidth(Number(localStorage.getItem(INSPECTOR_WIDTH_KEY)) || 340)
}

function clampWidth(width) {
  return Math.min(Math.max(width, MIN_INSPECTOR_WIDTH), MAX_INSPECTOR_WIDTH)
}

function setInspectorWidth(width) {
  inspectorWidth.value = clampWidth(width)
  localStorage.setItem(INSPECTOR_WIDTH_KEY, String(inspectorWidth.value))
}

function nudgeResize(step) {
  setInspectorWidth(inspectorWidth.value + step)
}

/** Measured from the panes' own right edge — the builder is inset inside a dialog. */
function startResize() {
  const right = panes.value.getBoundingClientRect().right
  const onMove = (event) => setInspectorWidth(right - event.clientX)
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    document.body.style.userSelect = ''
  }
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function defaultDoc() {
  return {
    doctype: 'Automation Flow',
    title: '',
    document_type: 'CRM Lead',
    enabled: 0,
    log_only: 0,
    trigger_type: 'Doc Created',
    trigger_field: '',
    from_value: '',
    to_value: '',
    custom_event: '',
    date_field: '',
    date_offset: 0,
    date_direction: 'Before',
    cron_expression: '',
    filters: '',
    condition: '',
    relationships: '[]',
    run_as: 'Automation User',
    automation_user: '',
    revalidate_on_run: 0,
    actions: [],
    stop_on_error: 1,
    throttle_per_minute: 0,
  }
}

async function loadAutomation() {
  if (!props.automationName) return markClean()
  loading.value = true
  try {
    const saved = await call('frappe.client.get', {
      doctype: 'Automation Flow',
      name: props.automationName,
    })
    Object.assign(doc, saved, {
      actions: toTree((saved.actions || []).map(normalizeRow)),
    })
  } finally {
    loading.value = false
    markClean()
  }
}

function markClean() {
  savedSnapshot.value = JSON.stringify(payload())
}

function setTitle(title) {
  doc.title = title
}

function normalizeRow(row) {
  return {
    ...row,
    step_type: row.step_type || 'Action',
    params: stringify(row.params),
    related_condition: stringify(row.related_condition, ''),
  }
}

function stringify(value, fallback = '{}') {
  if (!value) return fallback
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2)
}

function parseJson(value, fallback) {
  if (!value) return fallback
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value)
  } catch {
    return fallback
  }
}

/** Load capabilities for the trigger DocType and every alias a step can target. */
function loadTargetCapabilities() {
  aliasTargets(
    doc.document_type,
    relationships.value,
    toRows(doc.actions),
  ).forEach((target) => loadCapabilities(target.doctype))
}

function targetsFor(step) {
  if (!step) return []
  return aliasTargets(
    doc.document_type,
    relationships.value,
    stepsBefore(doc.actions, step),
  )
}

function addStep(step, branch) {
  const created = newStep()
  if (!step) doc.actions.push(created)
  else if (branch) step.children[branch].push(created)
  else insertAfter(doc.actions, step, created)
  selectedId.value = created._id
}

function removeSelectedStep() {
  if (!selectedStep.value) return
  removeStep(doc.actions, selectedStep.value)
  selectedId.value = 'trigger'
}

async function saveAutomation() {
  saving.value = true
  clearErrors()
  try {
    const saved = props.automationName
      ? await call('frappe.client.save', { doc: payload() })
      : await call('frappe.client.insert', { doc: payload() })
    markClean()
    toast.success(__('Automation saved'))
    emit('saved', saved)
  } catch (error) {
    attachError(error)
    throw error
  } finally {
    saving.value = false
  }
}

function payload() {
  return {
    ...doc,
    title: doc.title || __('Untitled automation'),
    relationships: JSON.stringify(relationships.value),
    actions: toRows(doc.actions).map(rowPayload),
  }
}

function rowPayload(row) {
  return {
    ...row,
    doctype: 'Automation Action',
    params: JSON.stringify(parseJson(row.params, {})),
    related_condition: row.related_condition
      ? JSON.stringify(parseJson(row.related_condition, {}))
      : '',
  }
}

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

/** Server errors read "Row 3: ..." — map that flattened row back onto its node. */
function attachError(error) {
  const message = String(error?.messages?.[0] || error?.message || error)
  const match = message.match(/Row (\d+)/)
  const node = match && placed.value[Number(match[1]) - 1]?.node
  if (!node) return
  errors[node._id] = [{ message }]
  selectedId.value = node._id
}
</script>
