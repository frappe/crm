<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        v-if="!editing"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createAutomation"
      />
      <div v-else class="flex items-center gap-2">
        <Button :label="__('Back')" @click="closeEditor" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          @click="saveAutomation"
        />
      </div>
    </template>
  </LayoutHeader>

  <!-- list -->
  <div v-if="!editing" class="flex-1 overflow-y-auto">
    <div
      v-if="automations.data?.length"
      class="mx-auto flex w-full max-w-4xl flex-col divide-y divide-outline-gray-1 px-3 py-2 sm:px-5"
    >
      <div
        v-for="row in automations.data"
        :key="row.name"
        class="flex cursor-pointer items-center gap-4 rounded px-2 py-3 hover:bg-surface-gray-1"
        @click="openAutomation(row.name)"
      >
        <AutomationIcon
          class="size-5 shrink-0"
          :class="row.enabled ? 'text-ink-green-5' : 'text-ink-gray-4'"
        />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="truncate text-base font-medium text-ink-gray-9">
              {{ row.title }}
            </span>
            <Badge
              :label="row.enabled ? __('Active') : __('Draft')"
              :theme="row.enabled ? 'green' : 'gray'"
              size="sm"
            />
          </div>
          <div class="mt-0.5 truncate text-sm text-ink-gray-5">
            {{ __(row.trigger_event) }}
            <span v-if="row.description"> · {{ row.description }}</span>
          </div>
        </div>
        <div class="shrink-0 text-sm text-ink-gray-5">
          {{ row.active_count }} {{ __('active') }} ·
          {{ row.enrolled_count }} {{ __('total') }}
        </div>
        <Dropdown :options="rowOptions(row)" @click.stop>
          <Button variant="ghost" icon="lucide-more-horizontal" />
        </Dropdown>
      </div>
    </div>
    <div
      v-else-if="!automations.loading"
      class="flex h-full flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <AutomationIcon class="h-8 w-8" />
      <span class="text-lg font-medium">{{ __('No Automations Found') }}</span>
      <span class="text-sm">
        {{ __('Create a sequence of automated steps triggered by CRM events.') }}
      </span>
      <Button
        class="mt-2"
        variant="solid"
        :label="__('Create your first automation')"
        iconLeft="plus"
        @click="createAutomation"
      />
    </div>
  </div>

  <!-- editor -->
  <div v-else class="flex-1 overflow-y-auto">
    <div class="mx-auto w-full max-w-2xl px-3 py-6 sm:px-5">
      <!-- settings card -->
      <div class="rounded-lg border border-outline-gray-2 bg-surface-base p-4">
        <div class="mb-3 flex items-center justify-between">
          <span class="text-lg font-semibold text-ink-gray-9">
            {{ __('Automation') }}
          </span>
          <div class="flex items-center gap-2 text-sm text-ink-gray-5">
            {{ draft.enabled ? __('Active') : __('Draft') }}
            <Switch v-model="draft.enabled" />
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <FormControl
            v-model="draft.title"
            type="text"
            :label="__('Title')"
            :placeholder="__('e.g. Welcome sequence')"
            required
          />
          <FormControl
            v-model="draft.description"
            type="text"
            :label="__('Description')"
          />
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormControl
              v-model="draft.trigger_event"
              type="select"
              :label="__('Trigger')"
              :options="triggerOptions"
            />
            <div class="flex items-end gap-4 pb-1">
              <label class="flex items-center gap-2 text-sm text-ink-gray-7">
                <Switch v-model="draft.exit_on_reply" size="sm" />
                {{ __('Exit on reply') }}
              </label>
              <label class="flex items-center gap-2 text-sm text-ink-gray-7">
                <Switch v-model="draft.allow_reenrollment" size="sm" />
                {{ __('Re-enrollment') }}
              </label>
            </div>
          </div>
          <div>
            <div class="mb-1 text-xs text-ink-gray-5">
              {{ __('Only enroll records matching (optional)') }}
            </div>
            <ConditionRow v-model="draft.trigger_condition" :meta="meta" />
          </div>
        </div>
      </div>

      <!-- vertical sequence -->
      <div class="mt-6 flex flex-col items-center">
        <div class="rounded-full bg-surface-gray-2 px-3 py-1 text-sm text-ink-gray-7">
          {{ __(draft.trigger_event) }}
        </div>
        <template v-for="(step, i) in draft.steps" :key="i">
          <div class="h-5 w-px bg-outline-gray-3" />
          <div
            class="group w-full cursor-pointer rounded-lg border border-outline-gray-2 bg-surface-base p-3 hover:border-outline-gray-3"
            @click="editStep(i)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Badge :label="stepLabel(step.type)" :theme="stepTheme(step.type)" />
                <span
                  v-if="step.condition"
                  class="text-xs text-ink-amber-3"
                  :title="conditionSummary(step.condition)"
                >
                  {{ __('if') }} {{ conditionSummary(step.condition) }}
                </span>
              </div>
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                <Button
                  variant="ghost"
                  icon="lucide-arrow-up"
                  :disabled="i == 0"
                  @click.stop="moveStep(i, -1)"
                />
                <Button
                  variant="ghost"
                  icon="lucide-arrow-down"
                  :disabled="i == draft.steps.length - 1"
                  @click.stop="moveStep(i, 1)"
                />
                <Button
                  variant="ghost"
                  icon="lucide-trash-2"
                  @click.stop="draft.steps.splice(i, 1)"
                />
              </div>
            </div>
            <div class="mt-1 truncate text-sm text-ink-gray-6">
              {{ stepSummary(step) }}
            </div>
          </div>
        </template>
        <div class="h-5 w-px bg-outline-gray-3" />
        <Dropdown :options="addStepOptions">
          <Button variant="subtle" :label="__('Add step')" iconLeft="plus" />
        </Dropdown>
      </div>

      <!-- enrollments -->
      <div v-if="draft.name" class="mt-8">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-base font-semibold text-ink-gray-9">
            {{ __('Recent enrollments') }}
          </span>
          <Button
            variant="ghost"
            icon="lucide-refresh-cw"
            @click="enrollments.reload()"
          />
        </div>
        <div
          v-if="enrollments.data?.length"
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="enr in enrollments.data"
            :key="enr.name"
            class="flex items-center justify-between px-3 py-2 text-sm"
          >
            <span class="truncate text-ink-gray-8">{{ enr.reference_name }}</span>
            <span class="flex items-center gap-3 text-ink-gray-5">
              <span>{{ __('step') }} {{ enr.current_step + 1 }}</span>
              <Badge :label="__(enr.status)" :theme="enrollmentTheme(enr.status)" size="sm" />
            </span>
          </div>
        </div>
        <div v-else class="text-sm text-ink-gray-4">
          {{ __('No enrollments yet.') }}
        </div>
      </div>
    </div>
  </div>

  <!-- step editor dialog -->
  <Dialog
    v-model="showStepDialog"
    :options="{ title: stepLabel(stepDraft.type), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <template v-if="stepDraft.type == 'send_email'">
          <FormControl v-model="stepDraft.subject" type="text" :label="__('Subject')" />
          <FormControl
            v-model="stepDraft.message"
            type="textarea"
            :label="__('Message')"
            :placeholder="__('Hi {{ first_name }}, ...')"
          />
        </template>
        <template v-else-if="stepDraft.type == 'send_sms' || stepDraft.type == 'notify'">
          <FormControl
            v-model="stepDraft.message"
            type="textarea"
            :label="__('Message')"
            :placeholder="__('Hi {{ first_name }}, ...')"
          />
        </template>
        <template v-else-if="stepDraft.type == 'send_whatsapp_template'">
          <FormControl
            v-model="stepDraft.template"
            type="select"
            :label="__('Template')"
            :options="(meta.data?.whatsapp_templates || []).map((t) => ({ label: t, value: t }))"
          />
        </template>
        <template v-else-if="stepDraft.type == 'create_task'">
          <FormControl v-model="stepDraft.title" type="text" :label="__('Task title')" />
          <FormControl
            v-model="stepDraft.due_in_days"
            type="number"
            :label="__('Due in (days)')"
          />
          <FormControl
            v-model="stepDraft.assigned_to"
            type="select"
            :label="__('Assign to (optional)')"
            :options="userOptions"
          />
        </template>
        <template v-else-if="stepDraft.type == 'assign'">
          <FormControl
            v-model="stepDraft.user"
            type="select"
            :label="__('User')"
            :options="userOptions"
          />
        </template>
        <template v-else-if="stepDraft.type == 'add_tag_comment'">
          <FormControl v-model="stepDraft.comment" type="textarea" :label="__('Comment')" />
        </template>
        <template v-else-if="stepDraft.type == 'set_field'">
          <FormControl
            v-model="stepDraft.field"
            type="text"
            :label="__('Field name')"
            :placeholder="__('e.g. status')"
          />
          <FormControl v-model="stepDraft.value" type="text" :label="__('Value')" />
        </template>
        <template v-else-if="stepDraft.type == 'wait'">
          <div class="grid grid-cols-3 gap-3">
            <FormControl v-model="stepDraft.days" type="number" :label="__('Days')" />
            <FormControl v-model="stepDraft.hours" type="number" :label="__('Hours')" />
            <FormControl v-model="stepDraft.minutes" type="number" :label="__('Minutes')" />
          </div>
        </template>
        <template v-if="stepDraft.type == 'stop_if'">
          <div class="mb-1 text-xs text-ink-gray-5">{{ __('Stop when') }}</div>
          <ConditionRow v-model="stepDraft.condition" :meta="meta" required />
        </template>
        <template v-else>
          <div class="mt-2 border-t border-outline-gray-1 pt-3">
            <div class="mb-1 text-xs text-ink-gray-5">
              {{ __('Run only if (optional)') }}
            </div>
            <ConditionRow v-model="stepDraft.condition" :meta="meta" />
          </div>
        </template>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Done')"
        @click="applyStep"
      />
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import AutomationIcon from '@/components/Icons/AutomationIcon.vue'
import ConditionRow from '@/components/Automations/ConditionRow.vue'
import {
  createResource,
  Breadcrumbs,
  Dropdown,
  Dialog,
  Switch,
  FormControl,
  toast,
} from 'frappe-ui'
import { ref, reactive, computed } from 'vue'

