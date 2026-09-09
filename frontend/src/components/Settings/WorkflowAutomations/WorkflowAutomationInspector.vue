<template>
  <div class="flex h-full min-h-0 flex-col bg-surface-base">
    <div class="flex h-12 shrink-0 items-center justify-between px-2">
      <div class="text-base-semibold text-ink-gray-8">
        {{ selectedStep ? __('Step') : __('Trigger') }}
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
      />
      <template v-else>
        <Link
          :model-value="doc.document_type"
          label="DocType"
          variant="outline"
          doctype="DocType"
          :filters="docTypeFilters"
          @update:model-value="patch({ document_type: $event })"
        />
        <div v-for="section in triggerSections" :key="section.group">
          <div class="mb-2 text-base text-ink-gray-5">{{ section.group }}</div>
          <button
            v-for="trigger in section.options"
            :key="trigger.value"
            class="trigger-row"
            :class="{
              'trigger-row-selected': selectedTrigger === trigger.value,
            }"
            @click="pickTrigger(trigger.value)"
          >
            <component
              :is="trigger.icon"
              class="size-4"
              :class="trigger.tone"
            />
            <span class="text-sm">{{ trigger.label }}</span>
          </button>
        </div>
        <TriggerDetails
          :doc="doc"
          :fields="fields"
          :events="events"
          @update="patch"
        />
        <Relationships
          :model-value="doc.relationships"
          :document-type="doc.document_type"
          @update:model-value="patch({ relationships: $event })"
        />
        <WorkflowFilters
          :model-value="doc.filters"
          :doctype="doc.document_type"
          flat
          @update:model-value="patch({ filters: $event })"
        />
        <ConditionEditor
          :model-value="doc.condition"
          :doctype="doc.document_type"
          :label="__('Condition')"
          variant="outline"
          :placeholder="__('doc.status == \'Open\'')"
          @update:model-value="patch({ condition: $event })"
        />
        <FormControl
          :model-value="doc.run_as"
          type="select"
          variant="outline"
          :label="__('Run As')"
          :options="runAsOptions"
          @update:model-value="patch({ run_as: $event })"
        />
        <Link
          v-if="doc.run_as === 'Automation User'"
          :model-value="doc.automation_user"
          :label="__('Automation User')"
          variant="outline"
          doctype="User"
          @update:model-value="patch({ automation_user: $event })"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import ConditionEditor from './WorkflowConditionEditor.vue'
import Relationships from './WorkflowRelationships.vue'
import StepEditor from './WorkflowStepEditor.vue'
import TriggerDetails from './WorkflowTriggerDetails.vue'
import WorkflowFilters from './WorkflowFilters.vue'
import { capabilitiesFor } from './workflowCapabilities'
import {
  triggerFromValue,
  triggerGroups,
  triggerValue,
} from './workflowTriggers'
import { FormControl, LoadingIndicator } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doc: { type: Object, required: true },
  selectedStep: { type: Object, default: null },
  targets: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update'])

const docTypeFilters = { istable: 0 }
const triggerSections = computed(() => triggerGroups(props.doc.document_type))
const selectedTrigger = computed(() => triggerValue(props.doc))

function pickTrigger(value) {
  patch(triggerFromValue(value))
}

/** The builder owns the document; edits here travel back up to it. */
function patch(values) {
  emit('update', values)
}

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
  background: var(--surface-gray-3);
}
</style>
