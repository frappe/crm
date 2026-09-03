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
    <div class="mx-auto w-full max-w-3xl px-3 py-6 sm:px-5">
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
                {{ __('Stop on reply') }}
              </label>
              <label class="flex items-center gap-2 text-sm text-ink-gray-7">
                <Switch v-model="draft.allow_reenrollment" size="sm" />
                {{ __('Re-enrollment') }}
              </label>
            </div>
          </div>

          <!-- trigger-specific config -->
          <div
            v-if="triggerConfigKind"
            class="rounded-md border border-outline-gray-1 bg-surface-gray-1 p-3"
          >
            <div class="mb-2 text-xs font-medium text-ink-gray-6">
              {{ __('Trigger filters') }}
            </div>
            <FormControl
              v-if="triggerConfigKind == 'tag'"
              v-model="draft.trigger_config.tag"
              type="text"
              :label="__('Only this tag (empty = any)')"
            />
            <FormControl
              v-else-if="triggerConfigKind == 'link'"
              v-model="draft.trigger_config.link"
              type="select"
              :label="__('Tracked link')"
              :options="linkOptions"
            />
            <div
              v-else-if="triggerConfigKind == 'date'"
              class="grid grid-cols-2 gap-3 sm:grid-cols-4"
            >
              <FormControl
                v-model="draft.trigger_config.date_field"
                type="text"
                :label="__('Date field')"
                :placeholder="__('e.g. custom_birthday')"
              />
              <FormControl
                v-model="draft.trigger_config.offset_days"
                type="number"
                :label="__('Days offset')"
              />
              <FormControl
                v-model="draft.trigger_config.direction"
                type="select"
                :label="__('Direction')"
                :options="[
                  { label: __('Before'), value: 'before' },
                  { label: __('After'), value: 'after' },
                ]"
              />
              <div class="flex items-end pb-1">
                <label class="flex items-center gap-2 text-sm text-ink-gray-7">
                  <Switch v-model="draft.trigger_config.annual" size="sm" />
                  {{ __('Every year') }}
                </label>
              </div>
            </div>
            <div v-else-if="triggerConfigKind == 'webhook'" class="text-sm">
              <div v-if="draft.webhook_key" class="break-all text-ink-gray-7">
                POST {{ webhookUrl }}
              </div>
              <div v-else class="text-ink-gray-5">
                {{ __('Save the automation to generate the webhook URL.') }}
              </div>
            </div>
          </div>

          <div>
            <div class="mb-1 text-xs text-ink-gray-5">
              {{ __('Only enroll records matching (optional)') }}
            </div>
            <ConditionRow v-model="draft.trigger_condition" :meta="meta" />
          </div>

          <!-- time window -->
          <div class="rounded-md border border-outline-gray-1 bg-surface-gray-1 p-3">
            <label class="flex items-center gap-2 text-sm text-ink-gray-7">
              <Switch v-model="draft.time_window_enabled" size="sm" />
              {{ __('Send messages only in a time window') }}
            </label>
            <div v-if="draft.time_window_enabled" class="mt-2">
              <div class="grid grid-cols-2 gap-3">
                <FormControl
                  v-model="draft.window_start"
                  type="time"
                  :label="__('From')"
                />
                <FormControl v-model="draft.window_end" type="time" :label="__('To')" />
              </div>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <Button
                  v-for="day in WEEKDAYS"
                  :key="day"
                  size="sm"
                  :variant="draft.window_days.includes(day) ? 'solid' : 'outline'"
                  :label="__(day).slice(0, 3)"
                  @click="toggleDay(day)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- vertical sequence -->
      <div class="mt-6 flex flex-col items-center">
        <div class="rounded-full bg-surface-gray-2 px-3 py-1 text-sm text-ink-gray-7">
          {{ __(draft.trigger_event) }}
        </div>
        <StepList :steps="draft.steps" :meta="meta" />
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
          <FormControl
            v-model="stepDraft.email_template"
            type="select"
            :label="__('Email template (optional)')"
            :options="withEmpty(meta.data?.email_templates)"
          />
          <FormControl v-model="stepDraft.subject" type="text" :label="__('Subject')" />
          <FormControl
            v-model="stepDraft.message"
            type="textarea"
            :label="__('Message')"
            :placeholder="placeholderHint"
          />
        </template>
        <template v-else-if="['send_sms', 'notify'].includes(stepDraft.type)">
          <FormControl
            v-model="stepDraft.message"
            type="textarea"
            :label="__('Message')"
            :placeholder="placeholderHint"
          />
        </template>
        <template v-else-if="stepDraft.type == 'send_whatsapp_template'">
          <FormControl
            v-model="stepDraft.template"
            type="select"
            :label="__('Template')"
            :options="withEmpty(meta.data?.whatsapp_templates)"
          />
          <div>
            <div class="mb-1 flex items-center justify-between">
              <span class="text-xs text-ink-gray-5">{{ __('Template variables') }}</span>
              <Button size="sm" variant="ghost" :label="__('Add')" @click="addTemplateParameter" />
            </div>
            <FormControl
              v-for="(value, index) in stepDraft.template_parameters || []"
              :key="index"
              :modelValue="value"
              type="text"
              class="mb-1.5"
              :label="variableLabel(index)"
              :placeholder="placeholderHint"
              @update:modelValue="(v) => (stepDraft.template_parameters[index] = v)"
            />
            <p class="text-xs text-ink-gray-4">
              {{ __('Leave empty if the template has no variables.') }}
            </p>
          </div>
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
          <div class="text-xs text-ink-gray-5">
            {{ __('One user = fixed. Multiple users = equal round robin.') }}
          </div>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="u in meta.data?.users || []"
              :key="u"
              size="sm"
              :variant="(stepDraft.users || []).includes(u) ? 'solid' : 'outline'"
              :label="u"
              @click="toggleUser(u)"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="stepDraft.only_if_unassigned" size="sm" />
            {{ __('Only apply to unassigned records') }}
          </label>
        </template>
        <template v-else-if="['add_note', 'add_tag_comment'].includes(stepDraft.type)">
          <FormControl v-model="stepDraft.comment" type="textarea" :label="__('Note')" />
        </template>
        <template v-else-if="['add_tag', 'remove_tag'].includes(stepDraft.type)">
          <FormControl v-model="stepDraft.tag" type="text" :label="__('Tag')" />
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
        <template v-else-if="stepDraft.type == 'webhook'">
          <FormControl
            v-model="stepDraft.method"
            type="select"
            :options="['POST', 'GET', 'PUT', 'DELETE'].map((m) => ({ label: m, value: m }))"
            :label="__('Method')"
          />
          <FormControl v-model="stepDraft.url" type="text" :label="__('URL')" />
          <FormControl
            v-model="stepDraft.body"
            type="textarea"
            :label="__('JSON body (optional, Jinja allowed)')"
            :placeholder="'{&quot;email&quot;: &quot;{{ email }}&quot;}'"
          />
        </template>
        <template v-else-if="stepDraft.type == 'wait'">
          <FormControl
            v-model="stepDraft.mode"
            type="select"
            :label="__('Wait for')"
            :options="[
              { label: __('A period of time'), value: 'duration' },
              { label: __('A time of day'), value: 'until_time' },
              { label: __('The contact to reply'), value: 'until_reply' },
              { label: __('A tracked link click'), value: 'until_link_click' },
            ]"
          />
          <div v-if="stepDraft.mode == 'duration'" class="grid grid-cols-3 gap-3">
            <FormControl v-model="stepDraft.days" type="number" :label="__('Days')" />
            <FormControl v-model="stepDraft.hours" type="number" :label="__('Hours')" />
            <FormControl v-model="stepDraft.minutes" type="number" :label="__('Minutes')" />
          </div>
          <template v-else-if="stepDraft.mode == 'until_time'">
            <FormControl v-model="stepDraft.time" type="time" :label="__('Resume at')" />
          </template>
          <template v-else>
            <FormControl
              v-if="stepDraft.mode == 'until_link_click'"
              v-model="stepDraft.link"
              type="select"
              :label="__('Tracked link')"
              :options="linkOptions"
            />
            <FormControl
              v-model="stepDraft.timeout_hours"
              type="number"
              :label="__('Timeout (hours, empty = wait forever)')"
            />
            <div class="text-xs text-ink-gray-5">
              {{
                __(
                  'After this wait, branch with If/Else on field "wait_result" = event or timeout.',
                )
              }}
            </div>
          </template>
        </template>
        <template v-else-if="stepDraft.type == 'goal'">
          <FormControl
            v-model="stepDraft.event"
            type="select"
            :label="__('Goal')"
            :options="[
              { label: __('Contact replied'), value: 'reply' },
              { label: __('Tracked link clicked'), value: 'link_clicked' },
              { label: __('Tag added'), value: 'tag_added' },
              { label: __('Status becomes'), value: 'status_is' },
              { label: __('Appointment booked'), value: 'booking_booked' },
            ]"
          />
          <FormControl
            v-if="['link_clicked', 'tag_added', 'status_is'].includes(stepDraft.event)"
            v-model="stepDraft.value"
            type="text"
            :label="__('Value (link slug / tag / status; empty = any)')"
          />
          <FormControl
            v-model="stepDraft.outcome"
            type="select"
            :label="__('If a contact reaches this step without meeting the goal')"
            :options="[
              { label: __('Continue anyway'), value: 'continue' },
              { label: __('Wait until the goal is met'), value: 'wait' },
              { label: __('End this automation'), value: 'end' },
            ]"
          />
        </template>
        <template v-else-if="stepDraft.type == 'go_to'">
          <FormControl
            v-model="stepDraft.target"
            type="text"
            :label="__('Target step label')"
            :placeholder="__('Set a label on the target step first')"
          />
        </template>
        <template v-else-if="stepDraft.type == 'add_to_workflow'">
          <FormControl
            v-model="stepDraft.automation"
            type="select"
            :label="__('Automation')"
            :options="withEmpty(meta.data?.automations)"
          />
        </template>
        <template v-else-if="stepDraft.type == 'remove_from_workflow'">
          <FormControl
            v-model="stepDraft.automation"
            type="select"
            :label="__('Automation (or all)')"
            :options="[{ label: __('All'), value: 'all' }, ...withEmpty(meta.data?.automations).slice(1)]"
          />
        </template>
        <template v-if="stepDraft.type == 'stop_if'">
          <div class="mb-1 text-xs text-ink-gray-5">{{ __('Stop when') }}</div>
          <ConditionRow v-model="stepDraft.condition" :meta="meta" required />
        </template>
        <template v-else-if="stepDraft.type == 'split'">
          <div
            v-for="(path, pi) in stepDraft.paths"
            :key="pi"
            class="grid grid-cols-[1fr_100px_32px] items-end gap-2"
          >
            <FormControl v-model="path.label" type="text" :label="pi == 0 ? __('Path') : ''" />
            <FormControl v-model="path.percent" type="number" :label="pi == 0 ? '%' : ''" />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              :disabled="stepDraft.paths.length <= 2"
              @click="stepDraft.paths.splice(pi, 1)"
            />
          </div>
          <Button variant="ghost" :label="__('Add path')" iconLeft="plus" @click="addSplitPath" />
        </template>

        <template
          v-if="!['stop_if', 'if_else', 'split', 'goal', 'go_to', 'exit'].includes(stepDraft.type)"
        >
          <div class="mt-2 border-t border-outline-gray-1 pt-3">
            <div class="mb-1 text-xs text-ink-gray-5">
              {{ __('Run only if (optional)') }}
            </div>
            <ConditionRow v-model="stepDraft.condition" :meta="meta" />
          </div>
          <FormControl
            v-model="stepDraft.label"
            type="text"
            :label="__('Label (for Go To, optional)')"
          />
        </template>
      </div>
    </template>
    <template #actions>
      <Button class="w-full" variant="solid" :label="__('Done')" @click="applyStep" />
    </template>
  </Dialog>

  <!-- branch editor dialog -->
  <Dialog v-model="showBranchDialog" :options="{ title: __('Branch'), size: 'lg' }">
    <template #body-content>
      <div v-if="branchDraft" class="flex flex-col gap-3">
        <FormControl v-model="branchDraft.label" type="text" :label="__('Branch name')" />
        <div class="text-xs text-ink-gray-5">
          {{ __('Conditions in a group are ANDed; groups are ORed.') }}
        </div>
        <div
          v-for="(group, gi) in branchDraft.condition_groups"
          :key="gi"
          class="rounded-md border border-outline-gray-1 p-2"
        >
          <div
            v-for="(cond, ci) in group"
            :key="ci"
            class="mb-2 grid grid-cols-[1fr_1fr_1fr_32px] gap-2"
          >
            <FormControl v-model="cond.field" type="text" :placeholder="__('field')" />
            <FormControl
              v-model="cond.operator"
              type="select"
              :options="(meta.data?.condition_operators || []).map((o) => ({ label: __(o), value: o }))"
            />
            <FormControl v-model="cond.value" type="text" :placeholder="__('value')" />
            <Button variant="ghost" icon="lucide-trash-2" @click="group.splice(ci, 1)" />
          </div>
          <div class="flex justify-between">
            <Button
              variant="ghost"
              size="sm"
              :label="__('AND condition')"
              iconLeft="plus"
              @click="group.push({ field: '', operator: 'equals', value: '' })"
            />
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-trash-2"
              @click="branchDraft.condition_groups.splice(gi, 1)"
            />
          </div>
        </div>
        <Button
          variant="ghost"
          :label="__('OR group')"
          iconLeft="plus"
          @click="branchDraft.condition_groups.push([{ field: '', operator: 'equals', value: '' }])"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Done')"
        @click="showBranchDialog = false"
      />
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import AutomationIcon from '@/components/Icons/AutomationIcon.vue'
import ConditionRow from '@/components/Automations/ConditionRow.vue'
import StepList from '@/components/Automations/StepList.vue'
import {
  createResource,
  Breadcrumbs,
  Dropdown,
  Dialog,
  Switch,
  FormControl,
  toast,
} from 'frappe-ui'
import { ref, reactive, computed, provide } from 'vue'

