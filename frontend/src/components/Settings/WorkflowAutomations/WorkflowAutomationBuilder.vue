<template>
  <div class="relative flex h-full min-h-0 flex-col bg-surface-elevation-2">
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
          :label="__('Test Run')"
          icon-left="lucide-flask-conical"
          :disabled="!automationName || dirty"
          :tooltip="dirty ? __('Save the flow before testing it') : ''"
          @click="showTrial = true"
        />
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
      :style="{ gridTemplateColumns: paneColumns }"
    >
      <div class="relative min-h-0">
        <WorkflowFlow
          :nodes="nodes"
          :edges="edges"
          :block-groups="blocks"
          :trigger-groups="triggers"
          :selected-id="selectedId"
          :inspector-open="inspectorOpen"
          @select="selectNode"
          @add-step="addStep"
          @pick-trigger="pickTrigger"
        />
        <Button
          v-if="doc.trigger_type"
          class="absolute right-3 top-3 z-10 shadow-sm"
          :icon="
            inspectorOpen
              ? 'lucide-panel-right-close'
              : 'lucide-panel-right-open'
          "
          variant="subtle"
          :aria-label="
            inspectorOpen ? __('Close inspector') : __('Open inspector')
          "
          @click="inspectorOpen = !inspectorOpen"
        />
      </div>
      <div
        v-if="inspectorOpen"
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
        v-if="inspectorOpen"
        class="min-h-0 border-l border-outline-gray-2 bg-surface-elevation-1"
      >
        <AutomationInspector
          :doc="doc"
          :selected-step="selectedStep"
          :targets="targetsFor(selectedStep)"
          :errors="errors[selectedId] || []"
          :loading="loading"
          @request-remove="confirmSelectedRemoval"
        />
      </div>
    </div>
    <div
      v-if="saveError"
      class="absolute bottom-4 left-1/2 z-10 max-w-lg -translate-x-1/2 rounded-lg border border-outline-red-2 bg-surface-red-1 px-3 py-2 text-sm text-ink-red-4 shadow-lg"
      role="alert"
    >
      {{ saveError }}
    </div>
    <Dialog v-model:open="showRuns" :title="__('Automation Runs')">
      <template #default>
        <AutomationRuns :automation-name="automationName" />
      </template>
    </Dialog>
    <Dialog v-model:open="showTrial" :title="__('Test Run')">
      <template #default>
        <AutomationTrialRun
          :automation-name="automationName"
          :doctype="doc.document_type"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import AutomationInspector from './WorkflowAutomationInspector.vue'
import AutomationRuns from './WorkflowAutomationRuns.vue'
import AutomationTrialRun from './WorkflowTrialRun.vue'
import WorkflowFlow from './WorkflowFlow.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { globalStore } from '@/stores/global'
import { blockGroups } from './workflowBlocks'
import { aliasTargets, loadCapabilities } from './workflowCapabilities'
import { workflowEdges, workflowNodes } from './workflowGraph'
import { triggerGroups } from './workflowTriggers'
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
const { $dialog } = globalStore()

const INSPECTOR_WIDTH_KEY = 'crm:automation-inspector-width'
const MIN_INSPECTOR_WIDTH = 280
const MAX_INSPECTOR_WIDTH = 720

const loading = ref(false)
const saving = ref(false)
const inspectorWidth = ref(storedInspectorWidth())
const panes = ref(null)
const showRuns = ref(false)
const showTrial = ref(false)
const inspectorOpen = ref(false)
const selectedId = ref('trigger')
const errors = reactive({})
const saveError = ref('')
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
const blocks = computed(() => blockGroups(doc.document_type))
const triggers = triggerGroups()

const relationships = computed(() => parseJson(doc.relationships, []))
const paneColumns = computed(() =>
  inspectorOpen.value ? `1fr 6px ${inspectorWidth.value}px` : '1fr',
)
const canDeleteSelected = computed(() =>
  selectedId.value === 'trigger'
    ? Boolean(doc.trigger_type)
    : Boolean(selectedStep.value),
)

useKeyboardShortcuts({
  active: canDeleteSelected,
  shortcuts: [
    { keys: ['Backspace', 'Delete'], action: confirmSelectedRemoval },
  ],
})

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

/** Measured from the panes' own right edge - the builder is inset inside a dialog. */
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
    trigger_type: '',
    trigger_field: '',
    from_value: '',
    to_value: '',
    custom_event: '',
    date_field: '',
    date_offset: 0,
    date_direction: 'Before',
    cron_expression: '',
    filters: '[]',
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
    inspectorOpen.value = Boolean(doc.trigger_type)
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

function addStep({ after, branch, values }) {
  const created = newStep(values)
  if (!after) doc.actions.push(created)
  else if (branch) after.children[branch].push(created)
  else insertAfter(doc.actions, after, created)
  selectedId.value = created._id
  inspectorOpen.value = true
}

