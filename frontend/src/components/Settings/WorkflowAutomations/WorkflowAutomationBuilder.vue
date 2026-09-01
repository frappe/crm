<template>
  <div class="relative flex h-full min-h-0 flex-col bg-surface-elevation-2">
    <div
      class="flex h-14 shrink-0 items-center justify-between border-b border-outline-gray-2 px-4"
    >
      <div class="flex min-w-0 items-center gap-2">
        <div
          class="flex min-w-0 cursor-text items-center gap-1 rounded pr-1.5 transition-colors hover:bg-surface-gray-2"
          @focusin="selectTitle"
        >
          <div
            class="title-sizer text-base"
            :data-value="doc.title || __('Untitled automation')"
          >
            <TextInput
              variant="ghost"
              :model-value="doc.title"
              :aria-label="__('Automation title')"
              :placeholder="__('Untitled automation')"
              @update:model-value="setTitle"
            />
          </div>
          <EditIcon class="size-3.5 shrink-0 text-ink-gray-4" />
        </div>
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
          :label="doc.enabled ? __('Disable') : __('Enable')"
          :disabled="!doc.trigger_type"
          @click="doc.enabled = doc.enabled ? 0 : 1"
        />
        <Button
          :label="__('Save')"
          variant="solid"
          :loading="saving"
          :disabled="!dirty"
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
      <div class="relative min-h-0 outline-none" autofocus tabindex="0">
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
        class="relative cursor-col-resize bg-transparent after:absolute after:inset-y-0 after:left-1/2 after:w-px after:-translate-x-1/2 after:bg-outline-gray-2 after:transition-colors hover:after:bg-outline-gray-4"
        role="separator"
        aria-orientation="vertical"
        :aria-label="__('Resize panel')"
        tabindex="0"
        @mousedown.prevent="startResize"
        @keydown.left.prevent="nudgeResize(24)"
        @keydown.right.prevent="nudgeResize(-24)"
      />
      <div v-if="inspectorOpen" class="min-h-0 border-l">
        <AutomationInspector
          :doc="doc"
          :selected-step="selectedStep"
          :targets="targetsFor(selectedStep)"
          :loading="loading"
          @request-remove="confirmSelectedRemoval"
        />
      </div>
    </div>
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
import AutomationTrialRun from './WorkflowTrialRun.vue'
import WorkflowFlow from './WorkflowFlow.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { globalStore } from '@/stores/global'
import { blockGroups } from './workflowBlocks'
import { aliasTargets, loadCapabilities } from './workflowCapabilities'
import { workflowEdges, workflowNodes } from './workflowGraph'
import { triggerFromValue, triggerGroups } from './workflowTriggers'
import {
  insertAfter,
  layoutSteps,
  newStep,
  removeStep,
  stepsBefore,
  toRows,
  toTree,
} from './workflowSteps'
import EditIcon from '~icons/lucide/pencil'
import { Badge, Button, Dialog, TextInput, call, toast } from 'frappe-ui'
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
const showTrial = ref(false)
const inspectorOpen = ref(false)
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
const blocks = computed(() => blockGroups(doc.document_type))
const triggers = computed(() => triggerGroups(doc.document_type))

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
  } finally {
    loading.value = false
    markClean()
  }
}

function markClean() {
  savedSnapshot.value = JSON.stringify(payload())
}

/** Take the server's name and timestamp, so the next save is not a stale write. */
function adoptSaved(saved) {
  doc.name = saved.name
  doc.modified = saved.modified
  markClean()
}

function setTitle(title) {
  doc.title = title
}

/** Focus lands on the inner input, so select from the wrapper the icon shares. */
function selectTitle(event) {
  if (event.target instanceof HTMLInputElement) event.target.select()
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

function pickTrigger(trigger) {
  applyTrigger(trigger)
  selectedId.value = 'trigger'
  inspectorOpen.value = true
}

/** Event triggers store as a Custom Event; anything else clears the event it replaces. */
function applyTrigger(value) {
  Object.assign(doc, triggerFromValue(value))
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
    adoptSaved(saved)
    toast.success(__('Automation saved'))
    emit('saved', saved)
  } catch (error) {
    toast.error(attachError(error))
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
  Object.keys(errors).forEach((key) => delete errors[key])
}

/** Server errors read "Row 3: ..." - map that flattened row back onto its node. */
function attachError(error) {
  const message = errorMessage(error)
  const match = message.match(/Row (\d+)/)
  if (match) attachRowError(Number(match[1]), message)
  else if (selectedStep.value) errors[selectedStep.value._id] = [{ message }]
  return message
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

<style scoped>
/* An invisible mirror of the text sets the track width, so the field is only
   ever as wide as its content until it hits the cap and truncates. */
.title-sizer {
  display: inline-grid;
  min-width: 0;
  max-width: min(28rem, 40vw);
}

.title-sizer::after,
.title-sizer > * {
  grid-area: 1 / 1;
}

/* Matches TextInput's sm padding so the mirror and the field measure the same. */
.title-sizer::after {
  content: attr(data-value);
  visibility: hidden;
  white-space: pre;
  min-width: 6rem;
  padding: 0 8px;
  font: inherit;
  letter-spacing: inherit;
}

.title-sizer :deep(input) {
  cursor: text;
  background: transparent;
  text-overflow: ellipsis;
}

.title-sizer :deep(input::selection) {
  background: var(--surface-gray-3, #e2e8f0);
}
</style>