const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const placeholderHint = __('Hi {{ first_name }} … links: {{ tracked_link("slug") }}')

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
  trigger_config: {},
  allow_reenrollment: false,
  exit_on_reply: false,
  time_window_enabled: false,
  window_start: '',
  window_end: '',
  window_days: [],
  webhook_key: '',
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

const linkOptions = computed(() => withEmpty(meta.data?.tracked_links))

function withEmpty(list) {
  return [{ label: '', value: '' }, ...(list || []).map((x) => ({ label: x, value: x }))]
}

const triggerConfigKind = computed(() => {
  const t = draft.trigger_event
  if (t == 'Tag Added' || t == 'Tag Removed') return 'tag'
  if (t == 'Trigger Link Clicked') return 'link'
  if (t == 'Date Reminder') return 'date'
  if (t == 'Inbound Webhook') return 'webhook'
  return null
})

const webhookUrl = computed(
  () =>
    `${window.location.origin}/api/method/crm.api.automation.inbound_webhook?automation=${encodeURIComponent(draft.name || '')}&key=${draft.webhook_key}`,
)

function toggleDay(day) {
  const i = draft.window_days.indexOf(day)
  i == -1 ? draft.window_days.push(day) : draft.window_days.splice(i, 1)
}

function toggleUser(u) {
  stepDraft.users = stepDraft.users || []
  const i = stepDraft.users.indexOf(u)
  i == -1 ? stepDraft.users.push(u) : stepDraft.users.splice(i, 1)
}

