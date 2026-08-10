<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="flex h-12 shrink-0 items-center justify-between border-b border-outline-gray-2 px-4"
    >
      <div class="text-base-semibold text-ink-gray-8">
        {{ selectedStep ? __('Step') : __('Trigger') }}
      </div>
      <Button
        v-if="selectedStep"
        icon="lucide-trash-2"
        variant="ghost"
        :aria-label="__('Remove step')"
        @click="$emit('remove-step')"
      />
    </div>
    <div class="min-h-0 flex-1 space-y-5 overflow-y-auto p-4">
      <div v-if="loading" class="flex justify-center py-8">
        <LoadingIndicator class="w-4" />
      </div>
      <StepEditor
        v-else-if="selectedStep"
        :step="selectedStep"
        :doc="doc"
        :targets="targets"
        :errors="errors"
      />
      <template v-else>
        <Link
          v-model="doc.document_type"
          label="Doctype"
          doctype="DocType"
          :filters="docTypeFilters"
        />
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">{{ __('Data') }}</div>
          <button
            v-for="trigger in documentTriggers"
            :key="trigger.value"
            class="trigger-row"
            :class="{
              'trigger-row-selected': doc.trigger_type === trigger.value,
            }"
            @click="doc.trigger_type = trigger.value"
          >
            <component :is="trigger.icon" class="size-4" />
            <span class="text-sm">{{ trigger.label }}</span>
          </button>
        </div>
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">{{ __('Others') }}</div>
          <button
            v-for="trigger in otherTriggers"
            :key="trigger.value"
            class="trigger-row"
            :class="{
              'trigger-row-selected': doc.trigger_type === trigger.value,
            }"
            @click="doc.trigger_type = trigger.value"
          >
            <component :is="trigger.icon" class="size-4" />
            <span class="text-sm">{{ trigger.label }}</span>
          </button>
        </div>
        <TriggerDetails :doc="doc" :fields="fields" :events="events" />
        <Relationships
          v-model="doc.relationships"
          :document-type="doc.document_type"
        />
        <WorkflowFilters v-model="doc.filters" :fields="fields" />
        <FormControl
          v-model="doc.condition"
          type="textarea"
          :label="__('Condition')"
          :placeholder="__('doc.status == \'Open\'')"
        />
        <FormControl
          v-model="doc.run_as"
          type="select"
          :label="__('Run As')"
          :options="runAsOptions"
        />
        <Link
          v-if="doc.run_as === 'Automation User'"
          v-model="doc.automation_user"
          :label="__('Automation User')"
          doctype="User"
        />
        <SwitchField v-model="doc.enabled" :label="__('Enabled')" />
        <SwitchField v-model="doc.log_only" :label="__('Log Only')" />
        <SwitchField
          v-model="doc.revalidate_on_run"
          :label="__('Revalidate on Run')"
        />
        <SwitchField v-model="doc.stop_on_error" :label="__('Stop on Error')" />
        <FormControl
          v-model="doc.throttle_per_minute"
          type="number"
          :label="__('Throttle per Minute')"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import Relationships from './WorkflowRelationships.vue'
import StepEditor from './WorkflowStepEditor.vue'
import SwitchField from './WorkflowSwitchField.vue'
import TriggerDetails from './WorkflowTriggerDetails.vue'
import WorkflowFilters from './WorkflowFilters.vue'
import { capabilitiesFor } from './workflowCapabilities'
import CreatedIcon from '~icons/lucide/list-plus'
import UpdatedIcon from '~icons/lucide/refresh-cw'
import DeletedIcon from '~icons/lucide/trash-2'
import ChangedIcon from '~icons/lucide/pencil-line'
import ManualIcon from '~icons/lucide/hand'
import ScheduleIcon from '~icons/lucide/clock'
import EventIcon from '~icons/lucide/webhook'
import SubmitIcon from '~icons/lucide/send'
import CancelIcon from '~icons/lucide/circle-slash'
import { Button, FormControl, LoadingIndicator } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doc: { type: Object, required: true },
  selectedStep: { type: Object, default: null },
  targets: { type: Array, default: () => [] },
  errors: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['remove-step'])

const docTypeFilters = { istable: 0 }
const runAsOptions = ['Triggering User', 'Document Owner', 'Automation User']

const capabilities = computed(() => capabilitiesFor(props.doc.document_type))
const fields = computed(() => capabilities.value?.fields || [])
const events = computed(() => capabilities.value?.custom_events || [])

const documentTriggers = [
  { label: __('Record is created'), value: 'Doc Created', icon: CreatedIcon },
  { label: __('Record is updated'), value: 'Doc Updated', icon: UpdatedIcon },
  { label: __('Record is deleted'), value: 'Doc Deleted', icon: DeletedIcon },
  {
    label: __('Field value changes'),
    value: 'Field Value Changed',
    icon: ChangedIcon,
  },
  {
    label: __('Record is submitted'),
    value: 'Doc Submitted',
    icon: SubmitIcon,
  },
  {
    label: __('Record is cancelled'),
    value: 'Doc Cancelled',
    icon: CancelIcon,
  },
]

const otherTriggers = [
  { label: __('Launch manually'), value: 'Manual', icon: ManualIcon },
  { label: __('On a schedule'), value: 'Scheduled', icon: ScheduleIcon },
  { label: __('On a date'), value: 'Date Based', icon: ScheduleIcon },
  { label: __('Custom event'), value: 'Custom Event', icon: EventIcon },
]
</script>

<style scoped>
.trigger-row {
  display: flex;
  height: 36px;
  width: 100%;
  align-items: center;
  gap: 12px;
  margin-top: 1px;
  border-radius: 6px;
  padding: 0 8px;
  color: var(--ink-gray-7);
  text-align: left;
}

.trigger-row:hover,
.trigger-row-selected {
  background: var(--surface-gray-2);
}
</style>