const breadcrumbs = computed(() => {
  const items = [{ label: __('Automations'), route: { name: 'Automations' } }]
  if (editing.value) {
    items.push({ label: draft.title || __('New Automation') })
  }
  return items
})

const editing = ref(false)
const saving = ref(false)

const emptyDraft = () => ({
  name: null,
  title: '',
  description: '',
  enabled: false,
  trigger_event: 'Lead Created',
  trigger_condition: null,
  allow_reenrollment: false,
  exit_on_reply: false,
  steps: [],
})

const draft = reactive(emptyDraft())

const automations = createResource({
  url: 'crm.api.automation.list_automations',
  cache: 'crm-automations',
  auto: true,
})

const meta = createResource({
  url: 'crm.api.automation.get_builder_meta',
  cache: 'crm-automation-meta',
  auto: true,
})

const enrollments = createResource({
  url: 'crm.api.automation.get_enrollments',
  makeParams: () => ({ automation: draft.name }),
})

const triggerOptions = computed(() =>
  (meta.data?.trigger_events || []).map((t) => ({ label: __(t), value: t })),
)

const userOptions = computed(() => [
  { label: '', value: '' },
  ...(meta.data?.users || []).map((u) => ({ label: u, value: u })),
])

const STEP_LABELS = {
  send_email: 'Send Email',
  send_sms: 'Send SMS',
  send_whatsapp_template: 'Send WhatsApp Template',
  create_task: 'Create Task',
  assign: 'Assign User',
  add_tag_comment: 'Add Comment',
  set_field: 'Update Field',
  notify: 'Notify Team',
  wait: 'Wait',
  stop_if: 'Stop If',
}