const STEP_LABELS = {
  send_email: 'Send Email',
  send_sms: 'Send SMS',
  send_whatsapp_template: 'Send WhatsApp Template',
  notify: 'Internal Notification',
  create_task: 'Create Task',
  assign: 'Assign User',
  add_note: 'Add Note',
  add_tag_comment: 'Add Note',
  add_tag: 'Add Tag',
  remove_tag: 'Remove Tag',
  set_field: 'Update Field',
  convert_to_deal: 'Convert Lead to Deal',
  webhook: 'Webhook',
  wait: 'Wait',
  if_else: 'If / Else',
  split: 'Split test',
  goal: 'Goal',
  go_to: 'Go To',
  exit: 'Remove from this automation',
  stop_if: 'Stop If',
  add_to_workflow: 'Add to Automation',
  remove_from_workflow: 'Remove from Automation',
}

function stepLabel(type) {
  return __(STEP_LABELS[type] || type)
}

function stepTheme(type) {
  if (type == 'wait') return 'orange'
  if (['stop_if', 'exit', 'remove_from_workflow'].includes(type)) return 'red'
  if (['goal', 'go_to'].includes(type)) return 'purple'
  if (['send_email', 'send_sms', 'send_whatsapp_template', 'notify'].includes(type))
    return 'blue'
  if (['webhook', 'add_to_workflow'].includes(type)) return 'green'
  return 'gray'
}