function selectNode(id) {
  selectedId.value = id
  if (id !== 'trigger' || doc.trigger_type) inspectorOpen.value = true
}

function pickTrigger(triggerType) {
  doc.trigger_type = triggerType
  selectedId.value = 'trigger'
  inspectorOpen.value = true
}

function removeSelectedStep() {
  if (!selectedStep.value) return
  if (!removeStep(doc.actions, selectedStep.value)) return
  selectedId.value = 'trigger'
}

function confirmSelectedRemoval() {
  if (!canDeleteSelected.value) return
  const deletingTrigger = selectedId.value === 'trigger'
  $dialog({
    title: deletingTrigger ? __('Delete trigger') : __('Delete step'),
    message: deleteMessage(deletingTrigger),
    actions: [deleteAction(deletingTrigger)],
  })
}

function deleteMessage(deletingTrigger) {
  return deletingTrigger
    ? __('Delete the trigger and all workflow steps? This cannot be undone.')
    : __('Delete this step? This cannot be undone.')
}

function deleteAction(deletingTrigger) {
  return {
    label: __('Delete'),
    variant: 'solid',
    theme: 'red',
    onClick: (close) => {
      if (deletingTrigger) resetTrigger()
      else removeSelectedStep()
      close()
    },
  }
}

function resetTrigger() {
  Object.assign(doc, emptyTriggerState())
  selectedId.value = 'trigger'
  inspectorOpen.value = false
}

function emptyTriggerState() {
  return {
    trigger_type: '',
    trigger_field: '',
    from_value: '',
    to_value: '',
    custom_event: '',
    date_field: '',
    date_offset: 0,
    date_direction: 'Before',
    cron_expression: '',
    filters: '[]',
    condition: '',
    relationships: '[]',
    actions: [],
  }
}

async function saveAutomation() {
  saving.value = true
  clearErrors()
  try {
    validateBeforeSave()
    const saved = props.automationName
      ? await call('frappe.client.save', { doc: payload() })
      : await call('frappe.client.insert', { doc: payload() })
    markClean()
    toast.success(__('Automation saved'))
    emit('saved', saved)
  } catch (error) {
    attachError(error)
    toast.error(saveError.value || __('Could not save automation'))
  } finally {
    saving.value = false
  }
}

function validateBeforeSave() {
  const missing = toRows(doc.actions).find(missingRequiredField)
  if (!missing) return
  const message = __('Choose a field to set')
  attachRowError(missing.idx, message)
  throw new Error(message)
}

function missingRequiredField(row) {
  if (row.step_type !== 'Action' || row.action_type !== 'SetFieldValue')
    return false
  const params = parseJson(row.params, {})
  return !params.field && !hasValues(params.values)
}

function payload() {
  return {
    ...doc,
    title: doc.title || __('Untitled automation'),
    filters: normalizedJsonString(doc.filters, []),
    relationships: JSON.stringify(normalizedRelationships()),
    actions: toRows(doc.actions).map(rowPayload),
  }
}

function normalizedRelationships() {
  return Array.isArray(relationships.value) ? relationships.value : []
}

function normalizedJsonString(value, fallback) {
  return JSON.stringify(parseJson(value, fallback))
}

function rowPayload(row) {
  return {
    ...row,
    doctype: 'Automation Action',
    params: JSON.stringify(normalizedParams(row)),
    related_condition: normalizedRelatedCondition(row.related_condition),
  }
}

function normalizedParams(row) {
  const params = parseJson(row.params, {})
  if (row.action_type !== 'SetFieldValue') return params
  if (!hasValues(params.values)) delete params.values
  return params
}

function hasValues(value) {
  if (!value) return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'object') return Object.keys(value).length > 0
  return true
}

function normalizedRelatedCondition(value) {
  const condition = parseJson(value, null)
  if (!condition || Array.isArray(condition) || !condition.relationship)
    return null
  return JSON.stringify(condition)
}

function clearErrors() {
  saveError.value = ''
  Object.keys(errors).forEach((key) => delete errors[key])
}

/** Server errors read "Row 3: ..." - map that flattened row back onto its node. */
function attachError(error) {
  const message = errorMessage(error)
  saveError.value = message
  const match = message.match(/Row (\d+)/)
  if (match) return attachRowError(Number(match[1]), message)
  const node = selectedStep.value
  if (!node) return
  errors[node._id] = [{ message }]
}

function attachRowError(rowIndex, message) {
  const node = placed.value[rowIndex - 1]?.node
  if (!node) return
  errors[node._id] = [{ message }]
  selectedId.value = node._id
}

function errorMessage(error) {
  const messages = error?.messages || error?._server_messages
  if (Array.isArray(messages) && messages.length)
    return cleanMessage(messages[0])
  return cleanMessage(error?.message || error)
}

function cleanMessage(message) {
  try {
    return JSON.parse(message).message || String(message)
  } catch {
    return String(message || __('Could not save automation'))
  }
}
</script>