function stepLabel(type) {
  return __(STEP_LABELS[type] || type)
}

function stepTheme(type) {
  if (type == 'wait') return 'orange'
  if (type == 'stop_if') return 'red'
  if (['send_email', 'send_sms', 'send_whatsapp_template'].includes(type))
    return 'blue'
  return 'gray'
}

function stepSummary(step) {
  switch (step.type) {
    case 'send_email':
      return step.subject || __('No subject')
    case 'send_sms':
    case 'notify':
      return step.message || __('No message')
    case 'send_whatsapp_template':
      return step.template || __('No template selected')
    case 'create_task':
      return step.title || __('Follow up')
    case 'assign':
      return step.user || __('No user selected')
    case 'add_tag_comment':
      return step.comment || __('No comment')
    case 'set_field':
      return `${step.field || '?'} → ${step.value ?? '?'}`
    case 'wait':
      return [
        step.days && `${step.days} ${__('days')}`,
        step.hours && `${step.hours} ${__('hours')}`,
        step.minutes && `${step.minutes} ${__('minutes')}`,
      ]
        .filter(Boolean)
        .join(', ')
    case 'stop_if':
      return conditionSummary(step.condition)
    default:
      return ''
  }
}

function conditionSummary(condition) {
  if (!condition?.field) return ''
  return `${condition.field} ${__(condition.operator || 'equals')} ${
    condition.value ?? ''
  }`
}