function stepSummary(step) {
  switch (step.type) {
    case 'send_email':
      return step.subject || step.email_template || __('No subject')
    case 'send_sms':
    case 'notify':
      return step.message || __('No message')
    case 'send_whatsapp_template':
      return step.template || __('No template selected')
    case 'create_task':
      return step.title || __('Follow up')
    case 'assign':
      return (step.users || []).join(', ') || step.user || __('No user selected')
    case 'add_note':
    case 'add_tag_comment':
      return step.comment || __('No note')
    case 'add_tag':
    case 'remove_tag':
      return step.tag || __('No tag')
    case 'set_field':
      return `${step.field || '?'} → ${step.value ?? '?'}`
    case 'convert_to_deal':
      return __('Creates a deal from this lead')
    case 'webhook':
      return `${step.method || 'POST'} ${step.url || '?'}`
    case 'wait':
      return waitSummary(step)
    case 'goal':
      return `${step.event || '?'}${step.value ? ' = ' + step.value : ''} · ${__(step.outcome || 'continue')}`
    case 'go_to':
      return `→ #${step.target || '?'}`
    case 'exit':
      return __('Contact exits here')
    case 'stop_if':
      return conditionSummary(step.condition)
    case 'add_to_workflow':
    case 'remove_from_workflow':
      return step.automation || '?'
    default:
      return ''
  }
}

