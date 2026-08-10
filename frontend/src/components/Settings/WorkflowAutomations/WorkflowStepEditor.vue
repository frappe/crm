<template>
  <div class="space-y-5">
    <div
      v-for="error in errors"
      :key="error.message"
      class="rounded border border-outline-red-2 bg-surface-red-1 p-2 text-sm text-ink-red-4"
      role="alert"
    >
      {{ error.message }}
    </div>

    <FormControl
      v-model="step.step_type"
      type="select"
      :label="__('Step Type')"
      :options="stepTypeOptions"
    />
    <FormControl
      v-model="step.step_key"
      :label="__('Step Key')"
      :placeholder="__('score_lead')"
    />

    <template v-if="step.step_type === 'If'">
      <ConditionEditor
        v-model="step.step_condition"
        :fields="fields"
        :label="__('Condition')"
        :placeholder="__('doc.status == \'Qualified\'')"
      />
      <div class="text-xs text-ink-gray-5">
        {{
          __(
            'Steps added under the If and Else arms run only when this decides that way.',
          )
        }}
      </div>
    </template>

    <template v-else-if="step.step_type === 'Wait'">
      <div class="flex gap-2">
        <FormControl
          :model-value="params.value"
          type="number"
          class="flex-1"
          :label="__('Wait')"
          @update:model-value="setParam('value', Number($event))"
        />
        <FormControl
          :model-value="params.unit || 'Minutes'"
          type="select"
          class="w-32"
          :label="__('Unit')"
          :options="waitUnits"
          @update:model-value="setParam('unit', $event)"
        />
      </div>
    </template>

    <template v-else-if="step.step_type === 'WaitForEvent'">
      <FormControl
        :model-value="params.event_name"
        type="select"
        :label="__('Event')"
        :options="eventOptions"
        @update:model-value="setParam('event_name', $event)"
      />
      <FormControl
        :model-value="params.correlation_key"
        :label="__('Correlation Key')"
        :placeholder="correlationPlaceholder"
        @update:model-value="setParam('correlation_key', $event)"
      />
      <div class="flex gap-2">
        <FormControl
          :model-value="params.timeout_value"
          type="number"
          class="flex-1"
          :label="__('Timeout')"
          @update:model-value="setParam('timeout_value', Number($event))"
        />
        <FormControl
          :model-value="params.timeout_unit || 'Days'"
          type="select"
          class="w-32"
          :label="__('Unit')"
          :options="waitUnits"
          @update:model-value="setParam('timeout_unit', $event)"
        />
      </div>
      <div class="text-xs text-ink-gray-5">
        {{
          __(
            'Put the steps for a matched event on the If arm of a following condition, and the timeout steps on Else.',
          )
        }}
      </div>
    </template>

    <template v-else>
      <TargetPicker
        v-model="step.target"
        :targets="targets"
        :label="__('Acts on')"
      />
      <FormControl
        v-model="step.action_type"
        type="select"
        :label="__('Action')"
        :options="actionOptions"
      />
      <ParamEditor
        :action="step"
        :schema="schema"
        :doctype="targetDoctype"
        :fields="fields"
      />
      <FormControl
        v-if="schema?.output_schema"
        v-model="step.output_alias"
        :label="__('Name the result')"
        :placeholder="__('deal')"
      />
      <div
        v-if="outputPaths.length"
        class="min-w-0 overflow-hidden rounded bg-surface-gray-2 p-3"
      >
        <div class="mb-1 text-xs-semibold text-ink-gray-5">
          {{ __('Available to later steps') }}
        </div>
        <div
          v-for="path in outputPaths"
          :key="path"
          class="break-all font-mono text-xs text-ink-gray-7"
        >
          {{ path }}
        </div>
      </div>
    </template>

    <RelatedCondition v-model="step.related_condition" :targets="targets" />

    <ConditionEditor
      v-if="step.step_type !== 'If'"
      v-model="step.step_condition"
      :fields="fields"
      :label="__('Only run when')"
      :placeholder="__('doc.status == \'Open\'')"
    />
  </div>
</template>

<script setup>
import ConditionEditor from './WorkflowConditionEditor.vue'
import ParamEditor from './WorkflowParamEditor.vue'
import RelatedCondition from './WorkflowRelatedCondition.vue'
import TargetPicker from './WorkflowTargetPicker.vue'
import {
  actionSchema,
  capabilitiesFor,
  stepParams,
} from './workflowCapabilities'
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  step: { type: Object, required: true },
  doc: { type: Object, required: true },
  targets: { type: Array, default: () => [] },
  errors: { type: Array, default: () => [] },
})

const stepTypeOptions = [
  { label: __('Action'), value: 'Action' },
  { label: __('Wait'), value: 'Wait' },
  { label: __('Wait for event'), value: 'WaitForEvent' },
  { label: __('If / Else'), value: 'If' },
]

const waitUnits = ['Seconds', 'Minutes', 'Hours', 'Days']
const correlationPlaceholder = '{{ doc.message_id or doc.name }}'

const params = computed(() => stepParams(props.step))

const targetDoctype = computed(
  () =>
    props.targets.find(
      (target) => target.alias === (props.step.target || 'trigger'),
    )?.doctype,
)

const fields = computed(
  () => capabilitiesFor(targetDoctype.value)?.fields || [],
)

const actionOptions = computed(() => {
  const actions = capabilitiesFor(targetDoctype.value)?.actions || []
  const options = actions.map((action) => ({
    label: action.label,
    value: action.action_type,
  }))
  // Never render a chosen action as an empty select, even if its DocType is still unknown.
  if (props.step.action_type && !actions.some(isChosen))
    options.unshift({
      label: schema.value?.label || props.step.action_type,
      value: props.step.action_type,
    })
  return options
})

function isChosen(action) {
  return action.action_type === props.step.action_type
}

const eventOptions = computed(
  () => capabilitiesFor(props.doc.document_type)?.custom_events || [],
)

const schema = computed(() =>
  actionSchema(targetDoctype.value, props.step.action_type),
)

const outputPaths = computed(() => {
  const keys = Object.keys(schema.value?.output_schema || {})
  const key = props.step.step_key || __('<step key>')
  return keys.map((name) => `context.steps.${key}.${name}`)
})

function setParam(name, value) {
  props.step.params = JSON.stringify(
    { ...params.value, [name]: value },
    null,
    2,
  )
}
</script>