function enrollmentTheme(status) {
  return (
    { Active: 'blue', Waiting: 'orange', Completed: 'green', Exited: 'gray', Failed: 'red' }[
      status
    ] || 'gray'
  )
}

// --- list actions ---

function rowOptions(row) {
  return [
    {
      label: row.enabled ? __('Disable') : __('Enable'),
      icon: row.enabled ? 'pause' : 'play',
      onClick: () => toggle(row),
    },
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => remove(row),
    },
  ]
}

function toggle(row) {
  createResource({
    url: 'crm.api.automation.toggle_automation',
    params: { name: row.name, enabled: !row.enabled },
    auto: true,
    onSuccess: () => automations.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to update')),
  })
}

function remove(row) {
  createResource({
    url: 'crm.api.automation.delete_automation',
    params: { name: row.name },
    auto: true,
    onSuccess: () => automations.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}

// --- editor ---

function createAutomation() {
  Object.assign(draft, emptyDraft())
  editing.value = true
}

function openAutomation(name) {
  createResource({
    url: 'crm.api.automation.get_automation',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(draft, emptyDraft(), data, {
        enabled: Boolean(data.enabled),
        allow_reenrollment: Boolean(data.allow_reenrollment),
        exit_on_reply: Boolean(data.exit_on_reply),
      })
      editing.value = true
      enrollments.fetch()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function closeEditor() {
  editing.value = false
  automations.reload()
}

function saveAutomation() {
  if (!draft.title.trim()) {
    toast.error(__('Title is required'))
    return
  }
  if (!draft.steps.length) {
    toast.error(__('Add at least one step'))
    return
  }
  saving.value = true
  createResource({
    url: 'crm.api.automation.save_automation',
    params: {
      name: draft.name,
      automation: {
        title: draft.title,
        description: draft.description,
        trigger_event: draft.trigger_event,
        trigger_condition: draft.trigger_condition?.field
          ? draft.trigger_condition
          : null,
        allow_reenrollment: draft.allow_reenrollment,
        exit_on_reply: draft.exit_on_reply,
        steps: draft.steps,
      },
    },
    auto: true,
    onSuccess: (data) => {
      saving.value = false
      draft.name = data.name
      if (draft.enabled != Boolean(data.enabled)) {
        createResource({
          url: 'crm.api.automation.toggle_automation',
          params: { name: data.name, enabled: draft.enabled },
          auto: true,
        })
      }
      toast.success(__('Automation saved'))
      automations.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

// --- step editing ---

const showStepDialog = ref(false)
const stepDraft = reactive({ type: 'send_email' })
const editingStepIndex = ref(-1)

const addStepOptions = computed(() =>
  Object.keys(STEP_LABELS).map((type) => ({
    label: stepLabel(type),
    onClick: () => addStep(type),
  })),
)

function addStep(type) {
  Object.keys(stepDraft).forEach((k) => delete stepDraft[k])
  Object.assign(stepDraft, { type })
  if (type == 'wait') Object.assign(stepDraft, { days: 0, hours: 4, minutes: 0 })
  editingStepIndex.value = -1
  showStepDialog.value = true
}

function editStep(i) {
  Object.keys(stepDraft).forEach((k) => delete stepDraft[k])
  Object.assign(stepDraft, JSON.parse(JSON.stringify(draft.steps[i])))
  editingStepIndex.value = i
  showStepDialog.value = true
}

function applyStep() {
  const step = JSON.parse(JSON.stringify(stepDraft))
  if (step.condition && !step.condition.field) delete step.condition
  if (editingStepIndex.value == -1) {
    draft.steps.push(step)
  } else {
    draft.steps[editingStepIndex.value] = step
  }
  showStepDialog.value = false
}

function moveStep(i, delta) {
  const j = i + delta
  if (j < 0 || j >= draft.steps.length) return
  const [step] = draft.steps.splice(i, 1)
  draft.steps.splice(j, 0, step)
}
</script>