function waitSummary(step) {
  if (step.mode == 'until_time') return __('until {0}', [step.time || '?'])
  if (step.mode == 'until_reply')
    return __('until reply') + (step.timeout_hours ? ` (max ${step.timeout_hours}h)` : '')
  if (step.mode == 'until_link_click')
    return (
      __('until click on {0}', [step.link || '?']) +
      (step.timeout_hours ? ` (max ${step.timeout_hours}h)` : '')
    )
  return [
    step.days && `${step.days} ${__('days')}`,
    step.hours && `${step.hours} ${__('hours')}`,
    step.minutes && `${step.minutes} ${__('minutes')}`,
  ]
    .filter(Boolean)
    .join(', ')
}

function conditionSummary(condition) {
  if (!condition?.field) return ''
  return `${condition.field} ${__(condition.operator || 'equals')} ${condition.value ?? ''}`
}

function groupsSummary(groups) {
  if (!groups?.length) return __('Always')
  return groups
    .map((g) => g.map((c) => conditionSummary(c)).join(' && '))
    .join(' || ')
}

function enrollmentTheme(status) {
  return (
    {
      Active: 'blue',
      Waiting: 'orange',
      Completed: 'green',
      Exited: 'gray',
      Failed: 'red',
    }[status] || 'gray'
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
        time_window_enabled: Boolean(data.time_window_enabled),
        trigger_config: data.trigger_config || {},
        window_days: data.window_days || [],
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
        trigger_condition: draft.trigger_condition?.field ? draft.trigger_condition : null,
        trigger_config: draft.trigger_config,
        allow_reenrollment: draft.allow_reenrollment,
        exit_on_reply: draft.exit_on_reply,
        time_window_enabled: draft.time_window_enabled,
        window_start: draft.window_start,
        window_end: draft.window_end,
        window_days: draft.window_days,
        steps: draft.steps,
      },
    },
    auto: true,
    onSuccess: (data) => {
      saving.value = false
      draft.name = data.name
      draft.webhook_key = data.webhook_key || ''
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

// --- step editing (shared with the recursive StepList via provide) ---

const showStepDialog = ref(false)
const stepDraft = reactive({ type: 'send_email' })
const showBranchDialog = ref(false)
const branchDraft = ref(null)
let targetList = null
let targetIndex = -1

function addStepOptions(list) {
  return Object.keys(STEP_LABELS)
    .filter((t) => t != 'add_tag_comment')
    .map((type) => ({
      label: stepLabel(type),
      onClick: () => addStep(list, type),
    }))
}

function newStep(type) {
  const step = { type }
  if (type == 'wait') Object.assign(step, { mode: 'duration', days: 0, hours: 4, minutes: 0 })
  if (type == 'goal') Object.assign(step, { event: 'reply', outcome: 'continue' })
  if (type == 'if_else')
    Object.assign(step, {
      branches: [
        {
          label: '',
          condition_groups: [[{ field: '', operator: 'equals', value: '' }]],
          steps: [],
        },
      ],
      else_steps: [],
    })
  if (type == 'split')
    Object.assign(step, {
      paths: [
        { label: 'A', percent: 50, steps: [] },
        { label: 'B', percent: 50, steps: [] },
      ],
    })
  if (type == 'webhook') Object.assign(step, { method: 'POST' })
  return step
}

function addStep(list, type) {
  const step = newStep(type)
  list.push(step)
  if (!['if_else', 'exit', 'convert_to_deal'].includes(type)) {
    editStep(list, list.length - 1)
  }
}

function editStep(list, i) {
  targetList = list
  targetIndex = i
  Object.keys(stepDraft).forEach((k) => delete stepDraft[k])
  Object.assign(stepDraft, JSON.parse(JSON.stringify(list[i])))
  showStepDialog.value = true
}

function applyStep() {
  const step = JSON.parse(JSON.stringify(stepDraft))
  if (step.condition && !step.condition.field) delete step.condition
  if (!step.label) delete step.label
  if (targetList && targetIndex > -1) {
    // keep nested steps arrays that the dialog does not edit
    const existing = targetList[targetIndex]
    if (step.type == 'split' && existing?.paths) {
      step.paths = step.paths.map((p, i) => ({ ...p, steps: existing.paths[i]?.steps || [] }))
    }
    targetList[targetIndex] = step
  }
  showStepDialog.value = false
}

function addSplitPath() {
  stepDraft.paths.push({ label: '', percent: 0, steps: [] })
}

function moveStep(list, i, delta) {
  const j = i + delta
  if (j < 0 || j >= list.length) return
  const [step] = list.splice(i, 1)
  list.splice(j, 0, step)
}

function addBranch(step) {
  step.branches.push({
    label: '',
    condition_groups: [[{ field: '', operator: 'equals', value: '' }]],
    steps: [],
  })
}

function editBranch(step, bi) {
  branchDraft.value = step.branches[bi]
  if (!branchDraft.value.condition_groups?.length) {
    branchDraft.value.condition_groups = [[{ field: '', operator: 'equals', value: '' }]]
  }
  showBranchDialog.value = true
}

provide('automation-editor', {
  addStepOptions,
  editStep,
  moveStep,
  addBranch,
  editBranch,
  stepLabel,
  stepTheme,
  stepSummary,
  conditionSummary,
  groupsSummary,
})
</script>
