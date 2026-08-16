<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      class="flex h-12 shrink-0 items-center justify-between border-b border-outline-gray-2 px-4"
    >
      <div class="text-base-semibold text-ink-gray-8">
        {{ selectedStep ? __('Step') : __('Trigger') }}
      </div>
      <div class="flex items-center gap-1">
        <Button
          v-if="selectedStep || doc.trigger_type"
          icon="lucide-trash-2"
          variant="ghost"
          :aria-label="selectedStep ? __('Remove step') : __('Remove trigger')"
          @click="$emit('request-remove')"
        />
      </div>
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
        <WorkflowFilters
          v-model="doc.filters"
          :doctype="doc.document_type"
          flat
        />
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
import { documentTriggers, otherTriggers } from './workflowTriggers'
import { Button, FormControl, LoadingIndicator } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doc: { type: Object, required: true },
  selectedStep: { type: Object, default: null },
  targets: { type: Array, default: () => [] },
  errors: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['request-remove'])

const docTypeFilters = { istable: 0 }
const runAsOptions = ['Triggering User', 'Document Owner', 'Automation User']
const capabilities = computed(() => capabilitiesFor(props.doc.document_type))
const fields = computed(() => capabilities.value?.fields || [])
const events = computed(() => capabilities.value?.custom_events || [])
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
